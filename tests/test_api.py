from app import app


def test_scam_message():
    r = app.test_client().post(
        "/analyze",
        json={"message": "Aapka SBI account block ho jayega, KYC update karo http://sbi-kyc.xyz"},
    )
    assert r.status_code == 200
    assert r.get_json()["risk"] in ("medium", "high")


def test_empty_message():
    r = app.test_client().post("/analyze", json={"message": ""})
    assert r.status_code == 400