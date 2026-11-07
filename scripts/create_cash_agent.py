"""Create the Cash debater as a managed Claude Code agent from a template document (no Console clicks).

Uses the Gateway's template runner (POST /gateway/rooms/from-template-document), the same route Switch
Console uses. Works around the Windows Console 0.40.1 bug where the template form shows providers as
"Not supported here".

Cash runs on a different Claude model from Relationship (Codex was the plan; see README disclosure).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agents.switch_client import base_url, http  # noqa: E402
from scripts.register_agents import console_admin_opener  # noqa: E402

MODEL = os.environ.get("CASH_MODEL", "claude-sonnet-5-5")
WORKDIR = Path(os.environ.get("CASH_DIR", ROOT.parent / "paidsafe-agents" / "cash"))


def main() -> None:
    WORKDIR.mkdir(parents=True, exist_ok=True)
    doc = {
        "version": 1,
        "params": {"machine": {"type": "machine", "default": ["$first"]}},
        "agent": {
            "name": "cash",
            "display_name": "cash",
            "description": "Debater: argues to get paid now (cash flow, statutory rights)",
            "provider": "claude",
            "machine": "{machine}",
            "directory": str(WORKDIR),
            "model": MODEL,
            "addressing": "anyone",
            "instructions": (ROOT / "agents" / "instructions" / "cash.md").read_text(encoding="utf-8"),
        },
    }
    base = base_url()
    opener = console_admin_opener(base)
    try:
        res = http("POST", f"{base}/gateway/rooms/from-template-document",
                   {"template": yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
                    "template_name": "paidsafe-cash-agent"}, opener=opener)
    except urllib.error.HTTPError as e:
        sys.exit(f"{e.code}: {e.read().decode()[:800]}")
    print(json.dumps(res, indent=2)[:800])


if __name__ == "__main__":
    main()
