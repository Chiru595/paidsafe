import pytest

from conftest import ACCOUNTANT, IMPOSTOR, OWNER, ROOM
from tools import common
from tools.common import Frozen, frozen_info, require_not_frozen
from tools.send_client_message import NotApproved, send
from tools.warden_core import BREAKER_LIMIT, Warden


@pytest.fixture
def w():
    return Warden(ROOM, debaters={"relationship", "cash"})


def say(w, sender, text, name="human"):
    return "\n".join(w.on_message(sender, name, text))


def draft_ready(w):
    say(w, OWNER, "approve B", "user")
    out = say(w, "@agent-cash", "Dear MegaMart, INV-1042 for ₹4,80,000 is 32 days overdue.", "cash")
    assert "Draft captured" in out


# ----- freeze -----

def test_stopall_freezes_and_blocks_every_tool(w):
    assert "FROZEN" in say(w, OWNER, "@warden stopall")
    with pytest.raises(Frozen):
        require_not_frozen(ROOM)
    with pytest.raises(Frozen):
        send(ROOM)


def test_freeze_blocks_send_even_with_full_approvals(w):
    draft_ready(w)
    say(w, ACCOUNTANT, "approve numbers")
    common.freeze(ROOM, "owner", OWNER, "test")
    with pytest.raises(Frozen):
        send(ROOM)


def test_impostor_cannot_stop(w):
    out = say(w, IMPOSTOR, "@warden stopall", "Accountant")
    assert "Rejected" in out and frozen_info(ROOM) is None


# ----- two-key resume -----

def test_same_person_cannot_resume(w):
    say(w, OWNER, "@warden stopall")
    out = say(w, OWNER, "@warden resume")
    assert "Resume refused" in out and frozen_info(ROOM) is not None


def test_other_person_resumes(w):
    say(w, OWNER, "@warden stopall")
    out = say(w, ACCOUNTANT, "@warden resume")
    assert "Resumed" in out and frozen_info(ROOM) is None


def test_impostor_cannot_resume(w):
    say(w, OWNER, "@warden stopall")
    out = say(w, IMPOSTOR, "@warden resume", "Accountant")
    assert "Rejected" in out and frozen_info(ROOM) is not None


# ----- impostor approvals -----

def test_impostor_with_accountant_display_name_is_rejected(w):
    draft_ready(w)
    out = say(w, IMPOSTOR, "approve numbers", "Accountant")
    assert "Rejected" in out and IMPOSTOR in out and "Display names are ignored" in out
    say(w, OWNER, "approve send")
    with pytest.raises(NotApproved):
        send(ROOM)


def test_owner_cannot_approve_numbers_for_accountant(w):
    draft_ready(w)
    assert "Rejected" in say(w, OWNER, "approve numbers")


def test_only_owner_picks_option(w):
    assert "Rejected" in say(w, ACCOUNTANT, "approve B")


def test_repeated_rejections_trip_the_breaker(w):
    for _ in range(4):
        out = say(w, IMPOSTOR, "approve numbers", "Accountant")
    assert "FROZEN" in out and frozen_info(ROOM)["by_role"] == "warden"


# ----- happy path -----

def test_full_approval_flow_writes_outbox_and_playbook(w, isolated_state):
    draft_ready(w)
    assert "approved **numbers**" in say(w, ACCOUNTANT, "approve numbers")
    out = say(w, OWNER, "approve send")
    assert "Sent (simulated)" in out
    assert len(list((isolated_state / "outbox").glob("INV-1042-B-*.md"))) == 1
    assert "option B" in (isolated_state / "playbooks" / "megamart.md").read_text(encoding="utf-8")


def test_send_requires_accountant_first(w):
    draft_ready(w)
    out = say(w, OWNER, "approve send")
    assert "must `approve numbers`" in out
    with pytest.raises(NotApproved):
        send(ROOM)


def test_send_tool_refuses_without_approvals(w):
    draft_ready(w)
    with pytest.raises(NotApproved):
        send(ROOM)


# ----- circuit breaker -----

def test_agent_loop_trips_breaker(w):
    out = ""
    for i in range(BREAKER_LIMIT + 1):
        out = say(w, "@agent-relationship", f"thought {i}", "relationship")
    assert "FROZEN" in out and "circuit breaker" in out


def test_human_message_resets_streak(w):
    for i in range(BREAKER_LIMIT):
        say(w, "@agent-relationship", f"thought {i}", "relationship")
    say(w, OWNER, "hello")
    assert "FROZEN" not in say(w, "@agent-relationship", "one more", "relationship")


def test_debate_past_round_cap_trips_breaker(w):
    common.set_state(ROOM, "debate", {"status": "closed"})
    say(w, "@agent-cash", "Round 3, I insist.", "cash")
    out = say(w, "@agent-relationship", "Round 3 rebuttal.", "relationship")
    assert "round cap" in out


def test_switch_auto_reply_is_never_captured_as_draft(w):
    say(w, OWNER, "approve B", "user")
    assert say(w, "@agent-cash", "Starting a session to handle this — one moment.", "cash") == ""
    assert "Draft captured" in say(w, "@agent-cash", "Dear MegaMart, please pay ₹4,80,000.", "cash")
