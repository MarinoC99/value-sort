"""Extractor tests. Titles come from the development sample, which excludes the 200
audit items (DECISIONS.md #32)."""

import pytest

from value_sort.unit_price import extract, parse_title
from value_sort.schema import Item

T = 0.7


def it(title, **details):
    return Item(parent_asin="X", title=title, price=10.0, average_rating=4.0, rating_number=10,
                details={k.replace("_", " "): v for k, v in details.items()})


def got(title, **details):
    e = extract(it(title, **details), T)
    r = e.result
    return None if r is None else (r.count, r.size, r.unit)


# --- returns a pack size ---------------------------------------------------------------

@pytest.mark.parametrize("title, details, expected", [
    ("Stinger Detox Folli-Kleen Hair Shampoo Cleanser - 4 FL OZ", {}, (1, 4, "fl oz")),
    ("Crest Pro-Health Densify Daily Whitening Toothpaste 4.1 oz", {"Item_Package_Quantity": "1"}, (1, 4.1, "oz")),
    ("GNC Acetyl-L-Carnitine 500mg - 60 Capsules", {"Unit_Count": "60.00 Count"}, (1, 60, "ct")),
    ("Best Naturals Lutein, 20mg, 120 Softgels", {"Unit_Count": "120.00 Count"}, (1, 120, "ct")),
    ("Aimil Neeri Tablets (10*30 Tablets)", {}, (10, 30, "ct")),
    ("DenTek Floss Picks 6 x 60 Pack (360)", {}, (6, 60, "ct")),
    ("(2 PACK) - Organic India - Turmeric Formula | 60's | 2 PACK BUNDLE", {"Number_of_Items": "2"}, (2, 60, "ct")),
    ("BZK Antiseptic Towelette 5\" x 7\" [Box of 100]", {"Unit_Count": "100.00 Count"}, (1, 100, "ct")),
    ("R-kay Plastic Spoons 600 Pack - Plastic Teaspoons", {}, (1, 600, "ct")),
    ("Dixie Smart Top Reclosable Hot Cup Lid (100/bag)", {}, (1, 100, "ct")),
    ("Vanish Oxi Action Fabric Stain Remover Spray 400ml", {"Unit_Count": "13.53 Fl Oz"}, (1, 400, "ml")),
    ("Respiration Essential Oil Roll On, Pre-Diluted 10ml (1/3 fl oz)", {"Item_Volume": "10 Milliliters"}, (1, 10, "ml")),
    ("Toshiba CR2450 3 Volt Lithium Coin Battery (8 pcs)", {"Unit_Count": "8.00 Count"}, (1, 8, "ct")),
    ("Vitamin D2 Liquid Drops, 400iu, 1,200 Servings, 60ml", {"Item_Form": "Drop"}, (1, 60, "ml")),
    ("Momentous Tyrosine Capsules, 60 Servings", {"Unit_Count": "60.00 Count"}, (1, 60, "ct")),
    ("Shampoo 12 fl oz, Pack of 2 (24 fl oz total)", {}, (2, 12, "fl oz")),
    ("Whey Protein 2 lb (907 g)", {}, (1, 2, "lb")),
    ("Laundry Pods", {"Size": "42 Count (Pack of 2)"}, (2, 42, "ct")),
    ("Renata CR1220 Lithium Coin Cell Battery (5 Pack)", {"Unit_Count": "5.00 Count"}, (1, 5, "ct")),
    ("Tissue Paper 200 Sheets", {"Size": "200ct", "Sheet_Count": "200"}, (1, 200, "ct")),
])
def test_extracts(title, details, expected):
    assert got(title, **{k: v for k, v in details.items()}) == pytest.approx(expected)


# --- capacity is not contents ---------------------------------------------------------

def test_cup_capacity_ignored_count_used():
    assert got("Member's Mark Paper Cold Cup, 9 oz. (360 ct.)", Unit_Count="360 Count") == (1, 360, "ct")


def test_trash_bag_gallons_are_capacity():
    assert got("Global Strategies DB20 Demo Bag 42 Gallon Trash Bag", Unit_Count="1 Count") is None


def test_glasses_pack_without_count_abstains():
    assert got("G.E.T. 20 oz. Pineapple Glasses, Reusable Plastic (Pack of 4)", Unit_Count="1.0 Count") is None


def test_capacity_title_ignores_volume_field():
    assert got("Heavy Duty Mop Bucket with Wringer", Item_Volume="5 Gallons") is None


# --- abstains rather than guessing -----------------------------------------------------

@pytest.mark.parametrize("title, details, flag", [
    ("ThinkThin Protein Bars Chocolate Fudge, 2.1 Oz, 10 Count", {}, "title_size_count_ambiguous"),
    ("Sports Research Turmeric Curcumin C3 Complex 500 mg", {"Number_of_Items": "1"}, "no_size_found"),
    ("Whey Protein 25g Protein, 5 lbs, 3 lbs", {}, "title_conflicting_weight"),
    ("Fish Oil 120 Softgels", {"Unit_Count": "60 Count"}, "sources_disagree"),
    ("Floor Squeegee, 36\" Length", {"Item_Weight": "0.01 Ounces"}, "no_size_found"),
    ("Gift Bags", {"Number_of_Items": "25"}, "only_weak_sources"),
    ("Fujitsu NiMH Battery, AA 1.2V, Pack of 4", {"Unit_Count": "2.00 Count"}, "sources_disagree"),
    ("Mondo Medical 6 Pack of Black Toilet Paper Rolls", {"Sheet_Count": "140"}, "sources_disagree"),
    ("Tums E-X Berries Size 96s Tums Extra Strength", {"Unit_Count": "6.00 Count"}, "sources_disagree"),
    ("Energizer Max Alkaline AA Batteries 8 ea (Pack of 2)", {"Unit_Count": "2.00 Count"}, "sources_disagree"),
    ("FOGGLE Anti-Fog Cleansing Towelette (Single Towelette)", {"Size": "24L"}, "only_weak_sources"),
    ("Travel Toothbrush Kit, Includes Brushes and 60 Tabs", {}, "title_is_kit"),
])
def test_abstains_with_flag(title, details, flag):
    e = extract(it(title, **details), T)
    assert e.result is None and e.flag == flag


def test_item_weight_is_never_a_source():
    assert got("Heating Pad for Back", Item_Weight="2 Pounds") is None


def test_unit_count_of_one_is_filler():
    assert got("100 Pcs Happy Easter Napkins", Unit_Count="1.0 Count") == (1, 100, "ct")


def test_dosage_and_nutrition_are_not_size():
    readings, _ = parse_title("Protein Bar 20g Protein, Vitamin C 500 mg")
    assert readings == []


def test_confidence_levels():
    both = extract(it("Lutein 120 Softgels", Unit_Count="120 Count"), T)
    title_only = extract(it("Lutein 120 Softgels"), T)
    detail_only = extract(it("Lutein", Unit_Count="120 Count"), T)
    assert (both.confidence, title_only.confidence, detail_only.confidence) == (0.95, 0.8, 0.75)
    assert extract(it("Lutein", Unit_Count="120 Count"), 0.8).result is None  # threshold respected
