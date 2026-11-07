"""Reset PaidSafe's local state for a clean demo run: room state, approvals, audit log, outbox, playbook.

    python demo/reset.py            # wipe everything
    python demo/reset.py --keep-playbook   # keep the MegaMart playbook (to show "the room gets smarter")

It does not touch Switch, Mattermost history or config/roles.json.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.common import OUTBOX, STATE_DIR  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-playbook", action="store_true")
    a = ap.parse_args()
    for f in ("state.db", "audit.log"):
        (STATE_DIR / f).unlink(missing_ok=True)
    if OUTBOX.exists():
        for f in OUTBOX.glob("*.md"):
            f.unlink()
    if not a.keep_playbook:
        pb = STATE_DIR / "playbooks"
        if pb.exists():
            for f in pb.glob("*.md"):
                f.unlink()
    print("Reset done." + (" Playbook kept." if a.keep_playbook else ""))


if __name__ == "__main__":
    main()
