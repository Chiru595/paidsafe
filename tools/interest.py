"""Statutory late-payment interest, calculated in code from cited rule packs.

India (MSMED Act s.15/s.16): due date = agreed days capped at 45 from acceptance, or 15 days with no
written agreement. Interest is compound with monthly rests at 3x the RBI Bank Rate, from the day after
the due date.

UK (Late Payment of Commercial Debts (Interest) Act 1998): simple interest at base rate + 8 points, plus
fixed compensation of £40 / £70 / £100 by debt size.

Information only. Not legal or financial advice.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta

from tools.common import as_of_date, load_invoices, load_rules


class StaleRate(ValueError):
    """The rate in the rule pack is older than allowed and nobody confirmed it."""


def add_months(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    for day in (d.day, 30, 29, 28):  # clamp e.g. 31 Jan + 1 month -> 28/29 Feb
        try:
            return date(y, m, day)
        except ValueError:
            continue
    raise ValueError(d)


def _check_rate_age(rules: dict, rate_key: str, on: date, confirmed: bool) -> None:
    rate_as_of = date.fromisoformat(str(rules[rate_key]["as_of"]))
    age = (on - rate_as_of).days
    if age > rules.get("max_rate_age_days", 120) and not confirmed:
        raise StaleRate(f"{rate_key} is {age} days old (as of {rate_as_of}); Accountant must confirm it.")


@dataclass
class IndiaResult:
    principal: float
    accepted_on: str
    due_date: str
    days_overdue: int
    annual_rate_pct: float
    full_months: int
    extra_days: int
    interest: float
    total_due: float
    bank_rate_pct: float
    bank_rate_as_of: str
    source_url: str


def india_due_date(accepted_on: date, written_agreement: bool, agreed_days: int | None, rules: dict) -> date:
    pd = rules["payment_deadline"]
    if written_agreement and agreed_days:
        days = min(int(agreed_days), pd["max_days_with_agreement"])
    else:
        days = pd["days_without_agreement"]
    return accepted_on + timedelta(days=days)


def india_interest(principal: float, accepted_on: date, written_agreement: bool, agreed_days: int | None,
                   on: date | None = None, rules: dict | None = None, rate_confirmed: bool = False) -> IndiaResult:
    rules = rules or load_rules("india_msmed")
    on = on or as_of_date()
    _check_rate_age(rules, "bank_rate", on, rate_confirmed)

    due = india_due_date(accepted_on, written_agreement, agreed_days, rules)
    annual = rules["bank_rate"]["value_pct"] * rules["interest"]["multiple_of_bank_rate"] / 100
    start = due + timedelta(days=1)  # interest runs from the day after the due date
    days_overdue = max(0, (on - due).days)

    balance = float(principal)
    months, extra_days = 0, 0
    if on >= start:
        # The period runs from `start` to `on` inclusive, so the first month ends on start + 1 month - 1 day.
        end = on + timedelta(days=1)
        while add_months(start, months + 1) <= end:
            months += 1
        balance *= (1 + annual / 12) ** months
        extra_days = (end - add_months(start, months)).days
        balance *= 1 + annual * extra_days / 365

    interest = round(balance - principal, 2)
    return IndiaResult(
        principal=float(principal), accepted_on=accepted_on.isoformat(), due_date=due.isoformat(),
        days_overdue=days_overdue, annual_rate_pct=round(annual * 100, 4), full_months=months,
        extra_days=extra_days, interest=interest, total_due=round(principal + interest, 2),
        bank_rate_pct=rules["bank_rate"]["value_pct"], bank_rate_as_of=str(rules["bank_rate"]["as_of"]),
        source_url=rules["interest"]["source_url"],
    )


@dataclass
class UKResult:
    principal: float
    days_overdue: int
    annual_rate_pct: float
    interest: float
    fixed_compensation: int
    total_due: float


def uk_fixed_compensation(principal: float, rules: dict) -> int:
    for band in rules["fixed_compensation_gbp"]:
        if band["below"] is None or principal < band["below"]:
            return band["amount"]
    raise ValueError("no band")


def uk_interest(principal: float, due: date, on: date | None = None, rules: dict | None = None,
                rate_confirmed: bool = False) -> UKResult:
    rules = rules or load_rules("uk_late_payment")
    on = on or as_of_date()
    _check_rate_age(rules, "base_rate", on, rate_confirmed)
    annual = (rules["base_rate"]["value_pct"] + rules["interest"]["points_above_base_rate"]) / 100
    days = max(0, (on - due).days)
    interest = round(principal * annual * days / 365, 2)
    comp = uk_fixed_compensation(principal, rules) if days > 0 else 0
    return UKResult(float(principal), days, round(annual * 100, 4), interest, comp,
                    round(principal + interest + comp, 2))


def invoice_interest(invoice_id: str, on: date | None = None) -> IndiaResult:
    inv = load_invoices()[invoice_id]
    return india_interest(float(inv["amount_inr"]), date.fromisoformat(inv["accepted_on"]),
                          inv["written_agreement"] == "yes", int(inv["agreed_days"] or 0), on=on)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Statutory interest for an invoice (India MSMED).")
    p.add_argument("invoice_id")
    args = p.parse_args()
    print(json.dumps(asdict(invoice_interest(args.invoice_id)), indent=2))
