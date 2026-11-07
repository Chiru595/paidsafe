"""Capture real demo footage from the live #client-megamart room.

1. Drives a full run through Switch: debate on INV-1042, impostor, approvals, send, freeze + two-key resume,
   the Accountant recording the outcome, then a second debate on INV-1058 that starts from memory (F7).
2. Screenshots each key message by Mattermost permalink (scrolled to and highlighted).

The Owner lines come from a stand-in account (display name "Owner") mapped as owner in config/roles.json
only during the run; the real mapping is restored afterwards. Every message goes through Switch.

    python demo/video/capture.py <out_dir>                 # drive + shoot
    python demo/video/capture.py <out_dir> --from-history  # shoot only
"""
from __future__ import annotations

import json
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
DSF = 1.75  # pixel density of the screenshots (sharper text in the 1440p video)


def mmctl(*args):
    subprocess.run(["docker", "exec", MM, "mmctl", "--local", *args], capture_output=True, text=True)


def latest(n=14) -> list[str]:
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


def drive() -> None:
    backup = ROLES.read_text(encoding="utf-8")
    mmctl("user", "activate", STAND_IN)
    tok, me = call("POST", "/users/login", {"login_id": STAND_IN, "password": PW})
    call("PUT", f"/users/{me['id']}/patch", {"first_name": "Owner", "last_name": ""}, token=tok)
    roles = json.loads(backup)
    roles["owner"] = STAND_IN_ID
    ROLES.write_text(json.dumps(roles, indent=2), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "demo" / "reset.py")], check=True)
    try:
        for _ in range(4):  # Switch can drop the first message from a re-activated user
            post(STAND_IN, "@warden whoami")
            try:
                wait_for("(owner)", timeout=25)
                break
            except TimeoutError:
                print("warm-up not delivered, retrying", flush=True)
        # Part 1 + 2: decide and protect
        step(STAND_IN, "@ledger MegaMart invoice INV-1042 is late. Chase or wait?", "INV-1042 is late. **Chase", 60)
        wait_for("Options card", 300)
        step("accountant.desk", "approve B", "needs the verified **Owner**")
        step(STAND_IN, "approve B", "please draft", 40)
        wait_for("Draft captured", 180)
        step("accountant.desk", "approve numbers", "needs the verified **Accountant**")
        step("accountant", "approve numbers", "Accountant approved")
        step(STAND_IN, "approve send", "Sent (simulated)")
        step(STAND_IN, "@warden stopall", "ROOM FROZEN")
        step(STAND_IN, "@warden resume", "Resume refused")
        step("accountant", "@warden resume", "by the accountant. The room was frozen")
        # Part 3: learn
        step("accountant", "@warden outcome paid 12", "Outcome recorded")
        step(STAND_IN, "@ledger MegaMart is late again on INV-1058. Chase or wait?", "INV-1058 is late. **Chase", 60)
        wait_for("Worked before", 300)
        time.sleep(5)
    finally:
        ROLES.write_text(backup, encoding="utf-8")
        mmctl("user", "deactivate", STAND_IN)
        print("roles restored, stand-in deactivated", flush=True)


def open_channel(page) -> None:
    page.goto(f"{mm_url()}/{TEAM}/channels/{CHANNEL}")
    page.wait_for_timeout(3000)
    if page.get_by_text("View in Browser").count():
        page.get_by_text("View in Browser", exact=True).first.click(force=True)
        page.wait_for_timeout(3000)
    page.wait_for_selector("#post-list, .post-list__content, #postListContent", timeout=20000)
    page.wait_for_timeout(2000)


def shoot() -> None:
    from playwright.sync_api import sync_playwright
    tok, _ = call("POST", "/users/login", {"login_id": "accountant", "password": PW})
    _, ch = call("GET", f"/teams/name/{TEAM}/channels/name/{CHANNEL}", token=tok)
    _, posts = call("GET", f"/channels/{ch['id']}/posts?per_page=120", token=tok)
    ordered = [posts["posts"][i] for i in reversed(posts["order"])]  # oldest first
    starts = [i for i, p in enumerate(ordered) if p["message"].startswith("### 📒 Ledger fact cards")]
    run_a, run_c = ordered[starts[-2]:starts[-1]], ordered[starts[-1]:]
    first = lambda run, marker: next(p for p in run if marker in p["message"])  # noqa: E731
    flagged = next((p for p in run_a if p["message"].startswith("❌ **Fact-check")), None)
    shots = [
        ("01_facts", run_a[0]),
        ("02_debate", flagged or first(run_a, "Fact-check (")),
        ("03_options", first(run_a, "Options card")),
        ("04_impostor", first(run_a, "needs the verified **Owner**")),
        ("05_draft", first(run_a, "Draft captured")),
        ("06_sent", first(run_a, "Sent (simulated)")),
        ("07_frozen", first(run_a, "Resume refused")),
        ("08_resumed", first(run_a, "by the accountant. The room was frozen")),
        ("09_outcome", first(run_a, "Outcome recorded")),
        ("10_memory_facts", run_c[0]),
        ("11_memory_options", first(run_c, "Worked before")),
    ]
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        ctx = b.new_context(viewport={"width": 1536, "height": 1100}, device_scale_factor=DSF)
        host = mm_url().split("//")[1].split(":")[0]
        ctx.add_cookies([{"name": "MMAUTHTOKEN", "value": tok, "domain": host, "path": "/"},
                         {"name": "MMUSERID", "value": call("GET", "/users/me", token=tok)[1]["id"],
                          "domain": host, "path": "/"}])
        page = ctx.new_page()
        open_channel(page)
        for name, p in shots:
            page.goto(f"{mm_url()}/{TEAM}/pl/{p['id']}")
            page.wait_for_timeout(4500)
            page.screenshot(path=str(OUT / f"{name}.png"))
            print("shot", name, p["message"][:70].replace("\n", " "), flush=True)
        b.close()


if __name__ == "__main__":
    if "--from-history" not in sys.argv:
        drive()
    shoot()
