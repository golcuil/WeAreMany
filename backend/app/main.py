import time
from typing import Callable, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from .config import API_VERSION, MAX_BODY_BYTES
from .logging import configure_logging, redact_headers
from .events import EventName, get_event_emitter, new_request_id, safe_emit
from .matching import Candidate, get_dedupe_store, match_decision
from .moderation import get_leak_throttle, moderate_text
from .rate_limit import rate_limit
from .repository import MessageRecord, MoodRecord, get_repository
from .security import current_principal

logger = configure_logging()

app = FastAPI(title="We Are Many API", version=API_VERSION)


@app.middleware("http")
async def request_size_limit(request: Request, call_next: Callable) -> Response:
    if request.method in {"POST", "PUT", "PATCH"}:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Request too large")
        body = await request.body()
        if len(body) > MAX_BODY_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Request too large")
        request._body = body
    return await call_next(request)


@app.middleware("http")
async def request_logging(request: Request, call_next: Callable) -> Response:
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    logger.info(
        "request",
        {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "headers": redact_headers(dict(request.headers)),
        },
    )
    return response


@app.get("/health", include_in_schema=False)
def health() -> dict:
    return {"status": "ok"}


@app.get("/version", dependencies=[Depends(current_principal), Depends(rate_limit("read"))])
def version() -> dict:
    return {"version": API_VERSION}


class MoodRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valence: str
    intensity: str
    emotion: Optional[str] = None
    free_text: Optional[str] = Field(default=None, max_length=1000)


class MoodResponse(BaseModel):
    sanitized_text: Optional[str]
    risk_level: int
    reid_risk: float
    identity_leak: bool
    leak_types: List[str]
    crisis_action: Optional[str]


class MessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valence: str
    intensity: str
    emotion: Optional[str] = None
    free_text: str = Field(..., max_length=1000)


class MessageResponse(BaseModel):
    sanitized_text: Optional[str]
    risk_level: int
    reid_risk: float
    identity_leak: bool
    leak_types: List[str]
    status: str
    hold_reason: Optional[str] = None
    crisis_action: Optional[str]


class InboxItemResponse(BaseModel):
    inbox_item_id: str
    text: str
    created_at: str
    ack_status: Optional[str] = None


class InboxResponse(BaseModel):
    items: List[InboxItemResponse]


class AcknowledgementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inbox_item_id: str
    reaction: str


class AcknowledgementResponse(BaseModel):
    status: str


class MatchCandidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    intensity: str
    themes: List[str] = Field(default_factory=list)


class MatchSimulateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_level: int
    intensity: str
    themes: List[str] = Field(default_factory=list)
    candidates: List[MatchCandidateRequest] = Field(default_factory=list)


class MatchSimulateResponse(BaseModel):
    decision: str
    reason: str
    system_generated_empathy: Optional[str] = None
    finite_content_bridge: Optional[str] = None
    crisis_action: Optional[str] = None


@app.post(
    "/mood",
    dependencies=[Depends(current_principal), Depends(rate_limit("write"))],
)
def submit_mood(
    payload: MoodRequest,
    principal=Depends(current_principal),
    repo=Depends(get_repository),
    leak_throttle=Depends(get_leak_throttle),
    emitter=Depends(get_event_emitter),
) -> MoodResponse:
    request_id = new_request_id()
    text = payload.free_text or ""
    result = moderate_text(text, principal.principal_id, leak_throttle)

    crisis_action = "show_crisis" if result.risk_level == 2 else None
    if result.risk_level != 2:
        repo.save_mood(
            MoodRecord(
                principal_id=principal.principal_id,
                valence=payload.valence,
                intensity=payload.intensity,
                emotion=payload.emotion,
                risk_level=result.risk_level,
                sanitized_text=result.sanitized_text,
            )
        )
        repo.upsert_eligible_principal(principal.principal_id, payload.intensity, [])
    else:
        repo.touch_eligible_principal(principal.principal_id, payload.intensity)

    safe_emit(
        emitter,
        EventName.MOOD_SUBMITTED,
        {
            "request_id": request_id,
            "intensity_bucket": payload.intensity,
            "risk_bucket": result.risk_level,
            "has_free_text": bool(payload.free_text),
        },
    )
    if result.identity_leak or result.risk_level > 0:
        safe_emit(
            emitter,
            EventName.MODERATION_FLAGGED,
            {
                "request_id": request_id,
                "risk_bucket": result.risk_level,
                "identity_leak": result.identity_leak,
                "leak_type_count": len(result.leak_types),
            },
        )
    if result.risk_level == 2:
        safe_emit(
            emitter,
            EventName.CRISIS_BLOCKED,
            {"request_id": request_id, "risk_bucket": result.risk_level},
        )

    return MoodResponse(
        sanitized_text=result.sanitized_text,
        risk_level=result.risk_level,
        reid_risk=result.reid_risk,
        identity_leak=result.identity_leak,
        leak_types=result.leak_types,
        crisis_action=crisis_action,
    )


