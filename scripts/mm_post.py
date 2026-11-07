"""Post to a Mattermost channel as a demo human (for rehearsing the demo and smoke tests).

    python scripts/mm_post.py accountant "approve numbers"
    python scripts/mm_post.py accountant.desk "approve numbers"     # the impostor

Uses the Mattermost REST API with the demo account's password (env MM_DEMO_PASSWORD). Messages go through
Switch exactly like typed ones, so Switch stamps the real sender id on them.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.switch_client import console_ports  # noqa: E402

CHANNEL = os.environ.get("PAIDSAFE_ROOM", "client-megamart")
TEAM = os.environ.get("MM_TEAM", "switch")


def mm_url() -> str:
    return os.environ.get("MM_URL") or f"http://127.0.0.1:{console_ports()['mattermost']}"


def call(method, path, body=None, token=None):
    req = urllib.request.Request(mm_url() + "/api/v4" + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.headers.get("Token"), json.loads(r.read() or b"{}")


def post(username: str, message: str) -> None:
    pw = os.environ.get("MM_DEMO_PASSWORD", "PaidSafe-Demo-2026!")
    token, _ = call("POST", "/users/login", {"login_id": username, "password": pw})
    _, ch = call("GET", f"/teams/name/{TEAM}/channels/name/{CHANNEL}", token=token)
    call("POST", "/posts", {"channel_id": ch["id"], "message": message}, token=token)


if __name__ == "__main__":
    post(sys.argv[1], " ".join(sys.argv[2:]))
    print("posted")
