import time
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status

from .config import API_VERSION, MAX_BODY_BYTES
from .logging import configure_logging, redact_headers
from .rate_limit import rate_limit
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
