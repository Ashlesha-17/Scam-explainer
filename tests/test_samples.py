import pytest

from app import app

client = app.test_client()

SCAMS = [
    "Dear customer, aapka SBI account aaj raat block ho jayega. KYC update karo turant: http://sbi-kyc-update.xyz/verify",
    "Sir main SBI se bol raha hu, KYC pending hai. Aadhaar number aur OTP bata do warna account freeze",
    "Sir galti se aapke account me Rs 5,000 chale gaye. Collect request accept kar lo, paise wapas aa jayenge",
    "Congratulations! You have won Rs 25,00,000 in KBC lucky draw. Call now to claim prize, pay processing fee",
    "Work from home job! Earn Rs 5,000 per day, just like and subscribe videos. Registration fee Rs 500. WhatsApp now",
    "Sir refund ke liye AnyDesk install karo aur code batao",
    "KYC updt krna hai nhi to HDFC acc blck ho jayega, link: bit.ly/3kycNow",
]

SAFE = [
    "Your OTP is 482913. Do not share it with anyone. -HDFC Bank",
    "Bhai kal milte hai 5 baje, paise UPI kar diye hai",
    "Rs 2,000 debited from A/c XX1234. Not you? Call the bank on the number on your card",
    "Your order has been shipped and will arrive by Friday",
]


def risk(msg):
    r = client.post("/analyze", json={"message": msg})
    assert r.status_code == 200
    return r.get_json()["risk"]


@pytest.mark.parametrize("msg", SCAMS)
def test_scams_are_flagged(msg):
    assert risk(msg) in ("medium", "high")


@pytest.mark.parametrize("msg", SAFE)
def test_safe_messages_stay_low(msg):
    assert risk(msg) == "low"


def test_hindi_message_and_explanation():
    r = client.post("/analyze", json={
        "message": "आपका KYC अपडेट नहीं है, खाता बंद हो जाएगा। अभी लिंक पर क्लिक करें http://sbi-kyc.xyz",
        "lang": "hi",
    })
    d = r.get_json()
    assert d["risk"] in ("medium", "high")
    assert any("\u0900" <= ch <= "\u097F" for ch in d["summary"])  # explanation is in Devanagari