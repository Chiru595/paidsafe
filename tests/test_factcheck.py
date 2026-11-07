from tools.factcheck import check


def test_cited_correct_numbers_pass():
    post = ("MegaMart owes ₹4,80,000 [F1] and is 32 days overdue [F2]. Interest is ₹6,820 [F3]. "
            "They are 30% of revenue [F4]. Runway is 8.0 weeks [F5].")
    assert check(post) == []


def test_uncited_number_flagged():
    flags = check("MegaMart will cancel 40% of our orders if we push.")
    assert len(flags) == 1 and "no [F#] citation" in flags[0].problem


def test_wrong_number_with_citation_flagged():
    flags = check("Interest is already ₹25,000 [F3].")
    assert len(flags) == 1 and "not on F3" in flags[0].problem


def test_number_cited_to_wrong_card_flagged():
    flags = check("Runway is 8.0 weeks [F1].")
    assert len(flags) == 1


def test_unknown_fact_id_flagged():
    flags = check("Runway is 8 weeks [F9].")
    assert len(flags) == 1 and "F9" in flags[0].problem


def test_lakh_format_accepted():
    assert check("The invoice is ₹4.8 lakh [F1].") == []


def test_sections_ids_and_rounds_are_not_claims():
    assert check("Round 2: under s.43B(h) and s.16 the buyer loses on INV-1042 [F6].") == []


def test_text_without_numbers_passes():
    assert check("We should keep the relationship warm and ask politely.") == []
