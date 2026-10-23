"""Unit and Integration Tests for Seva Vaani Core Operational Directives."""

from fastapi.testclient import TestClient

from backend.app.conversation.dialogue import dialogue_manager
from backend.app.conversation.extractor import extract_all_facts
from backend.app.main import app
from backend.app.schemes.engine import check_scheme_eligibility

client = TestClient(app)


def test_directive_1_instant_activation_and_session_start():
    # 1. Start conversation
    res_start = client.post("/api/v1/conversation/start", json={"language": "en"})
    assert res_start.status_code == 200
    data = res_start.json()
    assert "Seva Vaani" in data["greeting"]
    assert "voice helper for government schemes" in data["greeting"]

    # 2. Test session-start trigger "[SESSION_START]"
    sess_id = data["session_id"]
    res_trigger = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "[SESSION_START]", "source": "voice"},
    )
    assert res_trigger.status_code == 200
    trigger_data = res_trigger.json()
    assert "Namaste" in trigger_data["reply"]
    assert "Seva Vaani" in trigger_data["reply"]


def test_directive_2_adaptive_intelligence_and_empathy_broken_sentences():
    # 1. Citizen reports drought/crop loss in casual Hindi: "Mera khet sookh gaya"
    res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
    sess_id = res_start.json()["session_id"]

    res_crop = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "Mera khet sookh gaya", "source": "voice"},
    )
    assert res_crop.status_code == 200
    crop_data = res_crop.json()
    # Empathy acknowledged
    assert "फसल" in crop_data["reply"] or "चिंता न करें" in crop_data["reply"]
    # Facts extracted
    assert crop_data["facts"]["has_crop_loss"] is True
    assert crop_data["facts"]["occupation"] == "farmer"

    # 2. Citizen reports education fee need: "College fees ke liye madad"
    res_start_edu = client.post("/api/v1/conversation/start", json={"language": "en"})
    sess_id_edu = res_start_edu.json()["session_id"]

    res_edu = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id_edu, "text": "College fees ke liye madad chahiye", "source": "voice"},
    )
    assert res_edu.status_code == 200
    edu_data = res_edu.json()
    assert "education" in edu_data["reply"].lower() or "scholarship" in edu_data["reply"].lower()
    assert edu_data["facts"]["occupation"] == "student"


def test_directive_3_conversational_extraction_slots():
    # Extraction of location, occupation, land in acres, income, and category
    sample_text = "I am a smallholder farmer in Mandya Karnataka with 2 acres land, OBC category, annual income 1.2 lakh"
    facts = extract_all_facts(sample_text)

    assert facts["occupation"] == "farmer"
    assert facts["state_of_residence"] == "Karnataka"
    assert facts["district"] == "Mandya"
    assert facts["land_acres"] == 2.0
    assert facts["land_hectares"] == round(2.0 * 0.404686, 2)
    assert facts["owns_cultivable_land"] is True
    assert facts["social_category"] == "obc"
    assert facts["annual_income"] == 120000


def test_directive_4_check_scheme_eligibility_tool_call():
    # Verify structured tool call check_scheme_eligibility returns deterministic rules
    result = check_scheme_eligibility(
        age=45,
        occupation="farmer",
        location_state="Uttar Pradesh",
        location_district="Varanasi",
        land_acres=2.0,
        annual_income=120000,
        social_category="obc",
        owns_cultivable_land=True,
        is_income_tax_payer=False,
        has_crop_loss=True,
    )

    assert result["status"] == "success"
    assert result["total_schemes_checked"] >= 5
    assert result["potential_matches_count"] >= 1
    matched_ids = [m["scheme_id"] for m in result["potential_matches"]]
    # PM-KISAN and STATE-KSS (crop loss) should match
    assert "PM-KISAN" in matched_ids
    assert "STATE-KSS" in matched_ids

    # API endpoint check
    res_api = client.post(
        "/api/v1/schemes/check-eligibility",
        json={
            "age": 45,
            "occupation": "farmer",
            "owns_cultivable_land": True,
            "is_income_tax_payer": False,
        },
    )
    assert res_api.status_code == 200
    api_data = res_api.json()
    assert api_data["status"] == "success"
    assert api_data["potential_matches_count"] >= 1


def test_directive_5_concise_spoken_responses_under_3_sentences():
    res_start = client.post("/api/v1/conversation/start", json={"language": "en"})
    sess_id = res_start.json()["session_id"]

    res_turn = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "45", "source": "voice"},
    )
    assert res_turn.status_code == 200
    reply = res_turn.json()["reply"]

    # Sentence count check (split by periods, exclamation marks, or question marks)
    import re
    sentences = [s.strip() for s in re.split(r"[.!?।]+", reply) if s.strip()]
    # Must be 1 to 3 concise sentences
    assert 1 <= len(sentences) <= 3
