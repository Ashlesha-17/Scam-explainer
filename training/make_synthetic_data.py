import csv
import random
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
import config

random.seed(42)

BANKS = ["SBI", "HDFC", "ICICI", "Axis Bank", "PNB", "Kotak"]
BRANDS = ["Jio", "Amazon", "Flipkart", "Paytm"]
LINKS = [
    "http://sbi-kyc-update.xyz/verify", "bit.ly/3kycNow", "http://hdfc-secure.top/login",
    "www.paytm-kyc.info/update", "http://192.168.4.21/refund",
]
AMTS = ["500", "2,000", "5,000", "10,000", "49,999"]

TEMPLATES = {
    "fake_kyc": [
        "Dear customer, your {bank} account will be blocked today. Update KYC immediately: {link}",
        "{bank} alert: aapka KYC expire ho gaya hai. Account band ho jayega. Abhi update karo {link}",
        "Aapka PAN card update nahi hai, 24 ghante me account block ho jayega. Click {link} aur OTP share karo",
        "Sir main {bank} se bol raha hu, KYC pending hai. Aadhaar number aur OTP bata do warna account freeze",
        "KYC updt krna hai nhi to {bank} acc blck ho jayega, link: {link}",
    ],
    "payment_trap": [
        "Sir galti se aapke account me Rs {amt} chale gaye, please wapas bhej do",
        "Accept the collect request of Rs {amt} to receive your refund",
        "Aapka refund Rs {amt} aane wala hai. Scan this QR code aur UPI PIN dalo to receive money",
        "Bhai maine galti se {amt} rupees bhej diye, request approve kar do wapas aa jayenge",
        "Refund of Rs {amt} initiated. Click {link} and enter UPI PIN to receive",
    ],
    "lottery_prize": [
        "Congratulations! You have won Rs 25,00,000 in KBC lucky draw. Call now to claim prize, pay processing fee",
        "Aapne {brand} lucky draw jeeta hai! Inaam claim karne ke liye {link} pe click karo",
        "Winner! Free iPhone for you. Pay Rs {amt} delivery charge to claim gift",
    ],
    "job_offer": [
        "Work from home job! Earn Rs {amt} per day, just like and subscribe videos. Registration fee Rs 500. WhatsApp now",
        "Part time job offer: ghar baithe kamao Rs {amt} daily. Simple tasks, join karo {link}",
        "Hello, we are hiring for data entry. Joining fee Rs {amt}, salary 30000 per month. Contact HR on WhatsApp {phone}",
    ],
    "utility_threat": [
        "Dear consumer, aapka bijli bill update nahi hua, aaj raat 9:30 baje connection disconnect ho jayega. Call {phone} immediately",
        "Your SIM will be deactivated in 2 hours. KYC pending. Click {link}",
        "Electricity board: last month ka bill pending hai, power cut hoga. Contact officer {phone} abhi",
    ],
    "safe": [
        "Your OTP is {otp}. Do not share it with anyone. -{bank}",
        "Rs {amt} debited from A/c XX{last4}. Not you? Call the bank on the number on your card",
        "Bhai kal milte hai 5 baje, paise UPI kar diye hai",
        "Your order has been shipped and will arrive by Friday",
        "Rs {amt} credited to your account via UPI from Rahul",
        "Mom: Aaj dinner ke liye kya banau?",
        "Your electricity bill of Rs {amt} is generated. Pay by due date via the official app",
        "Hi, aapka interview kal 11 baje hai. Please carry your documents",
        "{otp} is your OTP for login. Never share it. -{brand}",
    ],
}


def fields():
    return {
        "bank": random.choice(BANKS),
        "brand": random.choice(BRANDS),
        "link": random.choice(LINKS),
        "amt": random.choice(AMTS),
        "phone": "98" + "".join(random.choices("0123456789", k=8)),
        "otp": "".join(random.choices("0123456789", k=6)),
        "last4": "".join(random.choices("0123456789", k=4)),
    }


def noise(s):
    out = []
    for w in s.split():
        if random.random() < 0.08 and w.isalpha() and len(w) > 4:
            w = w[0] + "".join(c for c in w[1:] if c.lower() not in "aeiou")
        out.append(w)
    s = " ".join(out)
    if random.random() < 0.3:
        s = s.lower()
    if random.random() < 0.15:
        s += " 🙏"
    return s


rows = set()
for label, templates in TEMPLATES.items():
    for _ in range(200):
        rows.add((noise(random.choice(templates).format(**fields())), label))

rows = list(rows)
random.shuffle(rows)
config.DATASET_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(config.DATASET_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["text", "label"])
    w.writerows(rows)
print(f"Wrote {len(rows)} rows to {config.DATASET_CSV}")