@app.post(
    "/messages",
    dependencies=[Depends(current_principal), Depends(rate_limit("write"))],
)
def submit_message(
    payload: MessageRequest,
    principal=Depends(current_principal),
    repo=Depends(get_repository),
    leak_throttle=Depends(get_leak_throttle),
    emitter=Depends(get_event_emitter),
    dedupe_store=Depends(get_dedupe_store),
) -> MessageResponse:
    request_id = new_request_id()
    result = moderate_text(payload.free_text, principal.principal_id, leak_throttle)
    crisis_action = "show_crisis" if result.risk_level == 2 else None
    status_value = "blocked" if result.risk_level == 2 else "queued"
    hold_reason: Optional[str] = None

    if result.risk_level != 2:
        message_id = repo.save_message(
            MessageRecord(
                principal_id=principal.principal_id,
                valence=payload.valence,
                intensity=payload.intensity,
                emotion=payload.emotion,
                risk_level=result.risk_level,
                sanitized_text=result.sanitized_text,
                reid_risk=result.reid_risk,
            )
        )
        repo.upsert_eligible_principal(principal.principal_id, payload.intensity, [])
        candidates = repo.get_eligible_candidates(
            principal.principal_id,
            payload.intensity,
            [],
        )
        decision = match_decision(
            principal_id=principal.principal_id,
            risk_level=result.risk_level,
            intensity=payload.intensity,
            themes=[],
            candidates=candidates,
            dedupe_store=dedupe_store,
        )
        safe_emit(
            emitter,
            EventName.MATCH_DECISION,
            {
                "request_id": request_id,
                "risk_bucket": result.risk_level,
                "intensity_bucket": payload.intensity,
                "decision": decision.decision,
                "reason": decision.reason,
            },
        )
        if decision.decision == "DELIVER" and decision.recipient_id and result.sanitized_text:
            repo.create_inbox_item(message_id, decision.recipient_id, result.sanitized_text)
            safe_emit(
                emitter,
                EventName.DELIVERY_ATTEMPTED,
                {"request_id": request_id, "outcome": "delivered"},
            )
            status_value = "queued"
        elif decision.decision == "HOLD":
            hold_reason = decision.reason
            safe_emit(
                emitter,
                EventName.DELIVERY_ATTEMPTED,
                {"request_id": request_id, "outcome": "held"},
            )
            status_value = "held"
    else:
        repo.touch_eligible_principal(principal.principal_id, payload.intensity)

    safe_emit(
        emitter,
        EventName.MESSAGE_SUBMITTED,
        {
            "request_id": request_id,
            "intensity_bucket": payload.intensity,
            "risk_bucket": result.risk_level,
            "identity_leak": result.identity_leak,
            "status": status_value,
        },
    )
    if result.identity_leak or result.risk_level > 0:
        safe_emit(
            emitter,
            EventName.MODERATION_FLAGGED,
            {
                "request_id": request_id,
                "risk_bucket": result.risk_level,
                "identity_leak": result.identity_leak,
                "leak_type_count": len(result.leak_types),
            },
        )
    if result.risk_level == 2:
        safe_emit(
            emitter,
            EventName.CRISIS_BLOCKED,
            {"request_id": request_id, "risk_bucket": result.risk_level},
        )

    return MessageResponse(
        sanitized_text=result.sanitized_text if result.risk_level != 2 else None,
        risk_level=result.risk_level,
        reid_risk=result.reid_risk,
        identity_leak=result.identity_leak,
        leak_types=result.leak_types,
        status=status_value,
        hold_reason=hold_reason,
        crisis_action=crisis_action,
    )


@app.post(
    "/match/simulate",
    dependencies=[Depends(current_principal), Depends(rate_limit("write"))],
)
def simulate_match(
    payload: MatchSimulateRequest,
    principal=Depends(current_principal),
    dedupe_store=Depends(get_dedupe_store),
    emitter=Depends(get_event_emitter),
) -> MatchSimulateResponse:
    request_id = new_request_id()
    candidates = [
        Candidate(
            candidate_id=item.candidate_id,
            intensity=item.intensity,
            themes=item.themes,
        )
        for item in payload.candidates
    ]
    decision = match_decision(
        principal_id=principal.principal_id,
        risk_level=payload.risk_level,
        intensity=payload.intensity,
        themes=payload.themes,
        candidates=candidates,
        dedupe_store=dedupe_store,
    )
    safe_emit(
        emitter,
        EventName.MATCH_DECISION,
        {
            "request_id": request_id,
            "risk_bucket": payload.risk_level,
            "intensity_bucket": payload.intensity,
            "decision": decision.decision,
            "reason": decision.reason,
        },
    )
    return MatchSimulateResponse(
        decision=decision.decision,
        reason=decision.reason,
        system_generated_empathy=decision.system_generated_empathy,
        finite_content_bridge=decision.finite_content_bridge,
        crisis_action=decision.crisis_action,
    )


@app.get("/inbox", dependencies=[Depends(current_principal), Depends(rate_limit("read"))])
def fetch_inbox(
    principal=Depends(current_principal),
    repo=Depends(get_repository),
) -> InboxResponse:
    items = repo.list_inbox_items(principal.principal_id)
    response_items = [
        InboxItemResponse(
            inbox_item_id=item.inbox_item_id,
            text=item.text,
            created_at=item.created_at,
            ack_status=item.ack_status,
        )
        for item in items
    ]
    return InboxResponse(items=response_items)


@app.post(
    "/acknowledgements",
    dependencies=[Depends(current_principal), Depends(rate_limit("write"))],
)
def acknowledge_message(
    payload: AcknowledgementRequest,
    principal=Depends(current_principal),
    repo=Depends(get_repository),
) -> AcknowledgementResponse:
    try:
        status_value = repo.acknowledge(payload.inbox_item_id, principal.principal_id, payload.reaction)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return AcknowledgementResponse(status=status_value)
