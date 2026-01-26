import hashlib
import hmac
from typing import Any, Dict, Optional

from .config import SECURITY_EVENT_HMAC_KEY
from .repository import SecurityEventRecord, Repository


def actor_hash(principal_id: str) -> str:
    key = SECURITY_EVENT_HMAC_KEY.encode("utf-8")
    message = principal_id.encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def safe_record_security_event(
    repo: Repository,
    principal_id: str,
    event_type: str,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        repo.record_security_event(
            SecurityEventRecord(
                actor_hash=actor_hash(principal_id),
                event_type=event_type,
                meta=meta or {},
            )
        )
    except Exception:
        return None
