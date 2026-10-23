"""Unit tests for the Deterministic Scheme Eligibility Engine."""

from backend.app.schemes.catalogue import catalogue
from backend.app.schemes.engine import engine
from backend.app.schemes.models import CitizenFacts, EvaluationStatus


def test_catalogue_loaded():
    schemes = catalogue.get_all()
    assert len(schemes) >= 5
    ids = [s.id for s in schemes]
    assert "PM-KISAN" in ids
    assert "PM-SYM" in ids
    assert "PMMVY" in ids
    assert "AB-PMJAY" in ids
    assert "STATE-KSS" in ids


def test_pm_kisan_match():
    facts = CitizenFacts(
        occupation="farmer",
        owns_cultivable_land=True,
        is_income_tax_payer=False,
    )
    result = engine.evaluate_scheme(catalogue.get_by_id("PM-KISAN"), facts)
    assert result.status == EvaluationStatus.POTENTIAL_MATCH
    assert "PM-KISAN" == result.scheme_id
    assert len(result.required_documents) > 0
    assert result.official_source_url == "https://pmkisan.gov.in"


def test_pm_kisan_excluded_by_tax_payer():
    facts = CitizenFacts(
        occupation="farmer",
        owns_cultivable_land=True,
        is_income_tax_payer=True,  # Disqualifying exclusion
    )
    result = engine.evaluate_scheme(catalogue.get_by_id("PM-KISAN"), facts)
    assert result.status == EvaluationStatus.NOT_MATCHED
    assert any("income tax" in r.lower() for r in result.reasons)


def test_pm_sym_boundary_conditions():
    # Exactly age 18, income 15000 -> MATCH
    facts_18 = CitizenFacts(
        age=18,
        occupation="unorganized_worker",
        monthly_income=15000,
        covered_by_epfo_esic=False,
        is_income_tax_payer=False,
    )
    res_18 = engine.evaluate_scheme(catalogue.get_by_id("PM-SYM"), facts_18)
    assert res_18.status == EvaluationStatus.POTENTIAL_MATCH

    # Exactly age 40, income 15000 -> MATCH
    facts_40 = CitizenFacts(
        age=40,
        occupation="unorganized_worker",
        monthly_income=15000,
        covered_by_epfo_esic=False,
        is_income_tax_payer=False,
    )
    res_40 = engine.evaluate_scheme(catalogue.get_by_id("PM-SYM"), facts_40)
    assert res_40.status == EvaluationStatus.POTENTIAL_MATCH

    # Age 41 -> NOT MATCHED
    facts_41 = CitizenFacts(
        age=41,
        occupation="unorganized_worker",
        monthly_income=12000,
        covered_by_epfo_esic=False,
        is_income_tax_payer=False,
    )
    res_41 = engine.evaluate_scheme(catalogue.get_by_id("PM-SYM"), facts_41)
    assert res_41.status == EvaluationStatus.NOT_MATCHED

    # Monthly income 15001 -> NOT MATCHED
    facts_income_exceed = CitizenFacts(
        age=25,
        occupation="unorganized_worker",
        monthly_income=15001,
        covered_by_epfo_esic=False,
        is_income_tax_payer=False,
    )
    res_income = engine.evaluate_scheme(catalogue.get_by_id("PM-SYM"), facts_income_exceed)
    assert res_income.status == EvaluationStatus.NOT_MATCHED


def test_pmmvy_pregnant_mother_match():
    facts = CitizenFacts(
        gender="female",
        age=22,
        is_pregnant_or_lactating=True,
        occupation="homemaker",
    )
    result = engine.evaluate_scheme(catalogue.get_by_id("PMMVY"), facts)
    assert result.status == EvaluationStatus.POTENTIAL_MATCH
    assert any("Mother and Child Protection" in doc for doc in result.required_documents)


def test_pmmvy_male_applicant_not_matched():
    facts = CitizenFacts(
        gender="male",
        age=25,
        is_pregnant_or_lactating=False,
    )
    result = engine.evaluate_scheme(catalogue.get_by_id("PMMVY"), facts)
    assert result.status == EvaluationStatus.NOT_MATCHED


def test_ayushman_bharat_senior_citizen_universal_override():
    # Citizen is 72 years old with high income (> 2,50,000)
    # Under universal PM-JAY expansion for 70+, this qualifies!
    facts = CitizenFacts(
        age=72,
        annual_income=800000,
    )
    result = engine.evaluate_scheme(catalogue.get_by_id("AB-PMJAY"), facts)
    assert result.status == EvaluationStatus.POTENTIAL_MATCH
    assert any("universal" in r.lower() or "exempted" in r.lower() for r in result.reasons)


def test_insufficient_information_when_facts_empty():
    facts = CitizenFacts()
    results = engine.evaluate_all(facts)
    assert len(results) == catalogue.count()
    # When no facts are provided, schemes must report INSUFFICIENT_INFORMATION, not NOT_MATCHED
    assert all(r.status == EvaluationStatus.INSUFFICIENT_INFORMATION for r in results)
    # Must list missing facts
    pm_kisan_res = next(r for r in results if r.scheme_id == "PM-KISAN")
    assert "occupation" in pm_kisan_res.missing_facts
    assert "owns_cultivable_land" in pm_kisan_res.missing_facts


def test_manual_review_status():
    facts = CitizenFacts(
        occupation="farmer",
        has_crop_loss=True,
        state_of_residence="Madhya Pradesh",
    )
    result = engine.evaluate_scheme(catalogue.get_by_id("STATE-KSS"), facts)
    assert result.status == EvaluationStatus.MANUAL_REVIEW
    assert result.is_illustrative is True
