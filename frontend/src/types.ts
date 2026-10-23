export type Language =
  | 'en'
  | 'kn'
  | 'hi'
  | 'gu'
  | 'ta'
  | 'te'
  | 'ur'
  | 'or'
  | 'mr'
  | 'ml';

export type EvaluationStatus =
  | 'potential_match'
  | 'not_matched'
  | 'insufficient_information'
  | 'manual_review';

export interface CriterionEvaluation {
  criterion_id: string;
  description: string;
  status: 'passed' | 'failed' | 'unknown' | 'exempted';
  reason: string;
}

export interface SchemeEvaluationResult {
  scheme_id: string;
  scheme_name: string;
  department: string;
  status: EvaluationStatus;
  confidence_score: number;
  reasons: string[];
  missing_facts: string[];
  required_documents: string[];
  benefit_summary: string;
  official_source_url: string;
  effective_date: string;
  last_verified_date: string;
  rule_version: string;
  scheme_version: string;
  is_illustrative: boolean;
  evaluated_criteria: CriterionEvaluation[];
}

export interface CitizenFacts {
  age?: number | null;
  gender?: string | null;
  occupation?: string | null;
  annual_income?: number | null;
  monthly_income?: number | null;
  land_hectares?: number | null;
  owns_cultivable_land?: boolean | null;
  is_income_tax_payer?: boolean | null;
  covered_by_epfo_esic?: boolean | null;
  is_pregnant_or_lactating?: boolean | null;
  has_crop_loss?: boolean | null;
  state_of_residence?: string | null;
  social_category?: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  text: string;
  source: 'text' | 'voice' | 'system';
  audioConfidence?: number;
  timestamp: number;
}

export interface FormField {
  field_key: string;
  label_en: string;
  label_hi: string;
  field_type: string;
  value: any;
  is_allowlisted: boolean;
  is_confirmed_by_citizen: boolean;
  validation_status: string;
}

export interface FormPreview {
  form_id: string;
  scheme_id: string;
  scheme_name: string;
  fields: FormField[];
  mandatory_missing_count: number;
  is_ready_for_review: boolean;
  disclaimer: string;
}

export interface FormSubmissionReceipt {
  tracking_id: string;
  form_id: string;
  scheme_id: string;
  status: string;
  submission_timestamp: number;
  message: string;
  next_steps: string[];
}
