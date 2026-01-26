from enum import Enum


class HoldReason(str, Enum):
    CRISIS_WINDOW = "crisis_window"
    IDENTITY_LEAK = "identity_leak"
    INSUFFICIENT_POOL = "insufficient_pool"
    RISK_LEVEL_2 = "risk_level_2"
    NO_ELIGIBLE_CANDIDATES = "no_eligible_candidates"
    COOLDOWN_ACTIVE = "cooldown_active"
