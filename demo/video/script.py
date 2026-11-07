"""Narration and scene plan for the PaidSafe video. Shared by tts.py and build.py."""

VOICE = "en-IN-PrabhatNeural"
RATE = "+6%"

D, P, L = ("1 · Decide", "#60a5fa"), ("2 · Protect", "#f87171"), ("3 · Learn", "#a78bfa")

# (id, kind, narration, extra)
SCENES = [
    ("intro", "intro",
     "Meet PaidSafe: a team chat where a small business's people and AI agents make money decisions together, "
     "safely.", {}),
    ("pain_in", "pain_in",
     "The problem: a big customer pays late. Push too hard, and you lose them. Wait too long, and you miss "
     "payroll. Razorpay's Fix My Itch rates this eighty-two point eight, a top Indian business pain.", {}),
    ("pain_out", "pain_out",
     "And fraud has moved into chat. Someone poses as your accountant, types 'approved', and money goes out.", {}),
    ("pillars", "pillars",
     "PaidSafe does three things: it helps you decide with proven facts, it protects every approval, and it "
     "learns from every outcome.", {}),
    ("room", "room",
     "One Switch room: the owner, the accountant, and four agents. Two are plain code, so they can't invent "
     "numbers. Two AI debaters, on different models, argue each side.", {}),
    ("facts", "shot",
     "Part one: decide. The owner asks, chase or wait? The Ledger posts facts from the law: thirty-two days "
     "overdue, and seven thousand one hundred thirty rupees of interest owed.",
     {"img": "01_facts.png", "part": D, "label": "Fact cards from cited law"}),
    ("debate", "shot",
     "The agents debate. Every number must cite a card, and each post is fact-checked live.",
     {"img": "02_debate.png", "part": D, "label": "Debate, fact-checked live"}),
    ("options", "shot",
     "Then, four clear options, with their cash impact.",
     {"img": "03_options.png", "part": D, "label": "Options with cash impact"}),
    ("impostor", "shot",
     "Part two: protect. An impostor named Accountant tries to approve. Switch shows who really sent it, so the "
     "Warden rejects it.",
     {"img": "04_impostor.png", "part": P, "label": "Fake approval rejected by Switch sender id"}),
    ("draft", "shot",
     "Every amount in the draft is traced to a fact card.",
     {"img": "05_draft.png", "part": P, "label": "Every amount traced to its source"}),
    ("sent", "shot",
     "It's sent only after the real accountant and owner both approve.",
     {"img": "06_sent.png", "part": P, "label": "Two verified approvals, then send"}),
    ("kill", "shot2",
     "Why a freeze button? If an agent loops, or an attack starts, typing stop all freezes every tool, and only "
     "the other person can unfreeze it. No one, human or agent, can move money alone.",
     {"img": "07_frozen.png", "img2": "08_resumed.png", "part": P,
      "label": "Freeze: stop everything, two keys to resume"}),
    ("outcome", "shot",
     "Part three: learn. The accountant records the result: paid in twelve days.",
     {"img": "09_outcome.png", "part": L, "label": "The verified Accountant records the outcome"}),
    ("memory", "shot2",
     "Next time MegaMart is late, the Ledger brings that memory as a fact card, and marks the option that "
     "worked. Every decision makes the next one smarter.",
     {"img": "10_memory_facts.png", "img2": "11_memory_options.png", "part": L,
      "label": "Memory card F7: decisions get smarter"}),
    ("hood", "hood",
     "It's all built on Switch: the agent protocol, verified identities, room documents and templates, with "
     "guardrails and fifty-nine tests.", {}),
    ("roadmap", "roadmap",
     "Today, it's one mock client with four basic agents. The same template scales to a room per client, more "
     "agents, and supplier fraud checks.", {}),
    ("end", "end",
     "PaidSafe. Decide with proof. Approve with certainty.", {}),
]
