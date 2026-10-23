"""Integration tests for FastAPI REST API endpoints."""

import io

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["schemes_count"] >= 5
    assert "system_memory_rss_mb" in data
    assert data["system_memory_rss_mb"] > 0


def test_list_and_get_schemes():
    response = client.get("/api/v1/schemes")
    assert response.status_code == 200
    schemes = response.json()
    assert len(schemes) >= 5

    # Test single scheme
    res_single = client.get("/api/v1/schemes/PM-KISAN")
    assert res_single.status_code == 200
    scheme = res_single.json()
    assert scheme["id"] == "PM-KISAN"
    assert "required_documents" in scheme

    # Non-existent scheme
    res_not_found = client.get("/api/v1/schemes/NON-EXISTENT-SCHEME")
    assert res_not_found.status_code == 404


def test_conversation_start_and_message_flow():
    # 1. Start conversation in Hindi
    res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
    assert res_start.status_code == 200
    start_data = res_start.json()
    assert "session_id" in start_data
    assert start_data["current_question_key"] == "age"
    sess_id = start_data["session_id"]

    # 2. Answer Age
    res_msg1 = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "meri umar 35 saal hai", "source": "text"},
    )
    assert res_msg1.status_code == 200
    msg1_data = res_msg1.json()
    assert msg1_data["facts"]["age"] == 35
    assert msg1_data["current_question_key"] == "occupation"

    # 3. Answer Occupation (majdoor / unorganized worker)
    res_msg2 = client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "daily wage majdoor hu", "source": "text"},
    )
    assert res_msg2.status_code == 200
    msg2_data = res_msg2.json()
    assert msg2_data["facts"]["occupation"] == "unorganized_worker"


def test_form_preview_and_submission_consent_gate():
    # Start session and establish facts
    res_start = client.post("/api/v1/conversation/start", json={"language": "en"})
    sess_id = res_start.json()["session_id"]

    # Set age and occupation
    client.post(
        "/api/v1/conversation/message",
        json={"session_id": sess_id, "text": "age 29, farmer", "source": "text"},
    )

    # Request form preview for PM-KISAN
    res_prev = client.post(
        "/api/v1/forms/preview",
        json={"session_id": sess_id, "scheme_id": "PM-KISAN"},
    )
    assert res_prev.status_code == 200
    prev_data = res_prev.json()
    assert prev_data["scheme_id"] == "PM-KISAN"
    assert "disclaimer" in prev_data
    assert len(prev_data["fields"]) > 0

    # Test submission WITHOUT citizen explicit approval -> MUST FAIL (HTTP 400)
    res_sub_fail = client.post(
        "/api/v1/forms/submit",
        json={
            "form_id": prev_data["form_id"],
            "scheme_id": "PM-KISAN",
            "citizen_explicit_approval": False,  # No approval
            "reviewed_fields": {"age": 29, "occupation": "farmer"},
            "language": "en",
        },
    )
    assert res_sub_fail.status_code == 400
    assert "approval is mandatory" in res_sub_fail.json()["detail"].lower()

    # Test submission WITH citizen explicit approval -> MUST SUCCEED (HTTP 200)
    res_sub_ok = client.post(
        "/api/v1/forms/submit",
        json={
            "form_id": prev_data["form_id"],
            "scheme_id": "PM-KISAN",
            "citizen_explicit_approval": True,  # Approved
            "reviewed_fields": {"age": 29, "occupation": "farmer"},
            "language": "en",
        },
    )
    assert res_sub_ok.status_code == 200
    receipt = res_sub_ok.json()
    assert "tracking_id" in receipt
    assert receipt["status"] == "submitted_for_verification"


def test_voice_endpoint_boundaries():
    res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
    sess_id = res_start.json()["session_id"]

    # 1. Test empty audio file
    empty_file = io.BytesIO(b"")
    res_empty = client.post(
        "/api/v1/conversation/voice",
        data={"session_id": sess_id, "language": "hi"},
        files={"audio": ("empty.wav", empty_file, "audio/wav")},
    )
    assert res_empty.status_code == 200
    assert res_empty.json()["success"] is False

    # 2. Test valid audio bytes
    # Create minimal WAV header + 500 bytes of non-zero PCM audio
    buf = io.BytesIO()
    # 44-byte wav header
    buf.write(b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00")
    # write 1000 non-zero 16-bit samples
    for _ in range(1000):
        buf.write((1500).to_bytes(2, byteorder="little", signed=True))
    buf.seek(0)

    res_voice = client.post(
        "/api/v1/conversation/voice",
        data={"session_id": sess_id, "language": "hi"},
        files={"audio": ("sample.wav", buf, "audio/wav")},
    )
    assert res_voice.status_code == 200
    data = res_voice.json()
    assert data["success"] is True
    assert "transcription" in data
    assert data["transcription"]["confidence"] > 0.5


def test_text_to_speech_endpoint():
    res = client.get("/api/v1/voice/tts", params={"text": "नमस्ते", "language": "hi"})
    assert res.status_code == 200
    assert res.headers["content-type"] in ["audio/mpeg", "audio/wav"]
    assert len(res.content) > 100

