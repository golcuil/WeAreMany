import time
from typing import Callable, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from .config import API_VERSION, MAX_BODY_BYTES
from .logging import configure_logging, redact_headers
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
    crisis_action: Optional[str]


@app.post(
    "/mood",
    dependencies=[Depends(current_principal), Depends(rate_limit("write"))],
)
def submit_mood(
    payload: MoodRequest,
    principal=Depends(current_principal),
    repo=Depends(get_repository),
    leak_throttle=Depends(get_leak_throttle),
) -> MoodResponse:
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
) -> MessageResponse:
    result = moderate_text(payload.free_text, principal.principal_id, leak_throttle)
    crisis_action = "show_crisis" if result.risk_level == 2 else None
    status_value = "blocked" if result.risk_level == 2 else "queued"

    if result.risk_level != 2:
        repo.save_message(
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

    return MessageResponse(
        sanitized_text=result.sanitized_text if result.risk_level != 2 else None,
        risk_level=result.risk_level,
        reid_risk=result.reid_risk,
        identity_leak=result.identity_leak,
        leak_types=result.leak_types,
        status=status_value,
        crisis_action=crisis_action,
    )
