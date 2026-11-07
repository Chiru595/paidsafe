# PaidSafe — Build Brief

> **Get paid on time. Never pay a fraudster.**
> A Switch room where a small business's people and AI agents protect its cash flow in both directions: chasing late payments without losing the client, and stopping fake payment requests before money leaves.

This brief is for a Claude Code session that will build the project. Read all of it before writing code. Where it says **VERIFY**, check the Switch docs (MCP command in §6) instead of guessing. Never invent Switch endpoints, operation names or config keys. If something can't be verified, stop and ask the user.

---

## 0. Hard constraints (read first)

- **Hackathon:** Flip the Switch (WeMakeDevs × DevTools Academy × Switch AI by SandboxAQ). Online, Nov 4–7, 2026.
- **Deadline:** submissions close **Nov 7, 2026, 11:59 PM IST**. Scope everything to a working MVP first. Polish comes after.
- **Track:** Track 01, Best Business Workflow ($2,000).
- **Builder:** solo, Chiru (GitHub: Chiru595). He plays every human role himself using separate Mattermost accounts.
- **Synthetic data only.** No real client, employer or third-party data. The rules forbid third-party confidential information.
- **Not legal or financial advice.** All legal figures come from cited rule packs, and the UI says so.
- **Payments are simulated.** Nothing touches a real bank or payment API.
- **Build order:** get one end-to-end flow working before adding anything (see §12).

---

## 1. Hackathon rules that shape the build

- **Core requirement:** a workflow in team chat where at least one AI agent and one person get a real task done together, connected through Switch.
- **Switch must be central.** The project should stop working without it, and the README must show how Switch is used.
- **What may predate the hackathon:** existing agents, libraries and templates are fine. The Switch setup and the agents' workflow must be built during the hackathon. Add a "Build and AI disclosure" section to the README listing anything made before Nov 4.
- **AI tools are allowed**, but Chiru must understand and be able to explain everything submitted.
- **Submission needs:**
  - A public GitHub repo with visible commit history. Commit often.
  - A README explaining which agents are connected, how the channel is set up, and how to run it.
  - A short demo video, about 2 minutes.
- **Judging criteria:**
  1. **Use of Switch:** is it central?
  2. **Technical execution:** does it run, and can someone clone and reproduce it?
  3. **Creativity and impact:** is it a fresh idea solving a real team problem?
  4. **Presentation:** do the video and README make Switch's role clear?
- **Optional extras:**
  - Best Blog side track (AirPods 5): a dev.to post.
  - #HowISwitch social post: the top 5 win Logitech keyboards.
  - Star the Switch repo: chance at a Keychron keyboard.
- **Eligibility:** 18+, a single real identity, no bots or automated entries. Winners may need ID verification and handle their own taxes. Chiru should check that his employment contract permits prize acceptance.

---

## 2. The problem, and why it's real

### 2.1 The problem in plain words

Small businesses lose money in two directions:

1. **Money in:** big clients pay late, and the owner is afraid to push hard in case they lose the client.
2. **Money out:** fraudsters impersonate a boss or supplier ("our bank details changed", "approve this urgently") and the business pays the wrong account.

Both are judgment calls made under pressure, by one or two people, inside chat. PaidSafe puts AI agents and those people in the same room. The agents debate, check facts with real tools, and refuse to move money unless a verified human approves.

### 2.2 Defensibility from Razorpay's Fix My Itch (primary evidence)

**Fix My Itch** (razorpay.com/m/fix-my-itch/) is Razorpay's public, AI-curated database of real problems Indians want solved.

- **Scale:** 10,000+ verified problems drawn from about 50,000 inputs. Sources were Indian forums (r/india, r/bangalore, r/developersIndia), X discussions, and on-ground interviews.
- **Recognition:** launched on National Startup Day, Jan 16, 2026, and won a Shorty Award in the Platform category.

PaidSafe maps to several of its listed problems ("itch score" in brackets):

| Fix My Itch problem | Score | PaidSafe part |
|---|---|---|
| Why can't SMEs negotiate favorable payment terms with large buyers? | **82.8** (highest seen) | Money in: Chase-or-Wait debate |
| Why can't businesses verify new suppliers before purchasing? | 76 | Money out: PayGuard supplier checks |
| Why do freelancers ghost projects after partial payments without accountability systems? | 76 | Money in: payment accountability |
| Why do micro-SMEs waste 10+ hours weekly on invoice management? | 67.5 | The Desk room cuts the manual chasing |

