"""Push agents/instructions/*.md (debate rules + guardrails) to the Switch-managed debaters, and lock down
their Claude Code workspaces so they cannot use any tool except Switch.

    python scripts/sync_agents.py            # show what would change
    python scripts/sync_agents.py --apply

Uses the Gateway's managed-agent route (PATCH /gateway/management/agents/{id}) with the full definition, so
everything except `instructions` is kept as it is.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agents.switch_client import base_url, http  # noqa: E402
from scripts.register_agents import console_admin_opener  # noqa: E402

DEBATERS = ("relationship", "cash")
# Different models on purpose (debate works better with diverse models). Pinned, not left to defaults.
PINNED_MODELS = {"relationship": "claude-opus-5-5", "cash": "claude-sonnet-5-5"}

# Defence in depth: even if a prompt is subverted, the debater's Claude Code session has no shell, no file
# access and no web. It can still use its Switch tools (MCP), which is how it posts in the room.
WORKSPACE_SETTINGS = {
    "permissions": {
        "deny": ["Bash", "Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Glob", "Grep",
                 "WebFetch", "WebSearch", "Task", "TodoWrite"],
    }
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    base = base_url()
    opener = console_admin_opener(base)
    listing = http("GET", f"{base}/gateway/management/agents", opener=opener)
    agents = listing.get("agents", listing) if isinstance(listing, dict) else listing
    for ag in agents:
        name = ag.get("name") or ag.get("agent", {}).get("name")
        if name not in DEBATERS:
            continue
        definition = ag.get("definition") or {}
        new_instr = (ROOT / "agents" / "instructions" / f"{name}.md").read_text(encoding="utf-8")
        changed = definition.get("instructions", "").strip() != new_instr.strip()
        if name in PINNED_MODELS and definition.get("model") != PINNED_MODELS[name]:
            definition["model"] = PINNED_MODELS[name]
            changed = True
        directory = definition.get("directory")
        print(f"{name}: instructions {'differ' if changed else 'match'}; model={definition.get('model')}; dir={directory}")
        if not a.apply:
            continue
        if directory:
            settings = Path(directory) / ".claude" / "settings.json"
            settings.parent.mkdir(parents=True, exist_ok=True)
            settings.write_text(json.dumps(WORKSPACE_SETTINGS, indent=2), encoding="utf-8")
            print(f"  locked workspace tools: {settings}")
        if changed:
            definition["instructions"] = new_instr
            agent_id = ag.get("agent_id") or ag.get("id")
            http("PATCH", f"{base}/gateway/management/agents/{agent_id}", {"definition": definition}, opener=opener)
            print(f"  definition updated (model={definition.get('model')})")


if __name__ == "__main__":
    main()
