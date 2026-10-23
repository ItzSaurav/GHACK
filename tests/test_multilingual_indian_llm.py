"""Unit tests for Multilingual 10-Indian-Language expansion and Indian Accent LLM."""

import pytest
from fastapi.testclient import TestClient

from backend.app.conversation.dialogue import dialogue_manager
from backend.app.conversation.extractor import extract_all_facts
from backend.app.conversation.indian_accent_llm import indian_accent_llm
from backend.app.conversation.session import ConversationSession, MessageRecord
from backend.app.main import app

client = TestClient(app)


def test_indian_accent_llm_greetings():
    hi_greet = indian_accent_llm.format_greeting("hi")
    en_greet = indian_accent_llm.format_greeting("en")
    kn_greet = indian_accent_llm.format_greeting("kn")
    ta_greet = indian_accent_llm.format_greeting("ta")

    assert "नमस्ते जी" in hi_greet
    assert "Namaste ji" in en_greet
    assert "ನಮಸ್ಕಾರ" in kn_greet
    assert "வணக்கம்" in ta_greet


def test_kannada_fact_extraction():
    text = "ನನ್ನ ವಯಸ್ಸು 35 ವರ್ಷ ಮತ್ತು ನಾನು ರೈತ, ಕೃಷಿ ಭೂಮಿ ಇದೆ"
    facts = extract_all_facts(text)
    assert facts.get("age") == 35
    assert facts.get("occupation") == "farmer"
    assert facts.get("owns_cultivable_land") is True


def test_tamil_fact_extraction():
    text = "எனக்கு 40 வயது நான் விவசாயி மற்றும் நிலம் உள்ளது"
    facts = extract_all_facts(text)
    assert facts.get("age") == 40
    assert facts.get("occupation") == "farmer"
    assert facts.get("owns_cultivable_land") is True


def test_dialogue_across_all_ten_languages():
    languages = ["en", "kn", "hi", "gu", "ta", "te", "ur", "or", "mr", "ml"]
    for lang in languages:
        q = dialogue_manager.get_question("age", lang)
        assert "text" in q
        assert len(q["text"]) > 5
        assert len(q["options"]) >= 2

        # Start conversation API
        res = client.post("/api/v1/conversation/start", json={"language": lang})
        assert res.status_code == 200
        data = res.json()
        assert data["language"] == lang
        assert data["current_question_key"] == "age"


def test_multilingual_tts_generation():
    # Test Kannada and Tamil TTS endpoints
    for lang, sample in [("kn", "ನಮಸ್ಕಾರ"), ("ta", "வணக்கம்"), ("te", "నమస్కారం"), ("gu", "નમસ્તે")]:
        res = client.get("/api/v1/voice/tts", params={"text": sample, "language": lang})
        assert res.status_code == 200
        assert res.headers["content-type"] in ["audio/mpeg", "audio/wav"]
        assert len(res.content) > 100


def test_anti_repetition_and_adaptive_clarification():
    sess = ConversationSession(language="en")
    sess.facts.age = 35
    sess.current_question_key = "occupation"
    sess.messages.append(
        MessageRecord(role="assistant", text="Could you share what work you do?", language="en", source="system")
    )

    # User says something ambiguous that does not yield an occupation
    res = dialogue_manager.process_message(sess, "I just do some various things here and there")
    assert res["current_question_key"] == "occupation"
    # Reply must be an adaptive clarification with helpful options, not verbatim repeat of previous prompt
    assert res["reply"] != sess.messages[0].text
    assert "farming, daily wage labour" in res["reply"]


def test_silence_prompt_during_active_session():
    sess = ConversationSession(language="hi")
    sess.current_question_key = "age"
    sess.messages.append(
        MessageRecord(role="assistant", text="कृपया अपनी आयु बताएं।", language="hi", source="system")
    )
    sess.messages.append(
        MessageRecord(role="user", text="नमस्ते जी", language="hi", source="text")
    )

    # Empty text (silence from microphone) sent during active session
    res = dialogue_manager.process_message(sess, "")
    assert res["current_question_key"] == "age"
    # Must NOT reset to initial welcome greeting!
    assert "नमस्ते जी! मैं सेवा वाणी हूँ" not in res["reply"]
    assert "सुनाई नहीं दी" in res["reply"]

