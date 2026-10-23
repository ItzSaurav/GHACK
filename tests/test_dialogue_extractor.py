"""Tests for Multilingual Fact Extractor and Dialogue Flow."""

from backend.app.conversation.dialogue import dialogue_manager
from backend.app.conversation.extractor import (
    extract_age,
    extract_boolean_facts,
    extract_income,
    extract_occupation,
)
from backend.app.conversation.session import ConversationSession


def test_extract_age_multilingual():
    assert extract_age("my age is 28") == 28
    assert extract_age("I am 45 years old") == 45
    assert extract_age("meri umar 32 saal hai") == 32
    assert extract_age("उम्र 25 वर्ष") == 25
    # Devanagari numerals
    assert extract_age("मेरी आयु ३५ साल है") == 35
    assert extract_age("आयु ४०") == 40
    # Hindi word numerals
    assert extract_age("तीस साल") == 30
    assert extract_age("पच्चीस वर्ष") == 25


def test_extract_income():
    # Monthly
    amt, period = extract_income("12000 per month")
    assert amt == 12000
    assert period == "monthly"

    amt_k, _ = extract_income("kamai lagbhag 14k hai")
    assert amt_k == 14000

    amt_hi, period_hi = extract_income("महीने का 10000 रुपये कमाता हूँ")
    assert amt_hi == 10000
    assert period_hi == "monthly"

    # Annual
    amt_ann, p_ann = extract_income("saal ka 2.5 lakh income hai")
    assert amt_ann == 250000
    assert p_ann == "annual"


def test_extract_occupation():
    assert extract_occupation("kisan hu kheti karta hu") == "farmer"
    assert extract_occupation("main ek daily wage majdoor hu") == "unorganized_worker"
    assert extract_occupation("sarkari school teacher hu") == "salaried_govt"
    assert extract_occupation("chhoti dukaan hai meri") == "self_employed"
    assert extract_occupation("housewife hu ghar ka kaam karti hu") == "homemaker"


def test_extract_boolean_flags():
    flags1 = extract_boolean_facts("haan mere paas zameen hai aur fasal kharab ho gayi")
    assert flags1.get("owns_cultivable_land") is True
    assert flags1.get("has_crop_loss") is True

    flags2 = extract_boolean_facts("zameen nahi hai, koi tax nahi bharta, no pf")
    assert flags2.get("owns_cultivable_land") is False
    assert flags2.get("is_income_tax_payer") is False
    assert flags2.get("covered_by_epfo_esic") is False


def test_dialogue_conversation_flow_farmer_to_completion():
    session = ConversationSession(language="hi")
    session.current_question_key = "age"

    # 1. Citizen provides age
    res1 = dialogue_manager.process_message(session, "मेरी उम्र 38 साल है")
    assert session.facts.age == 38
    assert res1["current_question_key"] == "occupation"
    assert res1["is_completed"] is False

    # 2. Citizen provides occupation
    res2 = dialogue_manager.process_message(session, "मैं एक किसान हूँ")
    assert session.facts.occupation == "farmer"
    assert res2["current_question_key"] == "owns_cultivable_land"
    assert res2["is_completed"] is False

    # 3. Citizen confirms land ownership
    res3 = dialogue_manager.process_message(session, "हाँ, 2 एकड़ खेती की जमीन है")
    assert session.facts.owns_cultivable_land is True
    assert res3["current_question_key"] == "is_income_tax_payer"
    assert res3["is_completed"] is False

    # 4. Citizen confirms tax status
    res4 = dialogue_manager.process_message(session, "नहीं, टैक्स नहीं भरता")
    assert session.facts.is_income_tax_payer is False
    assert res4["current_question_key"] == "has_crop_loss"
    assert res4["is_completed"] is False

    # 5. Citizen reports crop status
    res5 = dialogue_manager.process_message(session, "नहीं, इस साल कोई फसल नुकसान नहीं हुआ")
    assert session.facts.has_crop_loss is False

    # 6. Gender check
    if res5["current_question_key"] == "gender":
        res6 = dialogue_manager.process_message(session, "पुरुष (Male)")
    else:
        res6 = res5

    # 7. Check final evaluation
    # If annual income question is prompted:
    if res6["current_question_key"] == "annual_income":
        res7 = dialogue_manager.process_message(session, "साल का 80000 रुपये")
    else:
        res7 = res6

    assert res7["is_completed"] is True
    eval_list = res7["evaluation"]
    assert len(eval_list) > 0
    pm_kisan_eval = next((e for e in eval_list if e["scheme_id"] == "PM-KISAN"), None)
    assert pm_kisan_eval is not None
    assert pm_kisan_eval["status"] == "potential_match"
