"""Deterministic fact-check of a debate post against the Ledger's fact cards.

Rules:
- Every sentence that states a number must cite at least one fact id, like [F3].
- Every cited id must exist.
- Every number in the sentence must appear on one of the cards it cites (small rounding allowed).

No LLM is involved: an agent can't talk its way past this check.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass

from tools.facts import Fact, build_facts, facts_index

CITE = re.compile(r"\[\s*(F\d+)\s*\]", re.I)
MULTI_CITE = re.compile(r"\[\s*(F\d+(?:\s*[,;/]\s*F\d+)+)\s*\]", re.I)
NUMBER = re.compile(
    r"(?<![\w.])(?:₹|rs\.?\s*|inr\s*)?(\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)\s*(%|lakhs?|lacs?|l\b|k\b|cr\b|crores?)?",
    re.I,
)
# Things that look like numbers but aren't claims: ids, section numbers, rounds, list markers, dates in ids.
IGNORE = [
    re.compile(r"\bINV-\d+\b", re.I),
    re.compile(r"\b(?:s|sec|section)\.?\s*\d+[A-Z]?(?:\(\w+\))*", re.I),
    re.compile(r"\bround\s*\d\b", re.I),
    re.compile(r"^\s*\d+[.)]\s", re.M),
    re.compile(r"\((?:[A-D])\)"),
    re.compile(r"\bFY\s*\d{2,4}(?:-\d{2,4})?\b", re.I),
]
MULTIPLIER = {"%": 1, "l": 1e5, "lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5, "k": 1e3,
              "cr": 1e7, "crore": 1e7, "crores": 1e7}


@dataclass
class Flag:
    sentence: str
    problem: str


def _numbers(sentence: str) -> list[float]:
    s = CITE.sub(" ", MULTI_CITE.sub(" ", sentence))
    for pat in IGNORE:
        s = pat.sub(" ", s)
    out = []
    for m in NUMBER.finditer(s):
        val = float(m.group(1).replace(",", ""))
        unit = (m.group(2) or "").lower()
        val *= MULTIPLIER.get(unit, 1)
        if not unit and val in (1, 2, 3) and "₹" not in m.group(0):
            continue  # "two options", "1 of them": not a quantitative claim worth flagging
        out.append(val)
    return out


def _cited(sentence: str) -> list[str]:
    ids = [m.upper() for m in CITE.findall(sentence)]
    for group in MULTI_CITE.findall(sentence):
        ids += [x.strip().upper() for x in re.split(r"[,;/]", group)]
    return ids


def _matches(value: float, fact: Fact) -> bool:
    for v in fact.values:
        if v == value:
            return True
        if v and abs(v - value) / abs(v) <= 0.005:  # rounding, e.g. ₹6,820 vs 6,819.97
            return True
        if abs(v) >= 1e5 and abs(v - value) / abs(v) <= 0.02:  # "₹4.87 lakh"
            return True
    return False


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z₹(\[*-])|\n+", text)
    return [p.strip() for p in parts if p and p.strip()]


def check(text: str, facts: list[Fact] | None = None) -> list[Flag]:
    idx = facts_index(facts or build_facts())
    flags: list[Flag] = []
    for sent in split_sentences(text):
        nums = _numbers(sent)
        cited = _cited(sent)
        unknown = [c for c in cited if c not in idx]
        if unknown:
            flags.append(Flag(sent, f"cites {', '.join(unknown)}, which is not a fact card"))
            continue
        if not nums:
            continue
        if not cited:
            flags.append(Flag(sent, "states a number with no [F#] citation"))
            continue
        for n in nums:
            if not any(_matches(n, idx[c]) for c in cited):
                shown = f"{n:,.0f}" if n >= 100 else f"{n:g}"
                flags.append(Flag(sent, f"{shown} is not on {', '.join(cited)}"))
                break
    return flags


def render(author: str, flags: list[Flag]) -> str:
    if not flags:
        return f"✅ **Fact-check ({author}):** every number is cited and matches the fact cards."
    lines = [f"❌ **Fact-check ({author}):** {len(flags)} problem(s)."]
    for f in flags[:6]:
        quote = f.sentence if len(f.sentence) <= 140 else f.sentence[:137] + "..."
        lines.append(f"- ❌ \"{quote}\": {f.problem}")
    return "\n".join(lines)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Fact-check a debate post read from stdin or --text.")
    p.add_argument("--text")
    p.add_argument("--author", default="post")
    a = p.parse_args()
    text = a.text if a.text is not None else sys.stdin.read()
    fl = check(text)
    print(render(a.author, fl))
    sys.exit(1 if fl else 0)
