from enum import Enum


class InboxOrigin(str, Enum):
    SYSTEM = "system"
    PEER = "peer"
