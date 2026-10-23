"""Deterministic Scheme Eligibility Engine.

Evaluates citizen facts against versioned scheme criteria using pure deterministic
logic. Never uses an LLM for final eligibility decisions.
"""

from typing import Any

from backend.app.schemes.catalogue import SchemeCatalogue, catalogue
from backend.app.schemes.models import (
    CitizenFacts,
    CriterionEvaluation,
    CriterionStatus,
    EvaluationStatus,
    SchemeCriterion,
    SchemeDefinition,
    SchemeEvaluationResult,
)


class EligibilityEngine:
    def __init__(self, scheme_repo: SchemeCatalogue = catalogue):
        self.repo = scheme_repo

    def evaluate_criterion(
        self, criterion: SchemeCriterion, facts: CitizenFacts
    ) -> CriterionEvaluation:
        fact_value = getattr(facts, criterion.field, None)

        # If fact is missing
        if fact_value is None:
            return CriterionEvaluation(
                criterion_id=criterion.id,
                description=criterion.description,
                status=CriterionStatus.UNKNOWN,
                reason=criterion.explanation_on_unknown,
            )

        # Evaluate based on operator
        matches_expected = False
        op = criterion.operator

        if op == "eq":
            matches_expected = (fact_value == criterion.expected_value)
        elif op == "gte":
            try:
                matches_expected = (float(fact_value) >= float(criterion.expected_value))
            except (ValueError, TypeError):
                matches_expected = False
        elif op == "lte":
            try:
                matches_expected = (float(fact_value) <= float(criterion.expected_value))
            except (ValueError, TypeError):
                matches_expected = False
        elif op == "in":
            if isinstance(criterion.expected_value, list):
                matches_expected = (fact_value in criterion.expected_value)
            else:
                matches_expected = (fact_value == criterion.expected_value)
        elif op == "is":
            matches_expected = (fact_value is criterion.expected_value)
        elif op == "is_not":
            matches_expected = (fact_value is not criterion.expected_value)
        else:
            matches_expected = False

        # If this is an exclusion criterion:
        # e.g., is_income_tax_payer == True is an EXCLUSION.
        # If matches_expected is True, the citizen IS excluded -> FAILED criterion.
        # If matches_expected is False, the citizen is NOT excluded -> PASSED criterion.
        if criterion.is_exclusion:
            if matches_expected:
                return CriterionEvaluation(
                    criterion_id=criterion.id,
                    description=criterion.description,
                    status=CriterionStatus.FAILED,
                    reason=criterion.explanation_on_fail,
                )
            else:
                return CriterionEvaluation(
                    criterion_id=criterion.id,
                    description=criterion.description,
                    status=CriterionStatus.PASSED,
                    reason=criterion.explanation_on_pass,
                )
        else:
            if matches_expected:
                return CriterionEvaluation(
                    criterion_id=criterion.id,
                    description=criterion.description,
                    status=CriterionStatus.PASSED,
                    reason=criterion.explanation_on_pass,
                )
            else:
                return CriterionEvaluation(
                    criterion_id=criterion.id,
                    description=criterion.description,
                    status=CriterionStatus.FAILED,
                    reason=criterion.explanation_on_fail,
                )

    def evaluate_scheme(
        self, scheme: SchemeDefinition, facts: CitizenFacts
    ) -> SchemeEvaluationResult:
        evaluations: list[CriterionEvaluation] = []
        reasons: list[str] = []
        missing_facts: list[str] = []

        has_failed_mandatory = False
        has_unknown_mandatory = False
        is_manual_review_needed = False

        # Special domain rule: Ayushman Bharat PM-JAY Senior Citizen Universal Expansion
        # All senior citizens aged 70 and above receive cover regardless of income.
        senior_citizen_pmjay_override = False
        if scheme.id == "AB-PMJAY" and facts.age is not None and facts.age >= 70:
            senior_citizen_pmjay_override = True

        for criterion in scheme.criteria:
            # Check override for Ayushman Bharat
            if senior_citizen_pmjay_override and criterion.id == "pmjay_income":
                eval_item = CriterionEvaluation(
                    criterion_id=criterion.id,
                    description=criterion.description,
                    status=CriterionStatus.EXEMPTED,
                    reason=f"Income ceiling exempted: Citizen age is {facts.age} (>=70 years) qualifying under universal Ayushman Vay Vandana expansion.",
                )
                evaluations.append(eval_item)
                reasons.append(eval_item.reason)
                continue

            eval_item = self.evaluate_criterion(criterion, facts)
            evaluations.append(eval_item)

            if eval_item.status == CriterionStatus.FAILED:
                if criterion.is_mandatory:
                    has_failed_mandatory = True
                    reasons.append(eval_item.reason)
            elif eval_item.status == CriterionStatus.UNKNOWN:
                if criterion.is_mandatory or criterion.field not in missing_facts:
                    has_unknown_mandatory = True
                    if criterion.field not in missing_facts:
                        missing_facts.append(criterion.field)
                    reasons.append(eval_item.reason)
            elif eval_item.status == CriterionStatus.PASSED:
                reasons.append(eval_item.reason)

        # Check for state applicability
        if (
            scheme.state_applicability != "All India"
            and facts.state_of_residence
            and (facts.state_of_residence.lower() not in scheme.state_applicability.lower())
        ):
            has_failed_mandatory = True
            reasons.append(
                f"Scheme applies to {scheme.state_applicability}, but citizen residence is {facts.state_of_residence}."
            )

        # Check manual review scenarios:
        # e.g. state-specific disaster relief requires on-ground patwari inspection
        if scheme.id == "STATE-KSS" and facts.has_crop_loss is True:
            is_manual_review_needed = True

        # Determine overall evaluation status
        if has_failed_mandatory:
            status = EvaluationStatus.NOT_MATCHED
            confidence = 0.95
        elif has_unknown_mandatory:
            status = EvaluationStatus.INSUFFICIENT_INFORMATION
            confidence = 0.50
        elif is_manual_review_needed:
            status = EvaluationStatus.MANUAL_REVIEW
            confidence = 0.85
        else:
            status = EvaluationStatus.POTENTIAL_MATCH
            confidence = 0.90

        return SchemeEvaluationResult(
            scheme_id=scheme.id,
            scheme_name=scheme.name,
            department=scheme.department,
            status=status,
            confidence_score=confidence,
            reasons=reasons,
            missing_facts=missing_facts,
            required_documents=scheme.required_documents,
            benefit_summary=scheme.benefit_summary,
            official_source_url=scheme.official_source_url,
            effective_date=scheme.effective_date,
            last_verified_date=scheme.last_verified_date,
            rule_version=scheme.rule_version,
            scheme_version=scheme.scheme_version,
            is_illustrative=scheme.is_illustrative,
            evaluated_criteria=evaluations,
        )

    def evaluate_all(self, facts: CitizenFacts) -> list[SchemeEvaluationResult]:
        schemes = self.repo.get_all()
        results = [self.evaluate_scheme(s, facts) for s in schemes]
        # Sort so potential matches and manual reviews appear first
        sort_order = {
            EvaluationStatus.POTENTIAL_MATCH: 0,
            EvaluationStatus.MANUAL_REVIEW: 1,
            EvaluationStatus.INSUFFICIENT_INFORMATION: 2,
            EvaluationStatus.NOT_MATCHED: 3,
        }
        results.sort(key=lambda r: (sort_order.get(r.status, 99), -r.confidence_score))
        return results


