from datetime import date

import pytest

from tools.interest import StaleRate, india_due_date, india_interest, uk_interest
from tools.common import inr, load_rules

RULES = load_rules("india_msmed")


def test_due_date_agreed_days_under_cap():
    assert india_due_date(date(2026, 9, 6), True, 30, RULES) == date(2026, 10, 6)


def test_due_date_capped_at_45_days():
    assert india_due_date(date(2026, 9, 1), True, 90, RULES) == date(2026, 10, 16)


def test_due_date_15_days_without_written_agreement():
    assert india_due_date(date(2026, 9, 1), False, None, RULES) == date(2026, 9, 16)


def test_no_interest_before_due_date():
    r = india_interest(100000, date(2026, 9, 6), True, 30, on=date(2026, 10, 6), rules=RULES)
    assert r.interest == 0 and r.days_overdue == 0


def test_india_one_full_month_is_monthly_rate():
    # Due 6 Oct; interest runs 7 Oct..6 Nov = exactly one month at 16.5%/12 = 1.375%.
    r = india_interest(480000, date(2026, 9, 6), True, 30, on=date(2026, 11, 6), rules=RULES)
    assert r.full_months == 1 and r.extra_days == 0
    assert r.interest == pytest.approx(6600.00, abs=0.01)


def test_india_compounds_monthly():
    # Due 31 Jan; 1 Feb..30 Apr is exactly three months: P * (1.01375^3 - 1), more than simple interest would give.
    r = india_interest(100000, date(2026, 1, 1), True, 30, on=date(2026, 4, 30), rules=RULES)
    assert r.full_months == 3
    assert r.interest == pytest.approx(100000 * (1.01375 ** 3 - 1), abs=0.01)
    assert r.interest > 100000 * 0.01375 * 3


def test_demo_invoice_figure():
    r = india_interest(480000, date(2026, 9, 6), True, 30, on=date(2026, 11, 7), rules=RULES)
    assert r.days_overdue == 32
    assert r.interest == pytest.approx(6819.97, abs=0.01)


def test_stale_rate_refused_unless_confirmed():
    with pytest.raises(StaleRate):
        india_interest(1000, date(2027, 6, 1), True, 30, on=date(2027, 8, 1), rules=RULES)
    r = india_interest(1000, date(2027, 6, 1), True, 30, on=date(2027, 8, 1), rules=RULES, rate_confirmed=True)
    assert r.interest > 0


def test_uk_simple_interest_and_fixed_compensation():
    rules = load_rules("uk_late_payment")
    r = uk_interest(5000, date(2026, 10, 1), on=date(2026, 10, 31), rules=rules)
    # 12% simple for 30 days on £5,000 = 49.32; £70 band for £1,000-£9,999.99
    assert r.interest == pytest.approx(5000 * 0.12 * 30 / 365, abs=0.01)
    assert r.fixed_compensation == 70


@pytest.mark.parametrize("amount,comp", [(999.99, 40), (1000, 70), (9999.99, 70), (10000, 100)])
def test_uk_compensation_bands(amount, comp):
    rules = load_rules("uk_late_payment")
    assert uk_interest(amount, date(2026, 10, 1), on=date(2026, 10, 2), rules=rules).fixed_compensation == comp


def test_inr_grouping():
    assert inr(480000) == "₹4,80,000"
    assert inr(12345678) == "₹1,23,45,678"
    assert inr(999) == "₹999"
