# PaidSafe — session handoff (read this first)

Full product brief: `PAIDSAFE_BRIEF.md` (the "PaidSafe — Build Brief"). This file holds the decisions and
current status, and it overrides the brief where they differ.

## Deadline
Submissions close **Sat Nov 7, 2026, 11:59 PM IST**. Planning started at 18:18 IST that day, so there are
about 5 hours left. Scope everything to that.

## Status (as of ~18:50 IST, Nov 7)
- Planning was done on an office Mac, where Switch Console couldn't be installed. **All building now happens
  on the personal Windows laptop.** No code was written on the office Mac. Keep it that way: this is a personal
  project, so use the personal GitHub account (Chiru595) only.

## Status (as of ~20:45 IST, Nov 7)
- Switch Console installed ("Only for me"), local server running in **native** runtime (switch-core v0.31.0).
  Only Mattermost runs in Docker; switch-core runs in a console window — **minimize it, never close it**.
- Ports change on every restart. Read them from `%APPDATA%\switchdash\local-switch-server\ports.json`
  (gateway / api / mattermost / postgres). `GET <api>/health` → 200 when the core is up.
- Mattermost team: `switch`. Admin commands work via
  `docker exec switchdash-local-mattermost-mattermost-1 mmctl --local ...` (local mode is enabled).
- Humans (Mattermost user ids — the Warden checks these, never display names):
  - owner = `user` (`txud4jrxfprsmds17xu5979o5r`), linked to Switch
  - accountant = `accountant` (`rg31x5b1ppdy8xd35p3d3jf4io`), display name "Accountant"
  - impostor = `accountant.desk` (`awx17pqenjydtk9m5urymnwzpc`), display name "Accountant"
  - Demo password for both accountant accounts: `PaidSafe-Demo-2026!` (local-only demo server)
- Switch auto-creates a room for each public Mattermost channel (bridge log: "Auto-created channel_public room").
- Docs say the agent protocol's SSE transport is deprecated: custom agents use WebSocket
  `/agents/{id}/connection/ws`; register via `POST /agents` with a `registration` API key.
- **Room creation gotcha:** a Mattermost channel becomes a Switch room only when an agent's *bot account*
  is added to it. `!invite-agent` typed in a channel that isn't a room yet gets no reply (the bridge isn't
  listening there). Fix: `mmctl --local channel users add switch:<channel> <agent-name>` (or Mattermost
  "Add members" → the agent's bot).
- Room `client-megamart` = `sw_room_b7970d13a1484f7d83d161ee4d19c204`. Agent `relationship`
  (Claude Code, id `bbdbff99-16e2-46e0-acf3-638af41d043c`, workspace `..\paidsafe-agents\relationship`,
  kept outside the repo so it doesn't load this CLAUDE.md).
- Next: go/no-go — `@relationship` replies in `#client-megamart`.

## Cut scope for tonight (decided)
KEEP:
- One room, `#client-megamart`.
- Two humans: `owner` and `accountant`, both linked and confirmed in Switch. Plus an impostor account,
  `accountant.desk`, with display name "Accountant".
- Ledger and Warden as custom Python agents with **no LLM**.
- Two LLM debaters: Relationship on Claude Code, and Cash on Codex. If Codex login takes more than 10 minutes,
  run Cash as a second Claude Code agent on a different Claude model, and say so honestly in the README.
- The loop: fact cards (F1..F6), then Round 1 with `[F#]` citations, then the fact-check flags ❌, then
  Round 2, then the options card, then the Owner sends `approve B`, then the Accountant approves the numbers,
  then the Owner approves sending, then a simulated send to `outbox/`.
- `!stopall`, two-key `!resume`, the circuit breaker, and impostor approvals rejected by **Switch sender id**
  (never by display name).
- Every side-effecting script checks the freeze flag and the approvals itself, so it's enforced in the tools,
  not the prompts.
- pytest for India interest, fact-check, freeze, two-key and impostor.

CUT: PayGuard and the supplier room, the OpenCode agent, the Desk and linked rooms, the UK/EU packs, Telegram,
cross-review. Playbook memory stays only if it's a single file append.

## Timeline (IST, hard stops)
- by 19:45: Switch running on Windows, owner and accountant linked, **one agent replying in a room** (go/no-go)
- meanwhile: Python core (data, `tools/interest.py`, `tools/factcheck.py`, warden core, tests), pushed to GitHub
- 19:45–21:15: Ledger and Warden on the agent protocol, debate working
- 21:15–22:00: approvals, kill switch, impostor, template YAML
- **22:00 FEATURE FREEZE**
- 22:00–23:15: README (Switch-feature table, Mermaid diagram, setup, gotchas, disclosure), 2-minute video
- 23:15–23:40: submit

**Fallback:** if custom agents on the agent protocol aren't working by 20:45, have the LLM agents call the
Ledger and Warden scripts as tools. The freeze and approval enforcement stays in the scripts.

## Windows notes
- Docker Desktop with the WSL2 backend must be running before you start a server.
- Switch Console v0.40.1 for Windows: `switch-console-x64.exe` (or `.msi`) from
  https://github.com/sandbox-quantum/switch/releases/latest. The Windows build is early access.
- Known Windows bug in 0.40.1: the template form shows providers as "Not supported here". **Create agents by
  hand (Your Agents → +) and use the template only for rooms.**
- The Mattermost port changes on every server restart. Read it from `docker ps`.

## Verified Switch docs (docs.switchagents.ai)
Index: https://docs.switchagents.ai/llms.txt
- Install Console: /switch-rooms/getting-started/install-switch-console.md
- Add a server: /switch-rooms/getting-started/add-a-server.md
  - Console → Add a server → **Run a server on this computer**. It starts Mattermost and the Gateway on free
    ports, creates an admin account and signs Console in. No URL or secret is needed.
  - Link chat: server **Home** → **Messaging apps** → **Link** (Mattermost) → search your name → **This is me**.
    If Mattermost isn't signed in, use the row's **Sign-in details…**.
  - Quitting Console leaves the server running, but it does **not** come back after a reboot.
- Add a custom agent: /switch-rooms/getting-started/add-a-second-agent.md
- Agent protocol: /switch-rooms/internals/agent-protocol.md
- Room templates: /switch-rooms/administer/room-templates.md
- Payments room (worked example, read first): /switch-rooms/building/payments-room.md
- Mattermost: /switch-rooms/deploy/messaging-apps/mattermost.md

Docs MCP: `claude mcp add switch-docs --transport http https://docs.switchagents.ai/mcp`.
Verify every endpoint, op name and config key against the docs. Never guess.
