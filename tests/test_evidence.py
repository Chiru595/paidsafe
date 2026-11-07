import pytest

from conftest import ACCOUNTANT, OWNER, ROOM
from tools.evidence import verify_draft
from tools.send_client_message import NotApproved, send
from tools.warden_core import Warden
from tools import common


def test_draft_with_fact_card_amounts_passes():
    ev = verify_draft("INV-1042: ₹4,80,000 plus interest ₹7,130, total ₹4,87,130.")
    assert ev.ok and {p["fact"] for p in ev.proofs} == {"F1", "F3"}


def test_draft_with_invented_amount_fails():
    ev = verify_draft("INV-1042: please pay ₹5,00,000 by Friday.")
    assert not ev.ok and ev.problems == ["500,000 is not on any fact card"]


def test_draft_about_another_invoice_is_out_of_scope():
    assert not verify_draft("INV-9999: please pay ₹4,80,000.").ok


def test_draft_with_internal_tags_fails():
    assert not verify_draft("INV-1042 is ₹4,80,000 [F1].").ok


def test_unverified_draft_cannot_be_approved_or_sent():
    w = Warden(ROOM, debaters={"relationship", "cash"})
    w.on_message(OWNER, "user", "approve B")
    out = "\n".join(w.on_message("@a", "cash", "INV-1042: please pay ₹9,99,999 now.", ))
    assert "failed the evidence check" in out
    assert "cannot be approved" in "\n".join(w.on_message(ACCOUNTANT, "accountant", "approve numbers"))
    # even with forged approval rows, the send tool re-checks the evidence itself
    d = common.get_state(ROOM, "draft")
    common.record_approval(ROOM, "numbers", d["hash"], ACCOUNTANT, "accountant")
    common.record_approval(ROOM, "send", d["hash"], OWNER, "owner")
    with pytest.raises(NotApproved, match="evidence"):
        send(ROOM)


def test_sent_file_carries_evidence(isolated_state):
    w = Warden(ROOM, debaters={"relationship", "cash"})
    w.on_message(OWNER, "user", "approve B")
    w.on_message("@a", "cash", "INV-1042 for ₹4,80,000 is overdue; interest to date is ₹7,130.")
    w.on_message(ACCOUNTANT, "accountant", "approve numbers")
    w.on_message(OWNER, "user", "approve send")
    text = next((isolated_state / "outbox").glob("*.md")).read_text(encoding="utf-8")
    assert "Evidence" in text and "→ F1" in text and "→ F3" in text