# Global singleton engine instance
engine = EligibilityEngine()


def check_scheme_eligibility(
    age: int | None = None,
    occupation: str | None = None,
    location_state: str | None = None,
    location_district: str | None = None,
    land_acres: float | None = None,
    annual_income: int | None = None,
    social_category: str | None = None,
    gender: str | None = None,
    owns_cultivable_land: bool | None = None,
    is_income_tax_payer: bool | None = None,
    covered_by_epfo_esic: bool | None = None,
    has_crop_loss: bool | None = None,
    is_pregnant_or_lactating: bool | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Structured tool function to evaluate scheme eligibility against verified database rules.
    Never hallucinates cutoffs or amounts; returns verified match status, reasons, and missing facts.
    """
    facts = CitizenFacts(
        age=age,
        occupation=occupation,
        state_of_residence=location_state or kwargs.get("state_of_residence"),
        district=location_district or kwargs.get("district"),
        land_acres=land_acres,
        land_hectares=land_acres * 0.404686 if land_acres is not None else kwargs.get("land_hectares"),
        annual_income=annual_income,
        social_category=social_category,
        gender=gender,
        owns_cultivable_land=owns_cultivable_land if owns_cultivable_land is not None else (True if land_acres and land_acres > 0 else None),
        is_income_tax_payer=is_income_tax_payer,
        covered_by_epfo_esic=covered_by_epfo_esic,
        has_crop_loss=has_crop_loss,
        is_pregnant_or_lactating=is_pregnant_or_lactating,
    )
    eval_results = engine.evaluate_all(facts)
    matches = [r for r in eval_results if r.status in [EvaluationStatus.POTENTIAL_MATCH, EvaluationStatus.MANUAL_REVIEW]]
    insufficient = [r for r in eval_results if r.status == EvaluationStatus.INSUFFICIENT_INFORMATION]
    not_matched = [r for r in eval_results if r.status == EvaluationStatus.NOT_MATCHED]

    return {
        "status": "success",
        "total_schemes_checked": len(eval_results),
        "potential_matches_count": len(matches),
        "potential_matches": [m.model_dump() for m in matches],
        "insufficient_information_count": len(insufficient),
        "insufficient_schemes": [m.scheme_name for m in insufficient],
        "not_matched_count": len(not_matched),
        "all_results": [r.model_dump() for r in eval_results],
    }
