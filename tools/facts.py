"""Ledger fact cards (F1..F6) and the options card, built from data and rule packs with no LLM.

Each card carries the numbers it states (`values`), so the fact-checker can tell whether a debater quoted a
card correctly.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import date

from tools.common import DISCLAIMER, DATA, ROOT, as_of_date, inr, load_invoices, load_json, load_rules
from tools.interest import invoice_interest

PLAYBOOKS = ROOT / "state" / "playbooks"


@dataclass
class Fact:
    id: str
    text: str
    values: list[float] = field(default_factory=list)
    source: str = ""

    def render(self) -> str:
        src = f" _(source: {self.source})_" if self.source else ""
        return f"**{self.id}** {self.text}{src}"


def build_facts(invoice_id: str = "INV-1042", on: date | None = None) -> list[Fact]:
    on = on or as_of_date()
    inv = load_invoices()[invoice_id]
    client = load_json(DATA / "clients.json")[inv["client"]]
    cash = load_json(DATA / "cash.json")
    rules = load_rules("india_msmed")
    r = invoice_interest(invoice_id, on=on)

    amount = float(inv["amount_inr"])
    accepted = date.fromisoformat(inv["accepted_on"])
    days_since = (on - accepted).days
    hist = client["late_history"]
    runway = cash["bank_balance_inr"] / cash["weekly_burn_inr"]
    runway_paid = (cash["bank_balance_inr"] + amount) / cash["weekly_burn_inr"]
    tax_rate = rules["tax_lever"]["illustrative_tax_rate_pct"]
    tax_at_stake = amount * tax_rate / 100

    return [
        Fact("F1", f"{invoice_id} to {client['name']}: {inr(amount)}, accepted on {accepted:%d %b %Y}, "
                   f"{days_since} days ago.",
             [amount, days_since, float(invoice_id.split('-')[1])], "data/invoices.csv"),
        Fact("F2", f"Written agreement: {inv['agreed_days']} days, so the due date was {date.fromisoformat(r.due_date):%d %b %Y} "
                   f"(MSMED s.15 caps it at 45). It is **{r.days_overdue} days overdue**.",
             [float(inv["agreed_days"]), 45, r.days_overdue], rules["payment_deadline"]["source_url"]),
        Fact("F3", f"Statutory interest to date: **{inr(r.interest)}** (compound, monthly rests, {r.annual_rate_pct}% "
                   f"= 3 x RBI Bank Rate {r.bank_rate_pct}% as of {r.bank_rate_as_of}). Total due {inr(r.total_due)}. "
                   f"Not tax-deductible for the buyer (s.23).",
             [r.interest, round(r.interest), r.annual_rate_pct, 3, r.bank_rate_pct, r.total_due, round(r.total_due), 23],
             r.source_url),
        Fact("F4", f"{client['name']} is {client['revenue_share_pct']}% of revenue. Paid late on {hist['paid_late']} of "
                   f"the last {hist['invoices_last_12m']} invoices, {hist['avg_days_late']} days late on average.",
             [client["revenue_share_pct"], hist["paid_late"], hist["invoices_last_12m"], hist["avg_days_late"]],
             "data/clients.json"),
        Fact("F5", f"Cash runway: **{runway:.1f} weeks** at {inr(cash['weekly_burn_inr'])}/week burn "
                   f"({inr(cash['bank_balance_inr'])} in the bank). If {invoice_id} is paid: {runway_paid:.1f} weeks.",
             [round(runway, 1), cash["weekly_burn_inr"], cash["bank_balance_inr"], round(runway_paid, 1)],
             "data/cash.json"),
        Fact("F6", f"Income Tax s.43B(h): paying an MSE late means {client['name']} can deduct the {inr(amount)} only "
                   f"in the year it actually pays. At an illustrative {tax_rate}% tax rate that is "
                   f"{inr(tax_at_stake)} of deduction timing at stake for the buyer.",
             [43, amount, tax_rate, tax_at_stake], rules["tax_lever"]["source_url"]),
    ]


def facts_index(facts: list[Fact]) -> dict[str, Fact]:
    return {f.id: f for f in facts}


def read_playbook(client_key: str) -> str:
    path = PLAYBOOKS / f"{client_key}.md"
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def render_fact_cards(facts: list[Fact], client_key: str = "megamart") -> str:
    lines = ["### 📒 Ledger fact cards", *[f"- {f.render()}" for f in facts]]
    pb = read_playbook(client_key)
    if pb:
        entries = [l for l in pb.splitlines() if l.startswith("- ")]
        lines += ["", f"**Playbook loaded** ({len(entries)} past decision(s)). Latest: {entries[-1][2:] if entries else ''}"]
    lines += ["", f"_{DISCLAIMER} All data is synthetic._"]
    return "\n".join(lines)


OPTIONS = {
    "A": ("Friendly nudge + 1% early-payment discount if paid within 7 days", "relationship"),
    "B": ("Firm reminder citing the statutory interest owed and the s.43B(h) deduction timing", "cash"),
    "C": ("Formal notice under MSMED s.15/16, escalating to MSEFC / MSME Samadhaan if unpaid in 15 days", "cash"),
    "D": ("Wait 2 weeks and bridge the gap from cash (no contact now)", "relationship"),
}


def options_card(invoice_id: str = "INV-1042", on: date | None = None) -> str:
    facts = facts_index(build_facts(invoice_id, on))
    inv = load_invoices()[invoice_id]
    amount = float(inv["amount_inr"])
    cash = load_json(DATA / "cash.json")
    interest = facts["F3"].values[0]
    burn = cash["weekly_burn_inr"]
    impact = {
        "A": f"recover {inr(amount * 0.99)} sooner; give up {inr(amount * 0.01)} discount and {inr(interest)} interest",
        "B": f"claim {inr(amount + interest)} (principal + interest [F3]); some relationship risk [F4]",
        "C": f"claim {inr(amount + interest)} with legal backing; highest relationship risk [F4]",
        "D": f"runway drops by 2 weeks of burn ({inr(2 * burn)}) to {(cash['bank_balance_inr'] - 2 * burn) / burn:.1f} weeks [F5]; interest keeps accruing",
    }
    lines = ["### 🧾 Options card (Ledger, template-based)"]
    for k, (desc, side) in OPTIONS.items():
        lines.append(f"- **({k})** {desc}. Cash impact: {impact[k]}. _Drafted by: {side}_")
    lines += ["", "Owner: reply `approve A`, `approve B`, `approve C` or `approve D`."]
    return "\n".join(lines)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("invoice_id", nargs="?", default="INV-1042")
    p.add_argument("--options", action="store_true")
    a = p.parse_args()
    print(options_card(a.invoice_id) if a.options else render_fact_cards(build_facts(a.invoice_id)))
