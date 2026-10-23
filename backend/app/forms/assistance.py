"""Step-by-step form assistance and allowlisted field prefill with citizen review gate."""

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

from backend.app.schemes.models import CitizenFacts


class FormField(BaseModel):
    field_key: str
    label_en: str
    label_hi: str
    field_type: str  # "text", "number", "select", "boolean"
    value: Any
    is_allowlisted: bool = True
    is_confirmed_by_citizen: bool = False
    validation_status: str = "valid"  # "valid", "missing", "unconfirmed"


class FormPreview(BaseModel):
    form_id: str = Field(default_factory=lambda: f"FORM-{uuid.uuid4().hex[:8].upper()}")
    scheme_id: str
    scheme_name: str
    fields: list[FormField]
    mandatory_missing_count: int
    is_ready_for_review: bool
    disclaimer: str
    generated_at: float = Field(default_factory=time.time)


class FormSubmissionRequest(BaseModel):
    form_id: str
    scheme_id: str
    citizen_explicit_approval: bool
    reviewed_fields: dict[str, Any]
    language: str = "hi"


class FormSubmissionReceipt(BaseModel):
    tracking_id: str
    form_id: str
    scheme_id: str
    status: str  # "submitted_for_verification", "demo_completed"
    submission_timestamp: float
    message: str
    next_steps: list[str]


# Security allowlist: Only these fields can be prefilled or handled
ALLOWLISTED_FORM_FIELDS = {
    "applicant_name": {"en": "Full Name", "hi": "आवेदक का पूरा नाम", "type": "text"},
    "age": {"en": "Age", "hi": "आयु", "type": "number"},
    "gender": {"en": "Gender", "hi": "लिंग", "type": "select"},
    "occupation": {"en": "Occupation / Profession", "hi": "व्यवसाय / पेशा", "type": "text"},
    "state_of_residence": {"en": "State of Residence", "hi": "निवास का राज्य", "type": "text"},
    "monthly_income": {"en": "Monthly Income (INR)", "hi": "मासिक आय (रुपये)", "type": "number"},
    "annual_income": {"en": "Annual Family Income (INR)", "hi": "वार्षिक पारिवारिक आय (रुपये)", "type": "number"},
    "owns_cultivable_land": {"en": "Cultivable Land Ownership", "hi": "कृषि योग्य भूमि स्वामित्व", "type": "boolean"},
    "is_income_tax_payer": {"en": "Income Tax Payer Status", "hi": "आयकर दाता स्थिति", "type": "boolean"},
    "has_crop_loss": {"en": "Natural Disaster Crop Loss", "hi": "फसल क्षति स्थिति", "type": "boolean"},
    "is_pregnant_or_lactating": {"en": "Maternal Nutrition Support Status", "hi": "मातृत्व पोषण लाभ स्थिति", "type": "boolean"},
}


class FormAssistanceService:
    def generate_preview(self, scheme_id: str, scheme_name: str, facts: CitizenFacts, language: str = "hi") -> FormPreview:
        fields: list[FormField] = []
        missing_count = 0

        for key, meta in ALLOWLISTED_FORM_FIELDS.items():
            val = getattr(facts, key, None)
            is_confirmed = facts.fact_confirmed.get(key, False) if val is not None else False
            val_status = "valid" if val is not None else "missing"

            if val is None and key in ["age", "occupation"]:
                missing_count += 1

            fields.append(
                FormField(
                    field_key=key,
                    label_en=meta["en"],
                    label_hi=meta["hi"],
                    field_type=meta["type"],
                    value=val,
                    is_allowlisted=True,
                    is_confirmed_by_citizen=is_confirmed,
                    validation_status=val_status,
                )
            )

        disclaimer = (
            "यह फॉर्म केवल प्रदर्शन एवं पूर्व-समीक्षा हेतु है। नागरिक की स्पष्ट स्वीकृति के बिना कोई भी डेटा जमा नहीं किया जाएगा। "
            "संवेदनशील पहचान पत्र (जैसे आधार नंबर या बैंक पासवर्ड) कभी भी इस प्रणाली में दर्ज न करें।"
            if language == "hi"
            else "This form is for pre-submission citizen review only. No data is transmitted without explicit citizen consent. "
            "Never share sensitive identity numbers, bank passwords, or OTPs."
        )

        return FormPreview(
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            fields=fields,
            mandatory_missing_count=missing_count,
            is_ready_for_review=True,
            disclaimer=disclaimer,
        )

    def submit_form(self, req: FormSubmissionRequest) -> FormSubmissionReceipt:
        if not req.citizen_explicit_approval:
            raise ValueError("Citizen explicit approval is mandatory before any form submission.")

        tracking_id = f"APPL-{uuid.uuid4().hex[:10].upper()}"

        next_steps = [
            "Keep your tracking ID safe for future reference." if req.language == "en" else "भविष्य के संदर्भ हेतु अपनी ट्रैकिंग आईडी सुरक्षित रखें।",
            "Carry original Aadhaar and Bank Passbook to the verification center." if req.language == "en" else "सत्यापन केंद्र पर मूल आधार कार्ड एवं बैंक पासबुक साथ ले जाएं।",
            "Demonstration receipt generated successfully." if req.language == "en" else "प्रदर्शन रसीद सफलतापूर्वक जनरेट हो गई है।",
        ]

        return FormSubmissionReceipt(
            tracking_id=tracking_id,
            form_id=req.form_id,
            scheme_id=req.scheme_id,
            status="submitted_for_verification",
            submission_timestamp=time.time(),
            message="आवेदन समीक्षा और सत्यापन हेतु सफलतापूर्वक दर्ज कर लिया गया है।" if req.language == "hi" else "Application successfully recorded for citizen verification.",
            next_steps=next_steps,
        )


form_service = FormAssistanceService()