**Pitch line:** "We didn't invent this problem. Razorpay surveyed India and SMEs ranked it at the top."

### 2.3 Global evidence (it isn't only Indian)

- **US:** the Intuit QuickBooks 2026 Late Payments Report found **59%** of small businesses have invoices overdue 30+ days, up from 47% the year before. Those businesses are owed **$17.7K** on average.
- **Global:** Bookipi's 2026 survey covered small business owners in **57 countries**. More than half had invoices go entirely unpaid.
- **Freelancers:** the Jobbers.io 2026 report (22,847 transactions, 62 countries) found **65%** wait over 30 days to be paid. 40–45% have missed personal bills because of it.
- **Fraud:** the FBI's 2025 internet crime report logged **24,768** business email compromise complaints and **$3.05B** in losses, up from $2.77B in 2024. In an AFP survey, **70%** of finance professionals named it the top fraud avenue. One finance team had a **wire payment request deepfaked via Slack**, so chat is already an attack surface.
- **Why Indian suppliers don't claim what they're owed:** commentators note many MSMEs don't demand statutory interest from large customers because they fear losing the business. That fear is the human problem the debate addresses.

### 2.4 Investor and research backing

- **YC's Fall 2026 Requests for Startups:**
  - It asks for "Multiplayer AI": shared, live agent sessions a whole team can join, redirect and hand off. That is Switch's thesis.
  - BigIdeasDB scored YC's list against 1M+ complaints, 17,000+ funded companies and 30,000+ Stripe companies. **Compliance infrastructure** and the **trust layer** (verifying a real human is on the other end) were among the four best-evidenced requests.
- **Multi-agent debate research:**
  - Du et al., *Improving Factuality and Reasoning in Language Models through Multiagent Debate* (ICML 2024): debating models converge on more accurate answers than a single model, at higher cost.
  - Hegazy 2024, *Diversity of Thought Elicits Stronger Reasoning in Multi-Agent Debate*: debate works better with **different models**. This is why every agent runs on a different model.

### 2.5 Honest weaknesses (say them before a judge does)

- **Not the builder's own field.** Domain expertise is encoded as cited rule packs, not claimed experience.
- **Payments are simulated**, and there's no real bank or accounting integration.
- **Not legal advice.** Legal figures come from public sources and can change.
- **Credit-control and vendor-verification SaaS exists.** That proves demand. What's new here is the multiplayer room: different-model debate, verified-human approvals, and a kill switch.

---

## 3. What makes it different

| Existing thing | What it does | PaidSafe difference |
|---|---|---|
| Hackathon entries: Refund Court, Refund Desk, Revenue Desk, Support-to-Ship, Release Room, Airlock, LabRoom, Shield, IdeaFlow, Glass Agency | Refunds (money going *out* to customers), dev pipelines, data quality, planning | Small-business cash flow in **both** directions. No finance-in/finance-out room was found among the entries. |
| Negotiation simulators (dozens of GitHub repos, incl. an Infosys Springboard internship project) | AI-vs-AI buyer/seller role-play in a web app | Real decisions on real (synthetic) ledgers, with legal rules, verified human approval, and memory |
| Karpathy's LLM Council | Single-user web app where models rank each other and a "chairman" model answers | Multiplayer and in chat: humans sit in the room, debaters must cite ledger facts, and a human decides |
| TradingAgents (~95K stars) | Bull and bear researchers debate before a trade | The same debate pattern, applied to a small business's cash-flow dilemma |
| Credit-control and vendor-verification SaaS | Single-user dashboards | A shared room, cross-model debate, a two-key kill switch, and per-client memory |

---

## 4. The product

### 4.1 Rooms (Switch linked rooms)

- **`#paidsafe-desk`:** the hub. Summaries of every client and supplier, decisions, and the kill-switch status.
- **`#client-<name>`:** one room per late-paying client, created from a template. Holds that client's invoices, debates, decisions and playbook.
- **`#supplier-<name>`:** one room per supplier, holding payment requests, checks, holds and trust history.

