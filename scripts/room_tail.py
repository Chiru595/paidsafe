"""Print the last N messages of the demo channel (read as the accountant). Debug/rehearsal helper."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.mm_post import CHANNEL, TEAM, call  # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
width = int(sys.argv[2]) if len(sys.argv) > 2 else 700
tok, _ = call("POST", "/users/login", {"login_id": "accountant", "password": "PaidSafe-Demo-2026!"})
_, ch = call("GET", f"/teams/name/{TEAM}/channels/name/{CHANNEL}", token=tok)
_, posts = call("GET", f"/channels/{ch['id']}/posts?per_page={n}", token=tok)
users = {}
for pid in reversed(posts["order"]):
    p = posts["posts"][pid]
    uid = p["user_id"]
    if uid not in users:
        users[uid] = call("GET", f"/users/{uid}", token=tok)[1].get("username", uid)
    print(f"----- {users[uid]}\n{p['message'][:width]}")
