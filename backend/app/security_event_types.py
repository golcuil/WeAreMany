from enum import Enum


class SecurityEventType(str, Enum):
    IDENTITY_LEAK_DETECTED = "identity_leak_detected"
    IDENTITY_LEAK_THROTTLE_HELD = "identity_leak_throttle_held"