For the MVP, use one client room and one supplier room. More can be created from the template.

### 4.2 Humans (two roles, both played by Chiru)

| Role | Mattermost account | Can do |
|---|---|---|
| **Owner** | `owner` | Asks the debate question, picks the strategy, approves outgoing client messages, requests supplier payments, `!stopall`, `!resume` (only if the Accountant stopped it) |
| **Accountant** | `accountant` | Approves numbers and ledger corrections, approves supplier payments, `!stopall`, `!resume` (only if the Owner stopped it) |
| Impostor (demo only) | `accountant.desk` with display name "Accountant" | Tries to approve a payment. Must be rejected because Switch's sender id doesn't match the linked Accountant identity. |

Both real accounts must be **linked** to Switch identities (Console → Home → Messaging apps → Mattermost → Link → "This is me"). Identity links must be **confirmed**, or approvals won't bind. **VERIFY** the exact steps in the docs.

### 4.3 Agents (each on a different model and tool)

| Agent | Runs on | Purpose | Instructions accepted from |
|---|---|---|---|
| **Ledger** | Custom Python agent via the Switch agent protocol. **No LLM.** | Holds the facts: invoices, due dates, days late, statutory interest, fixed compensation, cash runway in weeks, client history. Posts numbered **fact cards** (F1, F2…). Calculates all money with code. | Accountant (corrections), agents (read-only queries) |
| **Cash agent** | **Codex** (OpenAI model) | Argues for getting paid now: protect cash flow, enforce rights, escalate | Owner, other agents |
| **Relationship agent** | **Claude Code** (Claude model) | Argues for keeping the client: relationship value, future orders, softer options | Owner, other agents |
| **PayGuard Checker** | **OpenCode** (a third model, e.g. a free OpenCode model) | Runs deterministic payment checks via scripts and explains the result in plain language | Owner, Accountant |
| **Warden** | Custom Python agent. **No LLM.** | Kill switch, circuit breaker, approval enforcement, 48-hour holds, audit log | Owner and Accountant only, checked by verified sender id |

The Warden and Ledger have no LLM on purpose. They can't be talked out of a rule or make up a number.

**Minimum viable cast:** 2 humans, plus Ledger, Cash, Relationship and Warden. Add the PayGuard Checker second. In an emergency, the Warden can run the PayGuard checks itself with no LLM explanation.

### 4.4 Switch-only features to use (all of them, and the README must point to each)

1. **Agents from different tools in one chat app:** Codex, Claude Code, OpenCode and custom Python agents in the same Mattermost rooms.
2. **Humans watching and stepping in:** both humans see every debate turn and can redirect or stop it.
3. **Who-can-talk rules (addressing policies):** for example, only the Owner can start a debate, and only the Accountant can correct the Ledger. **VERIFY** the policy names in the docs (`anyone` and `owner-agents` exist in templates). Note that new agents are owner-only by default.
4. **Verified sender identity:** every approval, `!stopall` and `!resume` is checked against the sender id Switch attaches to the message, never the display name.
5. **Shared room memory and room documents:** each room's history, decisions and playbook live in the room.
6. **Linked rooms:** client and supplier rooms feed the Desk.
7. **Templates:** a YAML template creates the agents, rooms, instructions and kickoff in one import (`switch/paidsafe.template.yaml`). Judges can reproduce it in one step.
8. **Telegram (stretch):** the Owner approves from a phone. Not for the MVP.

---

## 5. Workflows

### 5.1 Money in: the Chase-or-Wait debate

**Trigger:** the Owner posts in `#client-megamart`: `@ledger @cash @relationship MegaMart invoice INV-1042 is late. Chase or wait?`

1. **Ledger posts fact cards**, for example:
   - F1: invoice ₹4,80,000, accepted on a date, 62 days ago
   - F2: due date under the written agreement, so N days overdue
   - F3: statutory interest to date, with the rate source and as-of date
   - F4: MegaMart's share of revenue, how often they've paid late before
   - F5: cash runway, X weeks at current burn
   - F6: the buyer's tax exposure under India's Section 43B(h)
