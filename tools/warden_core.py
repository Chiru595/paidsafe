"""Warden: kill switch, circuit breaker and approval enforcement. No LLM.

It decides who someone is ONLY by the Switch sender id on the message (config/roles.json), never by the
display name, so an account renamed to "Accountant" gets nowhere.

`Warden.on_message` is a pure-ish function over room state: it takes one room message and returns the
replies to post. The Switch transport lives in agents/warden/agent.py.
"""
from __future__ import annotations

import os
import re
import time

from tools.common import (
    Frozen, audit, freeze, frozen_info, get_state, is_auto_reply, load_invoices, load_roles, record_approval,
    record_rejection,
    set_state, unfreeze,
)
from tools import memory
from tools.evidence import render_proofs, verify_draft
from tools.facts import OPTIONS
from tools.send_client_message import NotApproved, draft_hash, send

BREAKER_LIMIT = int(os.environ.get("PAIDSAFE_BREAKER_LIMIT", "12"))
REJECTION_LIMIT = 3
OVERFLOW_LIMIT = 2
SYSTEM_AGENTS = {"ledger", "warden"}

MENTION = re.compile(r"@[\w.\-]+")
APPROVE_OPTION = re.compile(r"^approve\s+\(?([A-D])\)?\.?$", re.I)
# Switch reserves "!" for its own room commands (it answers "Unknown command" and never forwards them),
# so the kill switch is addressed to the Warden: "@warden stopall", "@warden resume".
STOP = re.compile(r"^!?stop\s*all\b", re.I)
RESUME = re.compile(r"^!?resume\.?$", re.I)
OUTCOME = re.compile(r"^outcome\s+(?:(paid)\s+(?:in\s+)?(\d{1,3})(?:\s*days?)?|(unpaid|disputed|partial))\.?$", re.I)


def _clean(text: str) -> str:
    return MENTION.sub("", text).strip()


