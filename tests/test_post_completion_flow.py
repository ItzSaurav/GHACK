"""Test post-completion conversational intelligence.
Verifies that Seva Vaani does NOT repeat summaries, provides specific scheme details when asked,
and automatically prepares/opens prefilled forms when requested by the citizen.
"""
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_post_completion_form_fill_and_details():
    # 1. Start session in Hindi
    res_start = client.post("/api/v1/conversation/start", json={"language": "hi"})
    assert res_start.status_code == 200
    sess_id = res_start.json()["session_id"]

    # 2. Intake sequence as in citizen conversation
    turns = [
        "मेरी आयु 50 साल है",
        "मैं खेती करता हूं",
        "हां है मेरे पास",
        "नहीं भरता कोई भी",
        "हां हुआ है",
        "पुरुष",
        "100000 से कम",
    ]

    last_res = None
    for user_text in turns:
        res = client.post(
            "/api/v1/conversation/message",
            json={"session_id": sess_id, "text": user_text, "source": "voice"},
        )
        assert res.status_code == 200
        last_res = res.json()

    # Verify intake is completed and summary was issued
    assert last_res["is_completed"] is True
    summary_text = last_res["reply"]
    assert "बधाई हो जी" in summary_text

    # 3. Citizen asks: "मुझे प्रधानमंत्री किसान योजना में फॉर्म भरना है"
    res_form = client.post(
        "/api/v1/conversation/message",
        json={
            "session_id": sess_id,
            "text": "मुझे प्रधानमंत्री किसान योजना में फॉर्म भरना है",
            "source": "voice",
        },
    )
    assert res_form.status_code == 200
    form_data = res_form.json()

    # Must NOT repeat the congratulatory summary
    assert "बधाई हो जी" not in form_data["reply"]
    # Must indicate the form is prepared using citizen's facts
    assert "आवेदन फॉर्म" in form_data["reply"] or "तैयार कर दिया है" in form_data["reply"]
    # Must signal open_form_scheme_id for PM-KISAN
    assert form_data["open_form_scheme_id"] == "PM-KISAN"

    # Verify that form preview endpoint works with these facts
    res_preview = client.post(
        "/api/v1/forms/preview",
        json={"session_id": sess_id, "scheme_id": "PM-KISAN"},
    )
    assert res_preview.status_code == 200
    preview_data = res_preview.json()
    fields_map = {f["field_key"]: f["value"] for f in preview_data["fields"]}
    assert fields_map["age"] == 50
    assert fields_map["occupation"] == "farmer"
    assert fields_map["owns_cultivable_land"] is True

    # 4. Citizen asks for scheme details: "आयुष्मान भारत योजना का विवरण बताओ"
    res_details = client.post(
        "/api/v1/conversation/message",
        json={
            "session_id": sess_id,
            "text": "आयुष्मान भारत योजना का विवरण बताओ",
            "source": "voice",
        },
    )
    assert res_details.status_code == 200
    details_data = res_details.json()

    # Must NOT repeat the congratulatory summary
    assert "बधाई हो जी" not in details_data["reply"]
    # Must provide benefit/document details
    assert "5,00,000" in details_data["reply"] or "लाभ" in details_data["reply"] or "दस्तावेज" in details_data["reply"]


def test_post_completion_gujarati_form_fill():
    # 1. Start in Gujarati
    res_start = client.post("/api/v1/conversation/start", json={"language": "gu"})
    sess_id = res_start.json()["session_id"]

    turns = [
        "મારી ઉંમર ૪૫ વર્ષ છે",
        "હું ખેડૂત છું",
        "હા જમીન છે",
        "ના ટેક્સ નથી ભરતા",
        "હા પાક નુકસાન થયું છે",
        "પુરુષ",
        "વાર્ષિક આવક ૮૦૦૦૦",
    ]

    for user_text in turns:
        res = client.post(
            "/api/v1/conversation/message",
            json={"session_id": sess_id, "text": user_text, "source": "voice"},
        )
        assert res.status_code == 200

    # Citizen asks to fill form in Gujarati
    res_form = client.post(
        "/api/v1/conversation/message",
        json={
            "session_id": sess_id,
            "text": "પીએમ કિસાન યોજનાનું ફોર્મ ભરી આપો",
            "source": "voice",
        },
    )
    assert res_form.status_code == 200
    data = res_form.json()

    # Form trigger signal
    assert data["open_form_scheme_id"] == "PM-KISAN"
    assert "અરજી ફોર્મ" in data["reply"] or "ફોર્મ" in data["reply"]