2. **Round 1 (independent positions):** Cash and Relationship each post a recommendation without reading the other's. **Every claim must cite a fact id like [F3].**
3. **Fact check (deterministic):** the Ledger scans both posts. Any number or claim without a valid fact id, or contradicting a fact card, is flagged ❌ in the room. This is the "agents check facts with real tools, not guessing" moment.
4. **Round 2 (rebuttal):** each agent answers the other's argument, using fact ids only.
5. **Options card:** the Ledger (template-based, no LLM) lists 2–4 options pulled from both sides, each with its cash impact. For example:
   - (A) friendly nudge plus an early-payment discount
   - (B) firm reminder citing the statutory interest owed
   - (C) formal notice citing the law, with escalation to the state MSME Facilitation Council or MSME Samadhaan portal
   - (D) wait two weeks and finance the gap (e.g. invoice discounting via TReDS; **VERIFY** before mentioning)
6. **The Owner picks** an option, e.g. `approve B`.
7. **Drafting and cross-review:** the agent whose side won drafts the client message. The other agent, on a different model, reviews it. The **Accountant approves the numbers**, then the **Owner approves sending**. The Warden only lets "send" happen after both verified approvals. Sending is simulated: the message is written to `outbox/` and posted in the room.
8. **Memory:** the Ledger appends to `#client-megamart`'s playbook: the decision, the reason, the outcome field (filled in later), and the client's pay pattern and typical excuses. The next debate for this client reads the playbook first.

**Debate caps:** at most 2 rounds. A 3rd round needs an explicit Owner request, or the circuit breaker trips.

### 5.2 Money out: PayGuard

**Trigger:** the Owner posts a supplier invoice or payment request in `#supplier-shree-polymers`.

**Checks** (deterministic Python scripts, called by the Checker or Warden):

1. **Bank details match the supplier master record** (`data/suppliers.json`).
2. **Duplicate invoice detection:** same supplier and amount, or the same invoice number.
3. **Amount anomaly:** the amount is far outside this supplier's history (simple z-score or percentage threshold).
4. **Bank detail change:**
   - Puts any new account on a **48-hour hold**.
   - Opens a task to verify by calling the supplier's **known number from the master record**, never a number from the request.
   - Requires the Accountant to confirm the call before the hold lifts. For the demo, the hold can be time-warped with an admin flag that's clearly labelled.
5. **Urgency slowdown:** messages with urgency words ("urgent", "today", "before EOD") get extra review and are never fast-tracked.
6. **Approver identity:** the approval must come from the verified Accountant sender id. Display names are ignored.

**Outcome:** all checks pass and the Accountant approves, so the Warden simulates the payment and writes it to `payments.log`. Otherwise the payment is held or rejected, with reasons posted in the room.

**Memory:** supplier trust history plus a fraud-pattern list. Lookalike supplier names (simple string similarity), new accounts and urgency patterns are flagged instantly next time.

### 5.3 Kill switch (the Warden)

- **Manual stop:** `!stopall` from the Owner or Accountant, verified by sender id.
  1. The room is set to **FROZEN** in `state.db`.
  2. Every agent is interrupted. Use Switch's per-agent `!interrupt` (it exists for CLI agent providers) or the relevant Switch operation. **VERIFY** which a custom agent may trigger.
  3. Freeze notices and an audit entry are posted in every linked room.
- **Infrastructure-level enforcement** (this is what makes the kill switch real):
  - **Every** side-effecting script (`send_client_message`, `release_payment`, `update_ledger`) checks the freeze flag first, and refuses when frozen.
  - This works even if an agent ignores instructions, and even if Switch has no room-wide stop.
- **Circuit breaker (automatic freeze):**
  - more than **12 agent messages** in a room without a human message, or
  - a debate passing its round cap, or
  - more than **3 rejected approval attempts** within 10 minutes (an attack in progress).
- **Resuming:** `!resume` must come from the **other** human (two-key). The Warden posts what was frozen and for how long.
- **Audit log:** `audit.log` records every stop, resume, approval, rejection and trip, with timestamp, verified sender id and reason.

---

## 6. Switch setup facts (gathered from docs and other builders; **VERIFY** each)

### Installing and running

- **Switch Console** from https://github.com/sandbox-quantum/switch/releases/latest.
  - macOS is primary. Windows and Linux builds are early access.
  - Requires **Docker**.
  - In Console: Add a server → **Run a server on this computer**. The first start downloads several GB and provides a **bundled Mattermost**.
