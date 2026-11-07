"""Register the Ledger and Warden as custom agents (agent protocol, POST /agents). Run once.

Needs a `registration` API key, created on the Gateway's API Keys page while signed in as yourself, so you
own the agents. Pass it as SWITCH_REGISTRATION_KEY. On a Switch Console local server you can instead pass
--console-admin, which signs in to the Gateway with the admin account Console created and makes the key.
Never use the deployment bootstrap key: agents registered with it belong to a different account.

Writes the agents' ids and API keys to .agents.json (gitignored).
"""
from __future__ import annotations

import argparse
from http.cookiejar import CookieJar
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.switch_client import AGENTS_FILE, base_url, http, load_agents  # noqa: E402

AGENTS = {
    "ledger": "PaidSafe Ledger: fact cards, debate referee, fact-check, options card. Deterministic, no LLM.",
    "warden": "PaidSafe Warden: kill switch, circuit breaker, verified-sender approvals. Deterministic, no LLM.",
}
PROFILE = {"connection_model": "always_on", "message_exchange": True,
           "pre_invocation_mediation": [], "post_invocation_mediation": [], "event_reporting": []}


def console_admin_opener(base: str):
    env = Path(os.environ["APPDATA"]) / "switchdash" / "local-switch-server" / "native" / "run" / "switch-core.env"
    vals = dict(l.split("=", 1) for l in env.read_text().splitlines() if "=" in l and not l.startswith("#"))
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    http("POST", f"{base}/gateway/auth/login",
         {"email": vals["GATEWAY_ADMIN_EMAIL"], "password": vals["GATEWAY_ADMIN_PASSWORD"]}, opener=opener)
    return opener


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--console-admin", action="store_true", help="create the registration key via Console's admin login")
    ap.add_argument("--overwrite", action="store_true", help="re-register (issues new API keys)")
    a = ap.parse_args()
    base = base_url()

    key = os.environ.get("SWITCH_REGISTRATION_KEY")
    opener = console_admin_opener(base) if a.console_admin else None
    if not key:
        if not a.console_admin:
            sys.exit("Set SWITCH_REGISTRATION_KEY (Gateway → API Keys → new key) or pass --console-admin.")
        key = http("POST", f"{base}/gateway/api-keys", {"label": "paidsafe-registration"}, opener=opener)["key"]
        print("Created a registration key via the Console admin login.")

    saved = load_agents()
    for name, desc in AGENTS.items():
        if name in saved and not a.overwrite:
            print(f"{name}: already registered ({saved[name]['id']})")
            continue
        body = {"name": name, "description": desc, "display_name": name.capitalize(),
                "connector_type": "paidsafe-python", "integration_profile": PROFILE, "overwrite": a.overwrite}
        try:
            res = http("POST", f"{base}/agents", body, {"Authorization": f"Bearer {key}"})
        except urllib.error.HTTPError as e:
            sys.exit(f"{name}: registration failed {e.code}: {e.read().decode()[:300]}")
        saved[name] = {"id": res["id"], "api_key": res["api_key"]}
        AGENTS_FILE.write_text(json.dumps(saved, indent=2))
        print(f"{name}: registered {res['id']}")

    # Who may address them: our code enforces roles by Switch sender id, so Switch shouldn't pre-refuse the
    # Accountant. policy=null means "anyone" (Gateway route; the agent itself gets a 403 on this).
    if a.console_admin:
        for name in AGENTS:
            http("PUT", f"{base}/gateway/agents/{saved[name]['id']}/addressing-policy", {"policy": None}, opener=opener)
            print(f"{name}: addressing open to anyone (roles enforced in code)")
    else:
        print("Set each agent's 'who can instruct' to Anyone in Console (Your Agents -> agent -> settings).")
    print(f"Saved to {AGENTS_FILE.name}. Next: add the agents to the room (see README).")


if __name__ == "__main__":
    main()
