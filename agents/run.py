"""Run the Ledger and Warden custom agents in one process (two separate Switch agent connections).

    python -m agents.run                      # room resolved by name "client-megamart"
    PAIDSAFE_ROOM_ID=<uuid> python -m agents.run

Each human can type `@warden whoami` in the room: the Warden replies with the Switch sender id, which goes in
config/roles.json.
"""
from __future__ import annotations

import asyncio
import json
import re
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.switch_client import AgentConnection, base_url, http, load_agents  # noqa: E402
from tools.common import STATE_DIR, load_roles  # noqa: E402
from tools.facts import read_playbook  # noqa: E402
from tools.ledger_core import Ledger  # noqa: E402
from tools.warden_core import Warden  # noqa: E402

ROOM_NAME = os.environ.get("PAIDSAFE_ROOM", "client-megamart")


def resolve_room_id() -> str:
    if os.environ.get("PAIDSAFE_ROOM_ID"):
        return os.environ["PAIDSAFE_ROOM_ID"]
    a = load_agents()["ledger"]
    rooms = http("POST", f"{base_url()}/agents/{a['id']}/ops/list_rooms", {},
                 {"Authorization": f"Bearer {a['api_key']}"})["result"]
    rooms = rooms["rooms"] if isinstance(rooms, dict) else rooms
    for r in rooms:
        if r["name"].split(": ", 1)[-1] == ROOM_NAME:
            return r["room_id"]
    raise SystemExit(f"Room '{ROOM_NAME}' not found for the Ledger. Add the ledger bot to the channel first.")


async def main() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler(STATE_DIR / "agents.log", encoding="utf-8")])
    room_id = resolve_room_id()
    logging.info("room %s = %s; roles loaded for %d sender ids", ROOM_NAME, room_id, len(load_roles()))

    ledger, warden = Ledger(ROOM_NAME), Warden(ROOM_NAME)

    async def on_ledger(p: dict) -> list[str]:
        return ledger.on_message(p.get("sender", ""), p.get("sender_name", ""), p.get("body") or "",
                                 bool(p.get("addressed")))

    async def on_warden(p: dict) -> list[str]:
        body = (p.get("body") or "").strip()
        if re.sub(r"@[\w.\-]+", "", body).strip().lower().lstrip("!") == "whoami":
            role = load_roles().get(p.get("sender", ""), "no role")
            return [f"🪪 Switch sender id for **{p.get('sender_name')}**: `{p.get('sender')}` ({role})"]
        replies = warden.on_message(p.get("sender", ""), p.get("sender_name", ""), body)
        if any(r.startswith("📤") for r in replies):
            await asyncio.to_thread(sync_playbook_doc)
        return replies

    def sync_playbook_doc() -> None:
        """Mirror the client playbook into a Switch room document. Only its creator (the Warden) can edit
        it, so no debater can rewrite the room's memory."""
        content = read_playbook("megamart") or "(no decisions yet)"
        ids_file = STATE_DIR / "room_docs.json"  # survives demo/reset.py, so we never create a duplicate doc
        ids = json.loads(ids_file.read_text()) if ids_file.exists() else {}
        doc_id = ids.get(f"{room_id}/megamart-playbook")
        try:
            if doc_id:
                warden_conn.op("update_room_document", {"document_id": doc_id, "content": content})
            else:
                res = warden_conn.op("create_room_document", {
                    "name": "megamart-playbook",
                    "description": "PaidSafe decisions for MegaMart: what we chose, why, and how it went",
                    "instructions": "Read before any new MegaMart debate. Written only by the Warden after a verified send.",
                    "content": content})["result"]
                ids[f"{room_id}/megamart-playbook"] = res.get("id") or res.get("document_id")
                ids_file.write_text(json.dumps(ids, indent=2))
            logging.info("playbook room document synced")
        except Exception:
            logging.exception("playbook room document sync failed (local playbook is still written)")

    ledger_conn = AgentConnection("ledger", room_id, on_ledger)
    warden_conn = AgentConnection("warden", room_id, on_warden)
    await asyncio.gather(ledger_conn.run(), warden_conn.run())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