- **Docs over MCP:**
  ```
  claude mcp add switch-docs --transport http https://docs.switchagents.ai/mcp
  ```
  Then ask it "How do I get started with Switch?" and use it to verify every API detail.
- **Useful docs** (from the hackathon resources page): Quickstart, Create a room, Add a custom agent, The Switch framework (rooms, agents, roles), Build a payments room (a full worked example; read this first), Share context, The agent protocol, The collaboration bridge.
- **The agent protocol:** Server-Sent Events in, HTTP out. Custom (non-CLI) agents join a room through it.

### API details other builders used (from blog posts, not official; **VERIFY**)

- Operations: `POST /agents/{id}/ops/{name}` with arguments in the body, plus an `X-Switch-Connection-Id` header when the op needs a connection.
- Posting to a room: `POST /agents/{id}/message` with `{room_id, content}`. Markdown renders in Mattermost.
- `create_room` on the default bridge creates the Mattermost channel.
- Custom agents registered with a **registration**-type API key created in the Gateway (API Keys page). One builder warned **not** to use the deployment bootstrap key: those agents belong to a separate account, so owner-only approval won't bind to you.
- With the standalone Docker Compose route: port 8000 = API and agent bridge, 3000 = Gateway, 8065 = Mattermost, and `SWITCH_VERSION` must be pinned.

### Known gotchas from other builders

