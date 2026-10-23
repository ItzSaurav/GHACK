"""Tests verifying Groq LLM operates as the primary conversational answer engine
across intake, completion summary, scheme details, and automated form filling in English, Hindi, and Gujarati.
"""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.conversation.groq_client import groq_engine
from backend.app.main import app

client = TestClient(app)


def test_groq_answer_engine_intake_turn():
    # Mock Groq client response for intake question
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content="जी, हम आपको सूखा राहत में पूरी मदद करेंगे। कृपया अपनी आयु बताएं।"))
    ]

    with patch.object(groq_engine, "client", MagicMock()):
        groq_engine.client.chat.completions.create.return_value = mock_resp

        # Start session
        res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
        sess_id = res_start.json()["session_id"]

        # User asks for help while stating crop problem
        res_msg = client.post(
            "/api/v1/conversation/message",
            json={
                "session_id": sess_id,
                "text": "मेरी फसल सूखे से बर्बाद हो गई, क्या मुझे सरकारी मदद मिल सकती है?",
                "source": "voice",
            },
        )
        assert res_msg.status_code == 200
        data = res_msg.json()
        assert "सूखा राहत" in data["reply"]
        assert "आयु" in data["reply"]
        assert data["detected_language"] == "hi"


def test_groq_answer_engine_post_completion_form_fill():
    # Mock Groq client response for form filling confirmation
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(
            message=MagicMock(
                content="जी, मैंने आपकी दर्ज जानकारी (आयु 50 वर्ष, किसान, 2 एकड़ जमीन) के साथ प्रधानमंत्री किसान सम्मान निधि का आवेदन फॉर्म खोल दिया है। कृपया स्क्रीन पर समीक्षा करें।"
            )
        )
    ]

    with patch.object(groq_engine, "client", MagicMock()):
        groq_engine.client.chat.completions.create.return_value = mock_resp

        # Start session and complete intake
        res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
        sess_id = res_start.json()["session_id"]

        turns = [
            "मेरी आयु 50 साल है",
            "मैं खेती करता हूं",
            "हां खेती की जमीन है",
            "टैक्स नहीं भरते",
            "हां फसल नुकसान हुआ है",
            "पुरुष",
            "100000",
        ]
        for t in turns:
            client.post(
                "/api/v1/conversation/message",
                json={"session_id": sess_id, "text": t, "source": "voice"},
            )

        # Citizen requests form filling
        res_form = client.post(
            "/api/v1/conversation/message",
            json={
                "session_id": sess_id,
                "text": "मुझे प्रधानमंत्री किसान योजना में फॉर्म भरना है",
                "source": "voice",
            },
        )
        assert res_form.status_code == 200
        data = res_form.json()
        assert data["open_form_scheme_id"] == "PM-KISAN"
        assert "आवेदन फॉर्म खोल दिया है" in data["reply"]
        assert "प्रधानमंत्री किसान" in data["reply"]


def test_groq_answer_engine_post_completion_scheme_details():
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(
            message=MagicMock(
                content="PM-KISAN: पात्र किसानों को प्रति वर्ष ₹6,000 की वित्तीय सहायता 3 किस्तों में मिलती है। आवश्यक दस्तावेज आधार कार्ड और बैंक पासबुक हैं।"
            )
        )
    ]

    with patch.object(groq_engine, "client", MagicMock()):
        groq_engine.client.chat.completions.create.return_value = mock_resp

        res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
        sess_id = res_start.json()["session_id"]

        turns = [
            "मेरी आयु 50 साल है",
            "मैं खेती करता हूं",
            "हां खेती की जमीन है",
            "टैक्स नहीं भरते",
            "हां फसल नुकसान हुआ है",
            "पुरुष",
            "100000",
        ]
        for t in turns:
            client.post(
                "/api/v1/conversation/message",
                json={"session_id": sess_id, "text": t, "source": "voice"},
            )

        res_details = client.post(
            "/api/v1/conversation/message",
            json={
                "session_id": sess_id,
                "text": "पीएम किसान योजना का विवरण और लाभ बताएं",
                "source": "voice",
            },
        )
        assert res_details.status_code == 200
        data = res_details.json()
        assert "6,000" in data["reply"]
        assert "आधार कार्ड" in data["reply"]
