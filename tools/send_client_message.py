"""Simulated send of the approved client message. Writes to outbox/ only; nothing leaves the machine.

Refuses unless ALL of these hold, checked here and not in any prompt:
1. the room is not frozen,
2. the Owner picked an option,
3. a draft exists,
4. the verified Accountant approved the numbers of THIS draft (by hash),
5. the verified Owner approved sending THIS draft (by hash).
"""
from __future__ import annotations

import argparse
import hashlib
from datetime import datetime

from tools.common import OUTBOX, ROOT, audit, get_state, has_approval, require_not_frozen, set_state
from tools.evidence import render_proofs, verify_draft

PLAYBOOKS = ROOT / "state" / "playbooks"


class NotApproved(PermissionError):
    pass


def draft_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:10]


def send(room: str, invoice_id: str = "INV-1042", client_key: str = "megamart") -> str:
    require_not_frozen(room)
    decision = get_state(room, "decision")
    draft = get_state(room, "draft")
    if not decision:
        raise NotApproved("No option chosen by the Owner yet.")
    if not draft:
        raise NotApproved("No draft to send.")
    h = draft["hash"]
    if draft_hash(draft["text"]) != h:
        raise NotApproved("Draft changed after it was captured.")
    if not has_approval(room, "numbers", h, "accountant"):
        raise NotApproved(f"The verified Accountant has not approved the numbers in draft {h}.")
    if not has_approval(room, "send", h, "owner"):
        raise NotApproved(f"The verified Owner has not approved sending draft {h}.")
    ev = verify_draft(draft["text"], invoice_id)  # re-checked here: the tool trusts no earlier step
    if not ev.ok:
        raise NotApproved("Draft failed the evidence check: " + "; ".join(ev.problems))
    if get_state(room, "sent_hash") == h:
        raise NotApproved(f"Draft {h} was already sent.")

    OUTBOX.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = OUTBOX / f"{invoice_id}-{decision['option']}-{h}-{stamp}.md"
    path.write_text(
        f"To: {client_key} (simulated)\nInvoice: {invoice_id}\nOption: {decision['option']}\n"
        f"Draft hash: {h}\nFacts hash: {ev.facts_hash}\n"
        f"Approved by: verified accountant (numbers), verified owner (send)\n\n{draft['text']}\n\n---\n"
        f"Evidence (every amount above, traced to a Ledger fact card):\n{render_proofs(ev)}\n"
        f"Calculations follow cited public rules for information only. Not legal or financial advice.\n",
        encoding="utf-8",
    )
    set_state(room, "sent_hash", h)
    audit("send", room, None, f"simulated send of {invoice_id} option {decision['option']}", draft=h, file=path.name,
          facts_hash=ev.facts_hash, evidence=[p["fact"] for p in ev.proofs])
    append_playbook(client_key, invoice_id, decision["option"], decision.get("label", ""),
                    sorted({p["fact"] for p in ev.proofs}), ev.facts_hash)
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def append_playbook(client_key: str, invoice_id: str, option: str, label: str,
                    evidence: list[str] | None = None, fhash: str = "") -> None:
    PLAYBOOKS.mkdir(parents=True, exist_ok=True)
    path = PLAYBOOKS / f"{client_key}.md"
    if not path.exists():
        path.write_text(f"# Playbook: {client_key}\n\n", encoding="utf-8")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"- {datetime.now():%Y-%m-%d}: {invoice_id} -> option {option} ({label}). "
                f"Evidence: {', '.join(evidence or []) or 'n/a'} (facts {fhash}). "
                f"Approved by the verified Accountant and Owner. Outcome: pending (fill in when paid).\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--room", default="client-megamart")
    p.add_argument("--invoice", default="INV-1042")
    a = p.parse_args()
    print(send(a.room, a.invoice))