- **Link your chat account,** or agents won't answer you.
- **Messages to a busy agent can be dropped.** Send one request per agent at a time, and retry if no reply.
- **Files uploaded through the Mattermost API by a script don't reach agents.** Attach files with the paperclip in chat.
- **The Mattermost port changes on every Console server restart.** Read it from `docker ps`, never hard-code it.
- **Windows (Console 0.40.1):** the template form showed providers as "Not supported here." Workaround: create agents by hand (Your Agents → +) and use a template only for rooms.
- **Room creation is slow** (~15 s each) and can outlast Console's timeout.
- **New agents are owner-only,** and identity links must be confirmed.
- **The bundled Mattermost user joins every channel** the bridge creates.
- **After Console quits,** its agent can show as "live" in the room for about an hour (issue #1114).
- **Agents reply by calling a post_message tool,** so use models that handle tool calls well.
- **Free model tiers run out fast** with several agents talking. Debate caps help.

---

## 7. Rule packs (domain knowledge as cited data)

Store each as `rules/<jurisdiction>.yaml`. Every value needs `source_url` and `as_of`. The Ledger refuses to calculate if a needed rate is older than a configured age, unless the Accountant confirms it. Rates conflict across secondary sources (e.g. UK sources quoted 11.75% and 12.5% at different times), which is exactly why the Ledger stamps source and date on every number.

### `rules/india_msmed.yaml` (primary, for the demo)

- **Applies to:** Udyam-registered micro and small enterprise suppliers. The 43B(h) tax rule doesn't apply to pure traders.
- **Payment deadline (MSMED Act s.15):** the agreed date, capped at **45 days** from acceptance. If there's no written agreement, **15 days**.
- **Interest (s.16):** **compound interest with monthly rests at 3× the RBI Bank Rate**, from the day after the due date, regardless of any contract term.
  - The Bank Rate is fetched or entered with a source. One Aug 2026 source said 5.50%, so 16.5%. **VERIFY** the current figure.
- **s.23:** this interest isn't tax-deductible for the buyer.
- **Income Tax Act s.43B(h)**, in force since FY 2023-24: if the buyer pays an MSE after the deadline, they can only deduct the expense in the year they actually pay. This is the supplier's leverage.
- **Forums:** the state MSME Facilitation Council, and the MSME Samadhaan portal.

### `rules/uk_late_payment.yaml` (shows it's global)

- **Late Payment of Commercial Debts (Interest) Act 1998:** statutory interest at **8% above the Bank of England base rate**, as **simple** interest, automatic for B2B even without a contract clause.
- **Fixed compensation:** **£40** for debts under £1,000, **£70** for £1,000–£9,999.99, **£100** for £10,000+.
- **Note:** the Commercial Payments Bill (60-day cap, non-excludable interest) was still going through Parliament at last check.

### `rules/eu_directive.yaml` (stretch)

- **Directive 2011/7/EU:** the ECB reference rate plus at least **8 points** (for example, Ireland and Spain set 10.40% from 1 Jul 2026), and at least **€40** per late invoice.

**Disclaimer**, shown in the room and README: "Calculations follow the cited public rules for information only. Not legal or financial advice."

---

## 8. Synthetic demo data (`data/`)

- **Company:** Kaveri Packaging Pvt Ltd, a fictional Udyam-registered micro enterprise in Bengaluru.
- **Clients (`clients.json` + `invoices.csv`):**
  - **MegaMart Retail:** a large buyer, about 30% of revenue, a history of paying 20–40 days late. INV-1042 is 62 days since acceptance.
  - **BlueLeaf Foods:** a good payer. Use it as the contrast case.
  - **NorthBridge Supplies Ltd:** a UK client (GBP invoice), to show the UK pack.
- **Suppliers (`suppliers.json`):**
  - **Shree Polymers:** a known account and a known phone number.
  - **"Shree Polymer"** (one letter different): the lookalike impostor.
- **Payment history (`payments_history.csv`):** for the anomaly baseline.
- **Cash (`cash.json`):** balance and weekly burn, for the runway calculation.
- Every name, number and account is fake. Mark the data as **synthetic** in the README.

---

## 9. Suggested repo layout

```
paidsafe/
├── README.md                  # judges read this first (see §11)
├── LICENSE                    # MIT
├── switch/
│   ├── paidsafe.template.yaml # agents + rooms + instructions + kickoff
│   └── rooms-only.template.yaml   # Windows fallback
├── agents/
│   ├── ledger/                # custom Python agent (agent protocol), no LLM
│   ├── warden/                # custom Python agent, no LLM
│   └── instructions/          # cash.md, relationship.md, payguard.md
├── tools/                     # deterministic scripts agents call
│   ├── interest.py            # India compound monthly, UK simple + fixed comp
│   ├── factcheck.py           # validate [F#] citations in debate posts
│   ├── payguard_checks.py     # bank match, duplicate, anomaly, lookalike, urgency
│   ├── send_client_message.py # freeze-checked, approval-checked, writes outbox/
│   └── release_payment.py     # freeze-checked, approval-checked, writes payments.log
├── rules/                     # india_msmed.yaml, uk_late_payment.yaml, eu_directive.yaml
├── data/                      # synthetic data (see §8)
├── state/                     # state.db (sqlite), audit.log, playbooks/
├── tests/                     # pytest: interest math, fact-check, payguard, freeze, two-key
└── demo/                      # demo script, seed/reset script
```

**Tests matter to judges.** The GitLab AI Hackathon 2026 grand prize winner shipped 43 tests, and a judge praised it as feeling like a product. Test at least these:

- India compound interest and UK simple interest plus fixed compensation, with known answers
- Fact-check flags a claim with no source and accepts a cited one
- Every PayGuard check, pass and fail
- Freeze blocks every side-effecting tool
- Two-key resume rejects the same person who stopped
- An impostor display name is rejected

---

## 10. The demo video (about 2 minutes, in Mattermost)

1. **0:00–0:15, the hook.** "59% of small businesses are waiting on late invoices. Business email scams took $3B last year. Razorpay's Fix My Itch ranks SME payment terms as India's top business itch."
2. **0:15–0:55, money in.**
   - The Owner asks "Chase or wait?" about MegaMart.
   - The Ledger posts fact cards.
   - Cash (Codex) and Relationship (Claude) argue.
   - The Ledger flags ❌ on a made-up number.
   - The Options card appears and the Owner picks B.
   - The Relationship agent drafts, Cash reviews.
   - The Accountant approves the numbers, the Owner approves sending.
3. **0:55–1:30, money out.**
   - "Shree Polymer" asks to pay a new account, urgently.
   - PayGuard flags the lookalike name, the new account and the urgency, then puts a 48-hour hold on it.
   - The **impostor account "Accountant"** posts "approved". It's **rejected because the Switch sender id doesn't match.**
4. **1:30–1:45, kill switch.**
   - Agents start looping, and the circuit breaker freezes everything (or the Owner types `!stopall`).
   - The Accountant's `!resume` is accepted, and the Owner's own resume attempt is shown being refused.
5. **1:45–2:00, it gets smarter.**
   - A new MegaMart invoice opens with the playbook loaded.
   - A second lookalike supplier is flagged instantly.
   - End card: "Every agent on a different model. Every rupee approved by a verified human."

---

## 11. README checklist (judges grade this)

- **The problem:** the §2 evidence, with Fix My Itch first.
- **How Switch is used:** a table mapping each of the §4.4 features to where it appears.
- **Architecture:** rooms, agents and models, humans and permissions. Use a Mermaid diagram.
- **Setup from zero:** Console, Docker, link accounts, create the second human account, import the template, register the custom agents with a registration key, seed the data, run the demo.
- **Gotchas:** from §6.
- **Kill switch design:** and why it's enforced in the tools, not the prompts.
- **Tests:** how to run them.
- **Disclaimers:** synthetic data, simulated payments, not legal advice.
- **Build and AI disclosure:** what existed before Nov 4, what was built during the hackathon, which AI tools were used.
- **Links:** the demo video, plus the blog post and #HowISwitch post if made.

---

## 12. Build plan (MVP first, in order)

1. Switch running locally, Owner and Accountant accounts linked, one agent answering in a room.
2. Synthetic data, `interest.py`, tests (India and UK).
3. Ledger agent posting fact cards in `#client-megamart`.
4. Cash (Codex) and Relationship (Claude Code) agents with instructions. Two-round debate with `[F#]` citations, plus `factcheck.py`.
5. Warden: freeze flag, `!stopall`, two-key `!resume`, circuit breaker, approvals bound to sender id, freeze-checked tools.
6. Options card, then draft and cross-review, then two approvals, then the simulated send, then the playbook write.
7. PayGuard checks and supplier room. Impostor rejection. 48-hour hold.
8. The template YAML, so everything imports in one step.
9. README, demo seed and reset script, recording.
10. Stretch: Desk summaries, UK client flow, Telegram, EU pack.

**If time runs short:** cut 10, then 7 (keep impostor rejection in the client flow), then the cross-review in step 6. Never cut the kill switch, the fact-check, or verified approvals. They are the core of the story.

---

## 13. Switch limitations found, and pull request plan (Track 03, optional)

**Limitations found:**

- No single **room-wide stop** that interrupts every agent at once. Only per-agent `!interrupt`.
- **Agent stays "live"** about an hour after Console quits (#1114, already claimed by someone else).
- **Messages to busy agents can be dropped.**
- **Files uploaded via the Mattermost API don't reach agents.**
- **The Mattermost port changes** on every restart.
- **Room creation is slow** and can outlast Console's timeout.
- **The bundled Mattermost user joins every channel,** which breaks private rooms.
- **New agents are owner-only;** identity links need confirming.
- **Every Switch call is a separate tool call,** so payloads bloat the agent's context (#1350).
- **Subagents can't be stopped individually** (#802).
- **On Windows,** template providers showed as "Not supported here."
- **No WhatsApp or SMS bridge** (another participant mentioned PRs for these).

**Track 03 rules:**

- Only issues labelled **hackathon** count.
- Comment on the issue, tag **@petr-sandbox** with your plan, and wait to be **assigned**.
- Read CONTRIBUTING.md and sign the CLA on your first PR.
- Up to 5 open PRs. Link the issue with `Closes #N`.
- The PR must be open by Nov 7, 11:59 PM IST.
- Low-effort PRs (typos, unreviewed AI output) aren't judged.

**Proposed new issue:** "Room-wide stop: one command interrupts every agent in a room." It may not get labelled in time, but it's still worth filing and mentioning in the README.

---

## 14. Builder preferences to respect

- A **different model for every LLM agent.**
- **Use every Switch-only feature** (§4.4).
- **A kill switch** that stops everything at once.
- **Multiple human roles,** played by one person.
- **Agents debate and check facts with real tools,** never guess numbers.
- **The room gets smarter** after every task.
- **Defend originality:** cite the evidence, acknowledge prior art (LLM Council, TradingAgents, negotiation simulators, refund desks), and explain the difference.
