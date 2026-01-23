import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from .config import (
    API_VERSION,
    COLD_START_MIN_POOL,
    CRISIS_WINDOW_HOURS,
    K_ANON_MIN,
    MATCH_SAMPLE_LIMIT,
    MAX_BODY_BYTES,
    SIMILAR_WINDOW_DAYS,
)
from .bridge import SYSTEM_SENDER_ID, build_reflective_message
from .logging import configure_logging, redact_headers
from .events import EventName, get_event_emitter, new_request_id, safe_emit
from .matching import Candidate, get_dedupe_store, match_decision, progressive_params
from .moderation import get_leak_throttle, moderate_text
from .rate_limit import rate_limit
from .repository import MessageRecord, MoodEventRecord, MoodRecord, get_repository
from .themes import map_mood_to_themes, normalize_theme_tags
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
    status: str
    sanitized_text: Optional[str]
    risk_level: int
    reid_risk: float
    identity_leak: bool
    leak_types: List[str]
    crisis_action: Optional[str]
    similar_count: Optional[int] = None


class ReflectionSummaryResponse(BaseModel):
    window_days: int
    total_entries: int
    distribution: Dict[str, int]
    trend: str
    volatility_days: int


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


class ImpactResponse(BaseModel):
    helped_count: int

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
    mood_themes = map_mood_to_themes(payload.emotion, payload.valence, payload.intensity)
    primary_theme = mood_themes[0] if mood_themes else "calm"

    if result.risk_level == 2:
        now = datetime.now(timezone.utc)
        repo.record_crisis_action(principal.principal_id, "show_resources", now=now)
        repo.record_mood_event(
            MoodEventRecord(
                principal_id=principal.principal_id,
                created_at=now,
                valence=payload.valence,
                intensity=payload.intensity,
                expressed_emotion=payload.emotion,
                risk_level=result.risk_level,
                theme_tag=primary_theme,
            )
        )
        return MoodResponse(
            status="blocked",
            sanitized_text=None,
            risk_level=result.risk_level,
            reid_risk=result.reid_risk,
            identity_leak=result.identity_leak,
            leak_types=result.leak_types,
            crisis_action="show_resources",
            similar_count=None,
        )

    crisis_action = None
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
        repo.record_mood_event(
            MoodEventRecord(
                principal_id=principal.principal_id,
                created_at=datetime.now(timezone.utc),
                valence=payload.valence,
                intensity=payload.intensity,
                expressed_emotion=payload.emotion,
                risk_level=result.risk_level,
                theme_tag=primary_theme,
            )
        )
        repo.upsert_eligible_principal(principal.principal_id, payload.intensity, mood_themes)

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

    similar_count = None
    if result.risk_level != 2:
        count = repo.get_similar_count(
            principal.principal_id,
            primary_theme,
            payload.valence,
            SIMILAR_WINDOW_DAYS,
        )
        if count >= K_ANON_MIN:
            similar_count = count

    return MoodResponse(
        status="ok",
        sanitized_text=result.sanitized_text,
        risk_level=result.risk_level,
        reid_risk=result.reid_risk,
        identity_leak=result.identity_leak,
        leak_types=result.leak_types,
        crisis_action=crisis_action,
        similar_count=similar_count,
    )


