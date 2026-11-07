# Demo video script (about 2 minutes)

Record the Mattermost window (`http://localhost:<port>`, port in `%APPDATA%\switchdash\local-switch-server\ports.json`).
Use three browser profiles (or one normal + two private windows), signed in as `user` (Owner),
`accountant` and `accountant.desk` (the impostor).

**Before recording**
```powershell
python demo/reset.py
python -m agents.run          # leave running in its own terminal
```
Do one throwaway `@warden whoami` from each account first, so Switch has created their actors
(the first message from a new user can be dropped).

| Time | Screen | Say |
|---|---|---|
| 0:00–0:15 | README "The problem" table | "Razorpay's Fix My Itch scores 'SMEs can't get favorable payment terms from large buyers' at 82.8, its top B2B itch. 59% of US small businesses wait 30+ days on invoices, and a wire request was deepfaked in Slack. PaidSafe is a Switch room where people and agents handle this together." |
| 0:15–0:25 | Owner types `@ledger MegaMart invoice INV-1042 is late. Chase or wait?` | "The Ledger has no LLM. It computes the facts: 32 days overdue, ₹7,130 statutory interest at three times the RBI Bank Rate." |
| 0:25–0:55 | Round 1, fact-checks, Round 2 | "Relationship runs on Claude Opus, Cash on Claude Sonnet. Every number must cite a fact card. Here the Ledger flags a number that isn't on the card it cites." (point at a ❌) |
| 0:55–1:05 | Options card | "Four options with their cash impact." |
| 1:05–1:15 | Impostor types `approve B` → ⛔ | "Same display name, 'Accountant'. Switch stamps a sender id on every message, and the Warden only trusts that." |
| 1:15–1:35 | Owner `approve B` → Cash drafts → Accountant `approve numbers` → Owner `approve send` → 📤 | "Two verified approvals on this exact draft hash, then a simulated send. The playbook is saved as a Switch room document only the Warden can edit." |
| 1:35–1:50 | Owner `@warden stopall` → Owner `@warden resume` (refused) → Accountant `@warden resume` | "Kill switch. It's enforced in the tools, not the prompt, and resuming needs the other person's key." |
| 1:50–2:00 | Terminal: `python -m pytest -q` (53 passed) + README feature table | "Different models, deterministic checks, every rupee approved by a verified human. That's PaidSafe on Switch." |
