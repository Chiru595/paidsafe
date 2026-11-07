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


def step(user: str, text: str, marker: str, timeout: int = 30) -> None:
    """Post and wait for the room's answer; Switch occasionally drops a message, so retry once."""
    for _ in range(2):
        post(user, text)
        try:
            wait_for(marker, timeout)
            return
        except TimeoutError:
            print(f"no answer to {text!r}, retrying", flush=True)
    raise TimeoutError(marker)


def open_channel(page) -> None:
    page.goto(f"{mm_url()}/{TEAM}/channels/{CHANNEL}")
    page.wait_for_timeout(3000)
    if page.get_by_text("View in Browser").count():
        page.get_by_text("View in Browser", exact=True).first.click(force=True)
        page.wait_for_timeout(3000)
    if page.locator("#input_loginId").count():
        page.fill("#input_loginId", "accountant")
        page.fill("#input_password-input", PW)
        page.keyboard.press("Enter")
        page.wait_for_timeout(4000)
        page.goto(f"{mm_url()}/{TEAM}/channels/{CHANNEL}")
        page.wait_for_timeout(4000)
    page.wait_for_selector("#post-list, .post-list__content, #postListContent", timeout=20000)
    page.wait_for_timeout(2000)


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
            open_channel(page)

            def shot(name: str) -> None:
                page.wait_for_timeout(2500)
                page.screenshot(path=str(OUT / f"{name}.png"))
                print("shot", name, flush=True)

            if "--check" in sys.argv:
                shot("check"); return
            step(STAND_IN, "@ledger MegaMart invoice INV-1042 is late. Chase or wait?", "Round 1 of 2", 60)
            shot("01_facts")
            wait_for("Round 2 of 2"); shot("02_round1")
            wait_for("Options card"); shot("03_options")
            step("accountant.desk", "approve B", "needs the verified **Owner**"); shot("04_impostor")
            step(STAND_IN, "approve B", "please draft", 40)
            wait_for("Draft"); shot("05_draft")
            step("accountant.desk", "approve numbers", "needs the verified **Accountant**")
            step("accountant", "approve numbers", "Accountant approved")
            step(STAND_IN, "approve send", "Sent (simulated)"); shot("06_sent")
            step(STAND_IN, "@warden stopall", "ROOM FROZEN")
            step(STAND_IN, "@warden resume", "Resume refused"); shot("07_frozen")
            step("accountant", "@warden resume", "by the accountant. The room was frozen"); shot("08_resumed")
            browser.close()
    finally:
        ROLES.write_text(backup, encoding="utf-8")
        mmctl("user", "deactivate", STAND_IN)
        for f in (ROOT / "outbox").glob("*.md"):
            shutil.copy(f, OUT / f.name)
        print("roles restored, stand-in deactivated")


if __name__ == "__main__" and "--from-history" not in sys.argv:
    main()


# ---- re-shoot from history: open each key message by permalink (Mattermost scrolls to it and highlights it)
SHOTS = [("01_facts", "Ledger fact cards"), ("02_round1", "Fact-check ("), ("03_options", "Options card"),
         ("04_impostor", "needs the verified **Owner**"), ("05_draft", "Draft captured"),
         ("06_sent", "Sent (simulated)"), ("07_frozen", "Resume refused"), ("08_resumed", "**Resumed** by")]


def shoot_from_history(out: Path) -> None:
    from playwright.sync_api import sync_playwright
    tok, _ = call("POST", "/users/login", {"login_id": "accountant", "password": PW})
    _, ch = call("GET", f"/teams/name/{TEAM}/channels/name/{CHANNEL}", token=tok)
    _, posts = call("GET", f"/channels/{ch['id']}/posts?per_page=80", token=tok)
    ordered = [posts["posts"][i] for i in reversed(posts["order"])]  # oldest first
    start = max(i for i, p in enumerate(ordered) if "Ledger fact cards" in p["message"])
    run = ordered[start:]
    flagged = next((p for p in run if p["message"].startswith("❌ **Fact-check")), None)
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        ctx = b.new_context(viewport={"width": 1536, "height": 1100}, device_scale_factor=1.25)
        host = mm_url().split("//")[1].split(":")[0]
        ctx.add_cookies([{"name": "MMAUTHTOKEN", "value": tok, "domain": host, "path": "/"},
                         {"name": "MMUSERID", "value": call("GET", "/users/me", token=tok)[1]["id"],
                          "domain": host, "path": "/"}])
        page = ctx.new_page()
        open_channel(page)
        for name, marker in SHOTS:
            post_ = flagged if (name == "02_round1" and flagged) else next(p for p in run if marker in p["message"])
            page.goto(f"{mm_url()}/{TEAM}/pl/{post_['id']}")
            page.wait_for_timeout(4500)
            page.screenshot(path=str(out / f"{name}.png"))
            print("shot", name, post_["message"][:60].replace("\n", " "), flush=True)
        b.close()


if __name__ == "__main__" and "--from-history" in sys.argv:
    shoot_from_history(OUT)
