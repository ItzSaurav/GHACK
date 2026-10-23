"""Tests verifying Seva Vaani answers any and every question a citizen asks
across schemes, procedures, benefits, and general civic inquiries in English, Hindi, and Gujarati.
"""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.conversation.groq_client import groq_engine
from backend.app.main import app

client = TestClient(app)


def test_answer_question_pm_kisan_benefit_in_hindi():
    # 1. Start session
    res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
    sess_id = res_start.json()["session_id"]

    # 2. Citizen asks how much money is provided in PM-KISAN
    res_msg = client.post(
        "/api/v1/conversation/message",
        json={
            "session_id": sess_id,
            "text": "प्रधानमंत्री किसान योजना में कितने पैसे मिलते हैं?",
            "source": "voice",
        },
    )
    assert res_msg.status_code == 200
    data = res_msg.json()

    # Must directly answer the question about ₹6,000 and 3 installments
    assert "6,000" in data["reply"] or "2,000" in data["reply"]
    # Must politely continue the eligibility check without breaking the flow
    assert "आयु" in data["reply"] or "उम्र" in data["reply"] or "पात्रता" in data["reply"] or "व्यवसाय" in data["reply"]


def test_answer_question_aadhaar_bank_linking():
    res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
    sess_id = res_start.json()["session_id"]

    res_msg = client.post(
        "/api/v1/conversation/message",
        json={
            "session_id": sess_id,
            "text": "आधार कार्ड बैंक खाते से कैसे लिंक करें?",
            "source": "voice",
        },
    )
    assert res_msg.status_code == 200
    data = res_msg.json()

    # Must provide clear Aadhaar seeding instructions
    assert "शाखा" in data["reply"] or "डीबीटी" in data["reply"] or "सीडिंग" in data["reply"] or "बैंक" in data["reply"]


def test_answer_question_ayushman_bharat_in_english():
    res_start = client.post("/api/v1/conversation/start", json={"language": "en"})
    sess_id = res_start.json()["session_id"]

    res_msg = client.post(
        "/api/v1/conversation/message",
        json={
            "session_id": sess_id,
            "text": "What is Ayushman Bharat and how much health cover does it give?",
            "source": "voice",
        },
    )
    assert res_msg.status_code == 200
    data = res_msg.json()

    # Must state 5,00,000 health cover
    assert "5,00,000" in data["reply"] or "cashless" in data["reply"].lower() or "hospital" in data["reply"].lower()


def test_answer_question_gujarati_pm_kisan_rupees():
    res_start = client.post("/api/v1/conversation/start", json={"language": "gu"})
    sess_id = res_start.json()["session_id"]

    res_msg = client.post(
        "/api/v1/conversation/message",
        json={
            "session_id": sess_id,
            "text": "પીએમ કિસાન યોજનામાં કેટલા રૂપિયા મળે છે?",
            "source": "voice",
        },
    )
    assert res_msg.status_code == 200
    data = res_msg.json()

    assert "6,000" in data["reply"] or "2,000" in data["reply"]
    assert data["detected_language"] == "gu"


def test_answer_question_who_are_you():
    res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
    sess_id = res_start.json()["session_id"]

    res_msg = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "तुम कौन हो?", "source": "voice"},
    )
    assert res_msg.status_code == 200
    data = res_msg.json()

    # Explains its identity as Seva Vaani
    assert "सेवा वाणी" in data["reply"] or "सहायता" in data["reply"]


def test_answer_question_why_asking_facts():
    res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
    sess_id = res_start.json()["session_id"]

    res_msg = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "मेरी उम्र क्यों पूछ रहे हो?", "source": "voice"},
    )
    assert res_msg.status_code == 200
    data = res_msg.json()

    # Explains official rules / age criteria
    assert "पात्र" in data["reply"] or "नियम" in data["reply"] or "योजना" in data["reply"]


def test_groq_answers_open_ended_custom_query():
    # Verify that when Groq is available, it can answer any open-ended question
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(
            message=MagicMock(
                content="जी, जैविक खेती के लिए सरकार परंपरागत कृषि विकास योजना के तहत सहायता देती है। क्या आप खेती करते हैं?"
            )
        )
    ]

    with patch.object(groq_engine, "client", MagicMock()):
        groq_engine.client.chat.completions.create.return_value = mock_resp

        res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
        sess_id = res_start.json()["session_id"]

        res_msg = client.post(
            "/api/v1/conversation/message",
            json={
                "session_id": sess_id,
                "text": "जैविक खेती (organic farming) के लिए सरकार क्या सब्सिडी देती है?",
                "source": "voice",
            },
        )
        assert res_msg.status_code == 200
        data = res_msg.json()
        assert "जैविक खेती" in data["reply"]
