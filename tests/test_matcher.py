import pytest

from value_sort.matcher import load_prereg, match, phrase_regex, term_regex
from value_sort.schema import Item

PRE = load_prereg()


def it(title, asin="X"):
    return Item(parent_asin=asin, title=title, price=10.0, average_rating=4.5, rating_number=10, details={})


@pytest.mark.parametrize("q, title, ok", [
    ("protein powder", "Whey Protein Powder, Chocolate", True),
    ("protein powder", "Vegan Protein-Powder 2 lb", True),
    ("protein powder", "Protein Powders Variety Pack", True),
    ("protein powder", "Powder, protein-rich", False),          # order matters
    ("protein powder", "Protein Shake Powder", False),          # adjacency matters
    ("baby wipes", "Huggies Baby Wipes, Unscented", True),
    ("baby wipes", "Baby Wipe Refill", True),                    # singular allowed
    ("vitamin d", "Vitamin D3 5000 IU", True),
    ("vitamin d", "Vitamin D-3 Softgels", True),
    ("vitamin d", "Vitamin D 1000 IU", True),
    ("vitamin d", "Vitamins C, D, E Complex", False),
    ("vitamin d", "D-Mannose with Vitamin C", False),
    ("vitamin d", "Vitamin Daily Pack", False),                  # 'd' must be a whole short word
    ("vitamin d", "Vitamin D 3 drops", True),                    # matches as 'vitamin d' (the '3' is separate)
    ("creatine", "Creatine Monohydrate Powder", True),
    ("creatine", "Creatinine test strips", False),
])
def test_phrase(q, title, ok):
    assert bool(phrase_regex(q).search(title)) is ok


@pytest.mark.parametrize("term, title, ok", [
    ("holder", "Hand Sanitizer Holder Keychain", True),
    ("case", "Purell Gel 8 oz (Case of 12)", True),             # literal application (DECISIONS 57)
    ("case", "Showcase Sanitizer", False),
    ("grab bar", "Toilet Paper Holder with Grab-Bar", True),
    ("dispenser only", "Foam Dispenser Only", True),
    ("dispenser only", "Gel with Dispenser Pump", False),
])
def test_terms(term, title, ok):
    assert bool(term_regex(term).search(title)) is ok


def test_match_splits_kept_and_excluded():
    items = [it("Hand Sanitizer Gel 8 oz", "A"), it("Hand Sanitizer Holder", "B"), it("Lotion", "C")]
    r = match(items, "hand sanitizer", PRE)
    assert [i.parent_asin for i in r.kept] == ["A"]
    assert [(i.parent_asin, h) for i, h in r.excluded] == [("B", ["holder"])]


def test_per_query_terms_only_apply_to_their_query():
    items = [it("Protein Powder with Scoop", "A"), it("Creatine with Scoop", "B"), it("Hand Sanitizer with Scoop", "C")]
    assert match(items, "protein powder", PRE).excluded[0][1] == ["scoop"]
    assert match(items, "hand sanitizer", PRE).kept[0].parent_asin == "C"


def test_adjacency_lost_is_any_order_minus_phrase():
    from value_sort.step7_audit import adjacency_lost
    items = [it("Whey Protein Isolate Powder", "A"), it("Whey Protein Powder", "B"),
             it("Powder for protein shakes", "C"), it("Protein Bar", "D")]
    assert [i.parent_asin for i in adjacency_lost(items, "protein powder")] == ["A", "C"]


def test_recall_rows_ignore_exclusion_terms_and_cap_per_query():
    from value_sort.step7_audit import recall_rows
    items = [it(f"Protein Isolate Powder {n}", f"P{n:02}") for n in range(25)] + \
        [it("Protein Isolate Powder Holder", "H")]
    rows = [r for r in recall_rows(items, PRE) if r["query"] == "protein powder"]
    assert len(rows) == PRE["recall_audit"]["per_query_sample"]
    assert rows == [r for r in recall_rows(items, PRE) if r["query"] == "protein powder"]  # seeded
    assert all(r["in_set"] == "" for r in rows)
