from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .hold_reasons import HoldReason


class DeliveryMode(str, Enum):
    HOLD = "HOLD"
    BRIDGE_SYSTEM = "BRIDGE_SYSTEM"
    DELIVER_PEER = "DELIVER_PEER"


@dataclass(frozen=True)
class DeliveryDecision:
    mode: DeliveryMode
    hold_reason: Optional[str]


def decide_delivery_mode(
    *,
    in_crisis_window: bool,
    hold_reason: Optional[str],
    recipient_pool_size: int,
    min_pool_size: int,
) -> DeliveryDecision:
    if in_crisis_window:
        return DeliveryDecision(
            mode=DeliveryMode.BRIDGE_SYSTEM,
            hold_reason=HoldReason.CRISIS_WINDOW.value,
        )
    if hold_reason:
        return DeliveryDecision(mode=DeliveryMode.HOLD, hold_reason=hold_reason)
    if recipient_pool_size < min_pool_size:
        return DeliveryDecision(
            mode=DeliveryMode.BRIDGE_SYSTEM,
            hold_reason=HoldReason.INSUFFICIENT_POOL.value,
        )
    return DeliveryDecision(mode=DeliveryMode.DELIVER_PEER, hold_reason=None)