@app.get(
    "/reflection/summary",
    dependencies=[Depends(current_principal), Depends(rate_limit("read"))],
    response_model=ReflectionSummaryResponse,
)
def reflection_summary(
    window_days: int = 7,
    principal=Depends(current_principal),
    repo=Depends(get_repository),
) -> ReflectionSummaryResponse:
    bounded = min(max(window_days, 1), 30)
    summary = repo.get_reflection_summary(principal.principal_id, bounded)
    return ReflectionSummaryResponse(
        window_days=summary.window_days,
        total_entries=summary.total_entries,
        distribution=summary.distribution,
        trend=summary.trend,
        volatility_days=summary.volatility_days,
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
        message_themes = map_mood_to_themes(payload.emotion, payload.valence, payload.intensity)
        if repo.is_in_crisis_window(principal.principal_id, CRISIS_WINDOW_HOURS):
            system_text = build_reflective_message(
                message_themes,
                payload.valence,
                payload.intensity,
            )
            system_message_id = repo.save_message(
                MessageRecord(
                    principal_id=SYSTEM_SENDER_ID,
                    valence=payload.valence,
                    intensity=payload.intensity,
                    emotion=payload.emotion,
                    theme_tags=message_themes,
                    risk_level=0,
                    sanitized_text=system_text,
                    reid_risk=0.0,
                )
            )
            repo.create_inbox_item(system_message_id, principal.principal_id, system_text)
            safe_emit(
                emitter,
                EventName.DELIVERY_ATTEMPTED,
                {"request_id": request_id, "outcome": "crisis_gate"},
            )
            status_value = "held"
            hold_reason = "crisis_window"
        else:
            message_id = repo.save_message(
                MessageRecord(
                    principal_id=principal.principal_id,
                    valence=payload.valence,
                    intensity=payload.intensity,
                    emotion=payload.emotion,
                    theme_tags=message_themes,
                    risk_level=result.risk_level,
                    sanitized_text=result.sanitized_text,
                    reid_risk=result.reid_risk,
                )
            )
            repo.upsert_eligible_principal(principal.principal_id, payload.intensity, message_themes)
            health = repo.get_matching_health(principal.principal_id, window_days=7)
            params = progressive_params(health.ratio)
            logger.info(
                "matching_health",
                {
                    "delivered": health.delivered_count,
                    "positive_acks": health.positive_ack_count,
                    "health_ratio": round(health.ratio, 2),
                    "bucket": params.bucket,
                },
            )
            limit = max(1, int(MATCH_SAMPLE_LIMIT * (1 + params.pool_multiplier)))
            cold_start_min = max(COLD_START_MIN_POOL, 1)
            candidate_limit = max(limit, cold_start_min)
            affinity_map = repo.get_affinity_map(principal.principal_id)
            candidates = repo.get_eligible_candidates(
                principal.principal_id,
                payload.intensity,
                message_themes,
                limit=candidate_limit,
            )
            if len(candidates) < cold_start_min:
                system_text = build_reflective_message(
                    message_themes,
                    payload.valence,
                    payload.intensity,
                )
                system_message_id = repo.save_message(
                    MessageRecord(
                        principal_id=SYSTEM_SENDER_ID,
                        valence=payload.valence,
                        intensity=payload.intensity,
                        emotion=payload.emotion,
                        theme_tags=message_themes,
                        risk_level=0,
                        sanitized_text=system_text,
                        reid_risk=0.0,
                    )
                )
                repo.create_inbox_item(system_message_id, principal.principal_id, system_text)
                safe_emit(
                    emitter,
                    EventName.DELIVERY_ATTEMPTED,
                    {"request_id": request_id, "outcome": "system_fallback"},
                )
                status_value = "held"
                hold_reason = "insufficient_pool"
            else:
                decision = match_decision(
                    principal_id=principal.principal_id,
                    risk_level=result.risk_level,
                    intensity=payload.intensity,
                    themes=message_themes,
                    candidates=candidates,
                    dedupe_store=dedupe_store,
                    intensity_band=params.intensity_band,
                    allow_theme_relax=params.allow_theme_relax,
                    affinity_map=affinity_map,
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
    normalized_themes = normalize_theme_tags(payload.themes)
    candidates = [
        Candidate(
            candidate_id=item.candidate_id,
            intensity=item.intensity,
            themes=normalize_theme_tags(item.themes),
        )
        for item in payload.candidates
    ]
    decision = match_decision(
        principal_id=principal.principal_id,
        risk_level=payload.risk_level,
        intensity=payload.intensity,
        themes=normalized_themes,
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
            created_at=_coarsen_day_iso(item.created_at),
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


@app.get(
    "/impact",
    dependencies=[Depends(current_principal), Depends(rate_limit("read"))],
)
def get_impact(
    principal=Depends(current_principal),
    repo=Depends(get_repository),
) -> ImpactResponse:
    helped_count = repo.get_helped_count(principal.principal_id)
    return ImpactResponse(helped_count=helped_count)


def _coarsen_day_iso(value: str) -> str:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    day = parsed.astimezone(timezone.utc).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return day.isoformat()