class Warden:
    def __init__(self, room: str, debaters: set[str] | None = None, invoice_id: str = "INV-1042"):
        self.room = room
        self.invoice_id = invoice_id
        self.debaters = debaters or set(os.environ.get("PAIDSAFE_DEBATERS", "relationship,cash").split(","))

    # ----- helpers -----
    def _inv(self) -> str:
        return (get_state(self.room, "debate") or {}).get("invoice", self.invoice_id)

    def role_of(self, sender_id: str) -> str | None:
        return load_roles().get(sender_id)

    def _reject(self, sender_id: str, sender_name: str, what: str, needed: str) -> list[str]:
        n = record_rejection(self.room, sender_id, f"{what} needs {needed}")
        out = [f"⛔ **Rejected:** `{what}` needs the verified **{needed}**. Switch sender id `{sender_id}` "
               f"(@{sender_name}) is not that person. Display names are ignored: only the Switch sender id counts."]
        if n > REJECTION_LIMIT and not frozen_info(self.room):
            out += self._freeze("warden", None, f"circuit breaker: {n} rejected approval attempts in 10 minutes")
        return out

    def _freeze(self, role: str, sender_id: str | None, reason: str) -> list[str]:
        freeze(self.room, role, sender_id, reason)
        return [f"🧊 **ROOM FROZEN** by {role}: {reason}.\n"
                f"Every side-effecting tool (send, ledger update, payment) now refuses to run. "
                f"Agents: stop and reply only \"Paused (room frozen).\" "
                f"To resume, the *other* verified human types `@warden resume`."]

    # ----- main entry -----
    def on_message(self, sender_id: str, sender_name: str, text: str) -> list[str]:
        name = (sender_name or "").lower().lstrip("@")
        if name in SYSTEM_AGENTS:
            return []
        role = self.role_of(sender_id)
        if name in self.debaters and not role:
            return [] if is_auto_reply(text) else self._on_debater(name, text)
        set_state(self.room, "agent_streak", 0)  # a human spoke
        return self._on_human(sender_id, sender_name, role, _clean(text))

    # ----- agents -----
    def _on_debater(self, name: str, text: str) -> list[str]:
        out: list[str] = []
        if frozen_info(self.room):
            return []
        streak = get_state(self.room, "agent_streak", 0) + 1
        set_state(self.room, "agent_streak", streak)
        if streak > BREAKER_LIMIT:
            return self._freeze("warden", None, f"circuit breaker: {streak} agent messages with no human message")

        req = get_state(self.room, "draft_request")
        if req and req["agent"] == name and not get_state(self.room, "draft"):
            return self._capture_draft(name, text)

        debate = get_state(self.room, "debate") or {}
        if debate.get("status") == "closed":
            overflow = get_state(self.room, "overflow", 0) + 1
            set_state(self.room, "overflow", overflow)
            if overflow >= OVERFLOW_LIMIT:
                out += self._freeze("warden", None, "circuit breaker: debate passed its 2-round cap")
        return out

    def _capture_draft(self, name: str, text: str) -> list[str]:
        h = draft_hash(text)
        ev = verify_draft(text, self._inv())
        set_state(self.room, "draft", {"text": text.strip(), "hash": h, "by": name, "verified": ev.ok,
                                       "facts_hash": ev.facts_hash})
        audit("draft", self.room, None, f"draft captured from {name}", draft=h, verified=ev.ok,
              facts_hash=ev.facts_hash, problems=ev.problems)
        if not ev.ok:
            set_state(self.room, "draft_request", None)
            return [f"📝 Draft from {name} (hash `{h}`) **failed the evidence check** and cannot be approved:\n"
                    + "\n".join(f"- ❌ {p}" for p in ev.problems)
                    + f"\nOwner: type `approve {get_state(self.room, 'decision')['option']}` again to request a redraft."]
        return [f"📝 **Draft captured** from {name} (hash `{h}`). ✅ Evidence check passed: every amount traces "
                f"to a fact card (facts `{ev.facts_hash}`).\n{render_proofs(ev)}\n"
                f"Next: **Accountant** types `approve numbers`, then **Owner** types `approve send`."]

    # ----- humans -----
    def _on_human(self, sender_id: str, sender_name: str, role: str | None, text: str) -> list[str]:
        low = text.lower()
        if STOP.match(low):
            if role not in ("owner", "accountant"):
                return self._reject(sender_id, sender_name, "stopall", "Owner or Accountant")
            if frozen_info(self.room):
                return ["🧊 Already frozen."]
            return self._freeze(role, sender_id, f"manual stopall by the {role}")

        if RESUME.match(low):
            info = frozen_info(self.room)
            if not info:
                return ["ℹ️ The room is not frozen."]
            if role not in ("owner", "accountant"):
                return self._reject(sender_id, sender_name, "resume", "Owner or Accountant")
            if info["by_role"] == role:
                audit("resume_refused", self.room, sender_id, "same key", role=role)
                return [f"🔐 **Resume refused:** the {role} froze the room, so the *other* human must resume it "
                        f"(two-key rule)."]
            unfreeze(self.room, role, sender_id)
            set_state(self.room, "agent_streak", 0)
            set_state(self.room, "overflow", 0)
            mins = (time.time() - info["ts"]) / 60
            return [f"▶️ **Resumed** by the {role}. The room was frozen by {info['by_role']} for {mins:.1f} min "
                    f"({info['reason']})."]

        m = OUTCOME.match(text)
        if m:
            if role != "accountant":
                return self._reject(sender_id, sender_name, "outcome", "Accountant")
            status, days = ("paid", int(m.group(2))) if m.group(1) else (m.group(3).lower(), None)
            client = load_invoices()[self._inv()]["client"]
            entry = memory.record_outcome(client, status, days)
            if not entry:
                return ["ℹ️ No sent decision is waiting for an outcome."]
            audit("outcome", self.room, sender_id, f"{entry['invoice']} option {entry['option']}: {status}",
                  days=days, role=role)
            return [f"📒 **Outcome recorded** by the verified Accountant: {entry['invoice']}, option "
                    f"({entry['option']}) → **{memory.describe_outcome(entry['outcome'])}**.\n"
                    f"The next debate for this client will cite it as fact card **F7**, and the option that "
                    f"worked will be marked on the options card."]

        m = APPROVE_OPTION.match(text)
        if m:
            if role != "owner":
                return self._reject(sender_id, sender_name, f"approve {m.group(1).upper()}", "Owner")
            if frozen_info(self.room):
                return ["🧊 Room is frozen; approvals are paused."]
            return self._choose(sender_id, m.group(1).upper())

        if low.startswith("approve numbers"):
            if role != "accountant":
                return self._reject(sender_id, sender_name, "approve numbers", "Accountant")
            return self._approve(sender_id, role, "numbers")

        if low.startswith("approve send"):
            if role != "owner":
                return self._reject(sender_id, sender_name, "approve send", "Owner")
            out = self._approve(sender_id, role, "send")
            if out and out[0].startswith("✅"):
                out += self._try_send()
            return out

        if re.match(r"^(approve|approved)\b", low) and role not in ("owner", "accountant"):
            return self._reject(sender_id, sender_name, text[:40], "Owner or Accountant")
        return []

    def _choose(self, sender_id: str, option: str) -> list[str]:
        label, side = OPTIONS[option]
        set_state(self.room, "decision", {"option": option, "label": label, "by": sender_id})
        set_state(self.room, "draft", None)
        set_state(self.room, "draft_request", {"agent": side, "option": option})
        record_approval(self.room, "option", option, sender_id, "owner")
        return [f"✅ Owner chose **({option})** {label}.\n"
                f"@{side} please draft the client message for option {option} to MegaMart about {self._inv()}. "
                f"Plain client-facing text, no [F#] tags, amounts only from the fact cards."]

    def _approve(self, sender_id: str, role: str, kind: str) -> list[str]:
        if frozen_info(self.room):
            return ["🧊 Room is frozen; approvals are paused."]
        draft = get_state(self.room, "draft")
        if not draft:
            return ["ℹ️ No draft to approve yet."]
        if not draft.get("verified"):
            return [f"⛔ Draft `{draft['hash']}` failed the evidence check, so it cannot be approved. Request a redraft."]
        if kind == "send" and not get_state(self.room, "approved_numbers_" + draft["hash"]):
            return [f"⏳ The Accountant must `approve numbers` for draft `{draft['hash']}` first."]
        record_approval(self.room, kind, draft["hash"], sender_id, role)
        if kind == "numbers":
            set_state(self.room, "approved_numbers_" + draft["hash"], True)
        return [f"✅ {role.capitalize()} approved **{kind}** for draft `{draft['hash']}` (verified sender id)."]

    def _try_send(self) -> list[str]:
        try:
            path = send(self.room, self._inv())
        except Frozen as e:
            return [f"🧊 Send refused: {e}"]
        except NotApproved as e:
            return [f"⛔ Send refused: {e}"]
        return [f"📤 **Sent (simulated).** Written to `{path}`. Playbook updated for MegaMart."]
