"""Data models for Scheme catalog, Citizen Facts, and Deterministic Eligibility Evaluation."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EvaluationStatus(str, Enum):
    POTENTIAL_MATCH = "potential_match"
    NOT_MATCHED = "not_matched"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    MANUAL_REVIEW = "manual_review"


class CriterionStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    EXEMPTED = "exempted"


class CriterionEvaluation(BaseModel):
    criterion_id: str
    description: str
    status: CriterionStatus
    reason: str


class SchemeEvaluationResult(BaseModel):
    scheme_id: str
    scheme_name: str
    department: str
    status: EvaluationStatus
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasons: list[str]
    missing_facts: list[str]
    required_documents: list[str]
    benefit_summary: str
    official_source_url: str
    effective_date: str
    last_verified_date: str
    rule_version: str
    scheme_version: str
    is_illustrative: bool = False
    evaluated_criteria: list[CriterionEvaluation] = []


class CitizenFacts(BaseModel):
    age: int | None = None
    gender: str | None = None  # "female", "male", "other"
    occupation: str | None = None  # "farmer", "unorganized_worker", "salaried_govt", "salaried_private", "student", "self_employed", "homemaker", "unemployed"
    annual_income: int | None = None  # in INR
    monthly_income: int | None = None  # in INR
    land_hectares: float | None = None  # land in hectares
    land_acres: float | None = None  # land in acres
    owns_cultivable_land: bool | None = None
    is_income_tax_payer: bool | None = None
    covered_by_epfo_esic: bool | None = None
    is_pregnant_or_lactating: bool | None = None
    has_crop_loss: bool | None = None
    state_of_residence: str | None = None
    district: str | None = None
    social_category: str | None = None  # "general", "obc", "sc", "st"

    # Provenance tracking
    fact_sources: dict[str, str] = Field(default_factory=dict)  # fact_key -> "voice", "text", "corrected"
    fact_confirmed: dict[str, bool] = Field(default_factory=dict)  # fact_key -> True/False


class SchemeCriterion(BaseModel):
    id: str
    description: str
    field: str
    operator: str  # "gte", "lte", "eq", "in", "is", "is_not"
    expected_value: Any
    is_mandatory: bool = True
    is_exclusion: bool = False
    explanation_on_pass: str
    explanation_on_fail: str
    explanation_on_unknown: str


class SchemeDefinition(BaseModel):
    id: str
    name: str
    name_hi: str | None = None
    department: str
    state_applicability: str = "All India"
    description: str
    description_hi: str | None = None
    benefit_summary: str
    benefit_summary_hi: str | None = None
    required_documents: list[str]
    required_documents_hi: list[str] | None = None
    official_source_url: str
    effective_date: str
    last_verified_date: str
    scheme_version: str
    rule_version: str
    is_illustrative: bool = False
    criteria: list[SchemeCriterion]
