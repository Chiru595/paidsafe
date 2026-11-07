"""Ledger: fact cards, the 2-round debate referee, fact-checks and the options card. No LLM.

`Ledger.on_message` takes one room message and returns the replies to post. Transport lives in
agents/ledger/agent.py.
"""
from __future__ import annotations

import os
import re

from tools.common import frozen_info, get_state, load_roles, set_state
from tools.factcheck import check, render
from tools.facts import build_facts, options_card, render_fact_cards

START = re.compile(r"chase|wait|late|facts|debate", re.I)
SYSTEM_AGENTS = {"ledger", "warden"}


def _quote(text: str, limit: int = 500) -> str:
    t = text.strip().replace("\n", " ")
    return "> " + (t if len(t) <= limit else t[: limit - 3] + "...")


class Ledger:
    def __init__(self, room: str, debaters: list[str] | None = None, invoice_id: str = "INV-1042",
                 client_key: str = "megamart"):
        self.room = room
        self.invoice_id = invoice_id
        self.client_key = client_key
        self.debaters = debaters or os.environ.get("PAIDSAFE_DEBATERS", "relationship,cash").split(",")

    def on_message(self, sender_id: str, sender_name: str, text: str, addressed: bool) -> list[str]:
        name = (sender_name or "").lower().lstrip("@")
        if name in SYSTEM_AGENTS:
            return []
        if name in self.debaters and sender_id not in load_roles():
            return self._on_debater(name, text)
        if addressed and START.search(text):
            return self._start(sender_id)
        return []

    def _start(self, sender_id: str) -> list[str]:
        if frozen_info(self.room):
            return ["🧊 Room is frozen. The Ledger will not open a debate until it is resumed."]
        role = load_roles().get(sender_id)
        if role != "owner":
            return ["⛔ Only the verified Owner can open a debate (checked by Switch sender id)."]
        for key, val in (("debate", {"status": "round1", "posted": {}, "posts": {}}), ("decision", None),
                         ("draft", None), ("draft_request", None), ("overflow", 0), ("agent_streak", 0)):
            set_state(self.room, key, val)
        facts = render_fact_cards(build_facts(self.invoice_id), self.client_key)
        mentions = " ".join(f"@{d}" for d in self.debaters)
        return [facts,
                f"### 🥊 Round 1 of 2\n{mentions} {self.invoice_id} is late. **Chase or wait?** "
                f"Give your recommendation independently, under 150 words. "
                f"**Every number must cite a fact card like [F3]**; uncited or wrong numbers get flagged ❌."]

    def _on_debater(self, name: str, text: str) -> list[str]:
        debate = get_state(self.room, "debate") or {}
        status = debate.get("status")
        if status not in ("round1", "round2") or frozen_info(self.room):
            return []
        out = [render(name, check(text, build_facts(self.invoice_id)))]
        posted = debate.setdefault("posted", {})
        posts = debate.setdefault("posts", {})
        if name not in posted:
            posted[name] = True
            posts[name] = text
        if all(d in posted for d in self.debaters):
            if status == "round1":
                a, b = self.debaters[0], self.debaters[1]
                debate = {"status": "round2", "posted": {}, "posts": {}}
                out.append(
                    f"### 🥊 Round 2 of 2 (rebuttal)\n"
                    f"@{a} rebut {b}:\n{_quote(posts[b])}\n\n@{b} rebut {a}:\n{_quote(posts[a])}\n\n"
                    f"Fact ids only. This is the last round.")
            else:
                debate = {"status": "closed", "posted": {}, "posts": {}}
                out.append(options_card(self.invoice_id))
        set_state(self.room, "debate", debate)
        return out
