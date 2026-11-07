"""Shared paths, data loading, room state (sqlite) and the audit log.

Every side-effecting tool goes through this module, so the freeze flag and the approval records are
enforced in code, not in agent prompts.
"""
from __future__ import annotations

import csv
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RULES = ROOT / "rules"
STATE_DIR = Path(os.environ.get("PAIDSAFE_STATE_DIR", ROOT / "state"))
OUTBOX = Path(os.environ.get("PAIDSAFE_OUTBOX", ROOT / "outbox"))
CONFIG = ROOT / "config"

DISCLAIMER = "Calculations follow the cited public rules for information only. Not legal or financial advice."


# ---------- data ----------

def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_rules(jurisdiction: str) -> dict:
    with open(RULES / f"{jurisdiction}.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_invoices() -> dict[str, dict]:
    with open(DATA / "invoices.csv", encoding="utf-8", newline="") as f:
        return {row["invoice_id"]: row for row in csv.DictReader(f)}


def as_of_date() -> date:
    """The demo runs on a fixed date so every number is reproducible. Override with PAIDSAFE_AS_OF."""
    return date.fromisoformat(os.environ.get("PAIDSAFE_AS_OF", load_json(DATA / "company.json")["as_of"]))


def inr(amount: float) -> str:
    """Indian digit grouping: 480000 -> ₹4,80,000."""
    neg = amount < 0
    amount = round(abs(amount))
    s = str(amount)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups) + "," + tail
    return ("-" if neg else "") + "₹" + s


# Switch posts these on an agent's behalf (content marker com.switch.auto_reply); they are not the agent's
# own words, so they never count as a debate turn, a draft, or a circuit-breaker tick.
AUTO_REPLY_PREFIXES = ("Starting a session to handle this", "Hi! I'm here to help", "Hi! I'm ")


def is_auto_reply(body: str) -> bool:
    return (body or "").strip().startswith(AUTO_REPLY_PREFIXES)


# ---------- state ----------

SCHEMA = """
CREATE TABLE IF NOT EXISTS room_state (room TEXT, key TEXT, value TEXT, PRIMARY KEY (room, key));
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT, kind TEXT, subject TEXT,
    sender_id TEXT, role TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS rejections (room TEXT, sender_id TEXT, reason TEXT, ts REAL);
"""


@contextmanager
def db():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(STATE_DIR / "state.db", timeout=10)
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_state(room: str, key: str, default=None):
    with db() as c:
        row = c.execute("SELECT value FROM room_state WHERE room=? AND key=?", (room, key)).fetchone()
    return json.loads(row[0]) if row else default


def set_state(room: str, key: str, value) -> None:
    with db() as c:
        c.execute("INSERT OR REPLACE INTO room_state (room, key, value) VALUES (?, ?, ?)",
                  (room, key, json.dumps(value)))


def del_state(room: str, key: str) -> None:
    with db() as c:
        c.execute("DELETE FROM room_state WHERE room=? AND key=?", (room, key))


def audit(event: str, room: str, sender_id: str | None, reason: str = "", **extra) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event,
             "room": room, "sender_id": sender_id, "reason": reason, **extra}
    with open(STATE_DIR / "audit.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------- freeze ----------

class Frozen(PermissionError):
    pass


def frozen_info(room: str) -> dict | None:
    return get_state(room, "frozen")


def require_not_frozen(room: str) -> None:
    """Called first by every side-effecting tool."""
    info = frozen_info(room)
    if info:
        raise Frozen(f"Room {room} is FROZEN since {info['since']} by {info['by_role']} ({info['reason']}). Refusing.")


def freeze(room: str, by_role: str, by_sender: str | None, reason: str) -> dict:
    info = {"since": datetime.now(timezone.utc).isoformat(timespec="seconds"), "ts": time.time(),
            "by_role": by_role, "by_sender": by_sender, "reason": reason}
    set_state(room, "frozen", info)
    audit("freeze", room, by_sender, reason, by_role=by_role)
    return info


def unfreeze(room: str, by_role: str, by_sender: str) -> dict:
    info = frozen_info(room) or {}
    del_state(room, "frozen")
    audit("resume", room, by_sender, "two-key resume", by_role=by_role, frozen_by=info.get("by_role"))
    return info


# ---------- roles (verified sender ids) ----------

def load_roles() -> dict[str, str]:
    """Maps Switch sender id -> role ('owner' | 'accountant'). Display names are never used."""
    path = CONFIG / "roles.json"
    if not path.exists():
        return {}
    data = load_json(path)
    return {sid: role for role, sid in data.items() if not role.startswith("_") and sid}


# ---------- approvals ----------

def record_approval(room: str, kind: str, subject: str, sender_id: str, role: str) -> None:
    with db() as c:
        c.execute("INSERT INTO approvals (room, kind, subject, sender_id, role, ts) VALUES (?,?,?,?,?,?)",
                  (room, kind, subject, sender_id, role, time.time()))
    audit("approval", room, sender_id, f"{kind}:{subject}", role=role)


def has_approval(room: str, kind: str, subject: str, role: str) -> bool:
    """True only if a sender currently mapped to `role` approved. Re-checks the role table at use time."""
    roles = load_roles()
    with db() as c:
        rows = c.execute("SELECT sender_id FROM approvals WHERE room=? AND kind=? AND subject=? AND role=?",
                         (room, kind, subject, role)).fetchall()
    return any(roles.get(sid) == role for (sid,) in rows)


def record_rejection(room: str, sender_id: str, reason: str) -> int:
    """Records a rejected approval attempt. Returns how many happened in the last 10 minutes."""
    now = time.time()
    with db() as c:
        c.execute("INSERT INTO rejections (room, sender_id, reason, ts) VALUES (?,?,?,?)",
                  (room, sender_id, reason, now))
        (n,) = c.execute("SELECT COUNT(*) FROM rejections WHERE room=? AND ts>?", (room, now - 600)).fetchone()
    audit("rejected", room, sender_id, reason)
    return n
