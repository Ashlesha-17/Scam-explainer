def test_hindi_message_and_explanation():
    r = client.post("/analyze", json={
        "message": "आपका KYC अपडेट नहीं है, खाता बंद हो जाएगा। अभी लिंक पर क्लिक करें http://sbi-kyc.xyz",
        "lang": "hi",
    })
    d = r.get_json()
    assert d["risk"] in ("medium", "high")
    assert any("\u0900" <= ch <= "\u097F" for ch in d["summary"])  # explanation is in Devanagari