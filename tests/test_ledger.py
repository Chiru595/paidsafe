from conftest import ACCOUNTANT, OWNER, ROOM
from tools.common import get_state
from tools.ledger_core import Ledger


def test_only_owner_opens_debate():
    out = Ledger(ROOM, ["relationship", "cash"]).on_message(ACCOUNTANT, "Accountant", "@ledger chase or wait?", True)
    assert "Only the verified Owner" in out[0]


def test_full_two_round_debate_ends_with_options_card():
    led = Ledger(ROOM, ["relationship", "cash"])
    out = led.on_message(OWNER, "user", "@ledger MegaMart INV-1042 is late. Chase or wait?", True)
    assert "F1" in out[0] and "Round 1" in out[1]

    out = led.on_message("@a-rel", "relationship", "Wait: they are 30% of revenue [F4].", False)
    assert out[0].startswith("✅")
    out = led.on_message("@a-cash", "cash", "Chase: interest is ₹25,000 [F3].", False)
    assert out[0].startswith("❌") and "Round 2" in out[1]

    led.on_message("@a-rel", "relationship", "Runway is 8.0 weeks [F5], so we can wait.", False)
    out = led.on_message("@a-cash", "cash", "Interest is ₹6,820 [F3] and grows.", False)
    assert "Options card" in out[-1]
    assert get_state(ROOM, "debate")["status"] == "closed"


def test_ledger_ignores_debaters_after_close():
    led = Ledger(ROOM, ["relationship", "cash"])
    led.on_message(OWNER, "user", "@ledger chase or wait?", True)
    for name in ("relationship", "cash", "relationship", "cash"):
        led.on_message("@x", name, "ok", False)
    assert led.on_message("@x", "cash", "one more [F9]", False) == []
