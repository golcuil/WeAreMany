from app.delivery_decision import DeliveryMode, decide_delivery_mode, is_low_density
from app.hold_reasons import HoldReason


def test_decision_crisis_overrides_hold_and_density():
    decision = decide_delivery_mode(
        in_crisis_window=True,
        hold_reason=HoldReason.IDENTITY_LEAK.value,
        recipient_pool_size=0,
        min_pool_size=10,
    )
    assert decision.mode == DeliveryMode.BRIDGE_SYSTEM
    assert decision.hold_reason == HoldReason.CRISIS_WINDOW.value


def test_decision_hold_overrides_low_density():
    decision = decide_delivery_mode(
        in_crisis_window=False,
        hold_reason=HoldReason.IDENTITY_LEAK.value,
        recipient_pool_size=0,
        min_pool_size=10,
    )
    assert decision.mode == DeliveryMode.HOLD
    assert decision.hold_reason == HoldReason.IDENTITY_LEAK.value


def test_decision_low_density_bridge():
    decision = decide_delivery_mode(
        in_crisis_window=False,
        hold_reason=None,
        recipient_pool_size=3,
        min_pool_size=10,
    )
    assert decision.mode == DeliveryMode.BRIDGE_SYSTEM
    assert decision.hold_reason == HoldReason.INSUFFICIENT_POOL.value


def test_decision_deliver_peer():
    decision = decide_delivery_mode(
        in_crisis_window=False,
        hold_reason=None,
        recipient_pool_size=10,
        min_pool_size=5,
    )
    assert decision.mode == DeliveryMode.DELIVER_PEER
    assert decision.hold_reason is None


def test_is_low_density_boundaries():
    assert is_low_density(4, 5)
    assert not is_low_density(5, 5)
    assert not is_low_density(6, 5)
