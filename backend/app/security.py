from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException, Request, status

from .config import AUTH_TOKEN_PREFIX


@dataclass(frozen=True)
class Principal:
    principal_id: str


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
    return parts[1]


def _verify_token(token: str) -> Principal:
    if not token.startswith(AUTH_TOKEN_PREFIX):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    principal_id = token[len(AUTH_TOKEN_PREFIX):]
    if not principal_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return Principal(principal_id=principal_id)


def current_principal(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> Principal:
    token = _extract_bearer_token(authorization)
    principal = _verify_token(token)
    request.state.principal_id = principal.principal_id
    return principal
