"""Capture real demo footage: drive the live #client-megamart room and screenshot it at each beat.

The Owner lines are posted by a stand-in account (display name "Owner") mapped as owner in config/roles.json
only for the capture; the real mapping is restored afterwards. Every message goes through Switch.

    python demo/video/capture.py <out_dir>
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.mm_post import CHANNEL, TEAM, call, mm_url, post  # noqa: E402

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "footage")
OUT.mkdir(parents=True, exist_ok=True)
MM = "switchdash-local-mattermost-mattermost-1"
PW = "PaidSafe-Demo-2026!"
STAND_IN = "rehearsal.owner"
STAND_IN_ID = "@switch-mattermost-57466b0b-9368-442d-9729-ebc1ebc4b371-rehearsal-owner:localhost"
ROLES = ROOT / "config" / "roles.json"


def mmctl(*args):
    subprocess.run(["docker", "exec", MM, "mmctl", "--local", *args], capture_output=True, text=True)


def latest(n=12) -> list[str]:
    tok, _ = call("POST", "/users/login", {"login_id": "accountant", "password": PW})
    _, ch = call("GET", f"/teams/name/{TEAM}/channels/name/{CHANNEL}", token=tok)
    _, posts = call("GET", f"/channels/{ch['id']}/posts?per_page={n}", token=tok)
    return [posts["posts"][pid]["message"] for pid in posts["order"]]


def wait_for(marker: str, timeout=240) -> None:
    end = time.time() + timeout
    while time.time() < end:
        if any(marker in m for m in latest()):
            return
        time.sleep(2)
    raise TimeoutError(marker)


def main() -> None:
    from playwright.sync_api import sync_playwright

    backup = ROLES.read_text(encoding="utf-8")
    mmctl("user", "activate", STAND_IN)
    mmctl("user", "edit", "firstname", STAND_IN, "Owner")  # harmless if unsupported; display set below too
    tok, me = call("POST", "/users/login", {"login_id": STAND_IN, "password": PW})
    call("PUT", f"/users/{me['id']}/patch", {"first_name": "Owner", "last_name": ""}, token=tok)
    roles = json.loads(backup)
    roles["owner"] = STAND_IN_ID
    ROLES.write_text(json.dumps(roles, indent=2), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "demo" / "reset.py")], check=True)

    # Switch can drop the first message from a (re)activated user while it recreates the actor: warm up until
    # a stand-in message is actually delivered to the Warden.
    for attempt in range(4):
        post(STAND_IN, "@warden whoami")
        try:
            wait_for("(owner)", timeout=25)
            break
        except TimeoutError:
            print("warm-up not delivered, retrying", flush=True)
    else:
        raise SystemExit("stand-in messages are not reaching Switch")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            ctx = browser.new_context(viewport={"width": 1536, "height": 1100}, device_scale_factor=1.25)
            atok, _ = call("POST", "/users/login", {"login_id": "accountant", "password": PW})
            host = mm_url().split("//")[1].split(":")[0]
            ctx.add_cookies([{"name": "MMAUTHTOKEN", "value": atok, "domain": host, "path": "/"},
                             {"name": "MMUSERID", "value": call("GET", "/users/me", token=atok)[1]["id"],
                              "domain": host, "path": "/"}])
            page = ctx.new_page()
            page.goto(f"{mm_url()}/{TEAM}/channels/{CHANNEL}")
            page.wait_for_timeout(6000)

            def shot(name: str) -> None:
                page.wait_for_timeout(2500)
                page.screenshot(path=str(OUT / f"{name}.png"))
                print("shot", name, flush=True)

            shot("00_room")
            post(STAND_IN, "@ledger MegaMart invoice INV-1042 is late. Chase or wait?")
            wait_for("Round 1 of 2"); shot("01_facts")
            wait_for("Round 2 of 2"); shot("02_round1")
            wait_for("Options card"); shot("03_options")
            post("accountant.desk", "approve B"); wait_for("needs the verified **Owner**"); shot("04_impostor")
            post(STAND_IN, "approve B"); wait_for("Draft captured"); shot("05_draft")
            post("accountant.desk", "approve numbers"); wait_for("needs the verified **Accountant**")
            post("accountant", "approve numbers"); wait_for("Accountant approved")
            post(STAND_IN, "approve send"); wait_for("Sent (simulated)"); shot("06_sent")
            post(STAND_IN, "@warden stopall"); wait_for("ROOM FROZEN")
            post(STAND_IN, "@warden resume"); wait_for("Resume refused"); shot("07_frozen")
            post("accountant", "@warden resume"); wait_for("Resumed by the accountant"); shot("08_resumed")
            browser.close()
    finally:
        ROLES.write_text(backup, encoding="utf-8")
        mmctl("user", "deactivate", STAND_IN)
        for f in (ROOT / "outbox").glob("*.md"):
            shutil.copy(f, OUT / f.name)
        print("roles restored, stand-in deactivated")


if __name__ == "__main__":
    main()
