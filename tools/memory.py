"""Client memory (the playbook): every verified decision and, later, its real outcome.

Written only by the Warden's tool path: a decision after a verified send, an outcome when the verified
Accountant records it. The Ledger turns the latest outcome into fact card F7, so the next debate for the
same client argues from what actually happened last time. Mirrored to a Switch room document.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from tools.common import ROOT

PLAYBOOKS = ROOT / "state" / "playbooks"


def _path(client_key: str) -> Path:
    return PLAYBOOKS / f"{client_key}.json"


def load(client_key: str) -> list[dict]:
    p = _path(client_key)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def _save(client_key: str, entries: list[dict]) -> None:
    PLAYBOOKS.mkdir(parents=True, exist_ok=True)
    _path(client_key).write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    (PLAYBOOKS / f"{client_key}.md").write_text(render_md(client_key, entries), encoding="utf-8")


def record_decision(client_key: str, invoice_id: str, option: str, label: str, evidence: list[str],
                    facts_hash: str, draft_hash: str) -> None:
    entries = load(client_key)
    entries.append({"date": datetime.now().strftime("%Y-%m-%d"), "invoice": invoice_id, "option": option,
                    "label": label, "evidence": evidence, "facts_hash": facts_hash, "draft": draft_hash,
                    "outcome": None})
    _save(client_key, entries)


def record_outcome(client_key: str, status: str, days: int | None) -> dict | None:
    """Attach an outcome to the most recent decision that has none. Returns that entry, or None."""
    entries = load(client_key)
    for e in reversed(entries):
        if e.get("outcome") is None:
            e["outcome"] = {"status": status, "days": days, "recorded": datetime.now().strftime("%Y-%m-%d")}
            _save(client_key, entries)
            return e
    return None


def latest_with_outcome(client_key: str) -> dict | None:
    return next((e for e in reversed(load(client_key)) if e.get("outcome")), None)


def describe_outcome(o: dict) -> str:
    if o["status"] == "paid":
        return f"paid {o['days']} days after the message"
    return o["status"]


def render_md(client_key: str, entries: list[dict] | None = None) -> str:
    entries = load(client_key) if entries is None else entries
    lines = [f"# Playbook: {client_key}", "",
             "Written only by the Warden after verified approvals. Outcomes recorded by the verified Accountant.", ""]
    if not entries:
        lines.append("(no decisions yet)")
    for e in entries:
        out = describe_outcome(e["outcome"]) if e.get("outcome") else "pending"
        lines.append(f"- {e['date']}: {e['invoice']} → option {e['option']} ({e['label']}). "
                     f"Evidence: {', '.join(e['evidence']) or 'n/a'} (facts {e['facts_hash']}). Outcome: {out}.")
    return "\n".join(lines) + "\n"
