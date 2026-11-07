from conftest import ACCOUNTANT, IMPOSTOR, OWNER, ROOM
from tools import memory
from tools.facts import build_facts, facts_index, options_card
from tools.ledger_core import Ledger
from tools.warden_core import Warden


def run_send(w):
    w.on_message(OWNER, "user", "approve B")
    w.on_message("@a", "cash", "INV-1042 for ₹4,80,000 is overdue; interest to date is ₹7,130.")
    w.on_message(ACCOUNTANT, "accountant", "approve numbers")
    return "\n".join(w.on_message(OWNER, "user", "approve send"))


def test_no_memory_card_before_any_outcome():
    assert "F7" not in facts_index(build_facts("INV-1058"))


def test_outcome_recorded_by_accountant_becomes_fact_card_f7():
    w = Warden(ROOM, debaters={"relationship", "cash"})
    assert "Sent (simulated)" in run_send(w)
    out = "\n".join(w.on_message(ACCOUNTANT, "accountant", "@warden outcome paid 12"))
    assert "Outcome recorded" in out and "paid 12 days" in out
    f7 = facts_index(build_facts("INV-1058"))["F7"]
    assert "option (B)" in f7.text and 12.0 in f7.values


def test_options_card_marks_the_option_that_worked():
    w = Warden(ROOM, debaters={"relationship", "cash"})
    run_send(w)
    w.on_message(ACCOUNTANT, "accountant", "outcome paid 12")
    card = options_card("INV-1058")
    line_b = next(l for l in card.splitlines() if l.startswith("- **(B)"))
    assert "Worked before" in line_b and "[F7]" in line_b


def test_only_verified_accountant_records_outcomes():
    w = Warden(ROOM, debaters={"relationship", "cash"})
    run_send(w)
    assert "Rejected" in "\n".join(w.on_message(IMPOSTOR, "Accountant", "outcome paid 3"))
    assert "Rejected" in "\n".join(w.on_message(OWNER, "user", "outcome paid 3"))
    assert memory.latest_with_outcome("megamart") is None


def test_debaters_can_cite_f7_and_wrong_memory_is_flagged():
    from tools.factcheck import check
    w = Warden(ROOM, debaters={"relationship", "cash"})
    run_send(w)
    w.on_message(ACCOUNTANT, "accountant", "outcome paid 12")
    assert check("Last time a firm reminder got paid in 12 days [F7].", build_facts("INV-1058")) == []
    assert check("Last time it took 30 days [F7].", build_facts("INV-1058"))


def test_ledger_debates_the_invoice_named_by_the_owner():
    out = Ledger(ROOM, ["relationship", "cash"]).on_message(OWNER, "user", "@ledger INV-1058 is late, chase or wait?", True)
    assert "INV-1058" in out[0] and "INV-1058 is late" in out[1]
