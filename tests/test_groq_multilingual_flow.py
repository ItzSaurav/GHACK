"""Test Groq LLM multilingual flow for English, Hindi, and Gujarati.
Verifies language detection, natural conversational responses without technical meta announcements,
intake conversation, and final scheme eligibility.
"""
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_groq_multilingual_flow_english():
    # 1. Start conversation (greeting & ask info)
    res_start = client.post("/api/v1/conversation/start", json={"language": "en"})
    assert res_start.status_code == 200
    start_data = res_start.json()
    sess_id = start_data["session_id"]
    assert "Namaste" in start_data["greeting"] or "Welcome" in start_data["greeting"]

    # 2. Citizen expresses problem in English
    res_problem = client.post(
        "/api/v1/conversation/message",
        json={
            "session_id": sess_id,
            "text": "I am a small farmer with 2 acres land, 42 years old, annual income 80000 rupees. Need financial assistance.",
            "source": "voice",
        },
    )
    assert res_problem.status_code == 200
    data = res_problem.json()

    # Bot analyzes language and responds naturally in English WITHOUT meta announcement
    assert "we are going to use groq" not in data["reply"].lower()
    assert "आपकी भाषा" not in data["reply"]
    assert data["detected_language"] == "en"
    assert data["facts"]["age"] == 42
    assert data["facts"]["occupation"] == "farmer"
    assert data["facts"]["owns_cultivable_land"] is True
    assert data["facts"]["annual_income"] == 80000

    # 3. Answer remaining questions: is_income_tax_payer, has_crop_loss, gender
    res_tax = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "No, I do not pay income tax", "source": "voice"},
    )
    assert res_tax.status_code == 200

    res_crop = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "No, crop is fine", "source": "voice"},
    )
    assert res_crop.status_code == 200

    res_gender = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "Male", "source": "voice"},
    )
    assert res_gender.status_code == 200
    final_data = res_gender.json()

    assert final_data["is_completed"] is True
    # Verify eligible schemes provided
    assert len(final_data["evaluation"]) > 0
    matched_ids = [e["scheme_id"] for e in final_data["evaluation"] if e["status"] == "potential_match"]
    assert "PM-KISAN" in matched_ids


def test_groq_multilingual_flow_hindi():
    # 1. Start session
    res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
    sess_id = res_start.json()["session_id"]
    assert "नमस्ते" in res_start.json()["greeting"]

    # 2. Citizen expresses need in Hindi
    res_msg = client.post(
        "/api/v1/conversation/message",
        json={
            "session_id": sess_id,
            "text": "मेरी उम्र ३५ साल है, मैं मजदूर हूँ और मेरी मासिक आमदनी ₹8000 है। मुझे सरकारी सहायता चाहिए।",
            "source": "voice",
        },
    )
    assert res_msg.status_code == 200
    data = res_msg.json()

    # Bot analyzes language as Hindi and responds naturally WITHOUT meta announcements
    assert "we are going to use groq" not in data["reply"].lower()
    assert "पहचानी गई है" not in data["reply"]
    assert data["detected_language"] == "hi"
    assert data["facts"]["age"] == 35
    assert data["facts"]["occupation"] == "unorganized_worker"
    assert data["facts"]["monthly_income"] == 8000

    # Complete remaining questions: covered_by_epfo_esic, is_income_tax_payer, gender
    res_pf = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "पीएफ नहीं कटता है", "source": "voice"},
    )
    assert res_pf.status_code == 200

    res_tax = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "टैक्स नहीं देते हैं", "source": "voice"},
    )
    assert res_tax.status_code == 200

    res_gender = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "पुरुष", "source": "voice"},
    )
    assert res_gender.status_code == 200
    final_data = res_gender.json()

    assert final_data["is_completed"] is True
    assert len(final_data["evaluation"]) > 0
    matched_ids = [e["scheme_id"] for e in final_data["evaluation"] if e["status"] == "potential_match"]
    assert "PM-SYM" in matched_ids


def test_groq_multilingual_flow_gujarati():
    # 1. Start session
    res_start = client.post("/api/v1/conversation/start", json={"language": "gu"})
    sess_id = res_start.json()["session_id"]
    assert "નમસ્તે" in res_start.json()["greeting"]

    # 2. Citizen expresses need in Gujarati
    res_msg = client.post(
        "/api/v1/conversation/message",
        json={
            "session_id": sess_id,
            "text": "હું ખેડૂત છું, મારી ઉંમર ૪૦ વર્ષ છે, મારી પાસે ૩ એકર જમીન છે અને વાર્ષિક આવક ૭૫૦૦૦ છે. મારે સહાય જોઈએ છે.",
            "source": "voice",
        },
    )
    assert res_msg.status_code == 200
    data = res_msg.json()

    # Bot analyzes language as Gujarati and responds naturally WITHOUT meta announcements
    assert "we are going to use groq" not in data["reply"].lower()
    assert "તમારી ભાષા" not in data["reply"]
    assert data["detected_language"] == "gu"
    assert data["facts"]["occupation"] == "farmer"
    assert data["facts"]["age"] == 40
    assert data["facts"]["owns_cultivable_land"] is True

    # Complete questions: is_income_tax_payer, has_crop_loss, gender
    res_tax = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "ના, ટેક્સ નથી ભરતા", "source": "voice"},
    )
    assert res_tax.status_code == 200

    res_crop = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "હા, વરસાદથી પાક નુકસાન થયું છે", "source": "voice"},
    )
    assert res_crop.status_code == 200

    res_gender = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "પુરુષ", "source": "voice"},
    )
    assert res_gender.status_code == 200
    final_data = res_gender.json()

    assert final_data["is_completed"] is True
    assert len(final_data["evaluation"]) > 0
    matched_ids = [e["scheme_id"] for e in final_data["evaluation"] if e["status"] == "potential_match"]
    assert "PM-KISAN" in matched_ids
    assert "AB-PMJAY" in matched_ids
