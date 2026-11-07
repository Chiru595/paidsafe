"""Evidence checks for anything that leaves the room: every amount must trace to a fact card.

`verify_draft` is called by the Warden when a draft is captured AND again by the send tool, so a draft with
an unproven number can be neither approved nor sent, whatever an agent says.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from tools.factcheck import _numbers
from tools.facts import Fact, build_facts

MIN_AMOUNT = 100  # smaller numbers (days, %, counts) are checked in the debate, not as money in a letter


@dataclass
class Evidence:
    ok: bool
    problems: list[str] = field(default_factory=list)
    proofs: list[dict] = field(default_factory=list)  # [{value, fact, source}]
    facts_hash: str = ""


def facts_hash(facts: list[Fact]) -> str:
    blob = json.dumps([[f.id, f.text, f.values, f.source] for f in facts], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:10]


def _match(value: float, facts: list[Fact]) -> Fact | None:
    for f in facts:
        for v in f.values:
            if v and abs(v - value) <= max(1, 0.005 * abs(v)):
                return f
    return None


def verify_draft(text: str, invoice_id: str = "INV-1042", facts: list[Fact] | None = None) -> Evidence:
    facts = facts or build_facts(invoice_id)
    ev = Evidence(ok=True, facts_hash=facts_hash(facts))
    if invoice_id not in text:
        ev.problems.append(f"does not mention {invoice_id} (out of scope or wrong invoice)")
    if "[F" in text:
        ev.problems.append("contains internal [F#] tags; client-facing text must not")
    for n in _numbers(text):
        if n < MIN_AMOUNT:
            continue
        f = _match(n, facts)
        if f is None:
            ev.problems.append(f"{n:,.0f} is not on any fact card")
        else:
            ev.proofs.append({"value": n, "fact": f.id, "source": f.source})
    ev.ok = not ev.problems
    return ev


def render_proofs(ev: Evidence) -> str:
    seen, lines = set(), []
    for p in ev.proofs:
        key = (p["value"], p["fact"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- {p['value']:,.0f} → {p['fact']} ({p['source']})")
    return "\n".join(lines) or "- (no amounts)"
