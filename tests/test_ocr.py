import io

import pytest
from PIL import Image, ImageDraw, ImageFont

from app import app
from nlp.ocr import ocr_ready

client = app.test_client()
needs_tesseract = pytest.mark.skipif(not ocr_ready(), reason="Tesseract is not installed")


def _image_with_text(text):
    img = Image.new("RGB", (1000, 220), "white")
    try:
        font = ImageFont.truetype("arial.ttf", 44)
    except OSError:
        font = ImageFont.load_default(size=44)
    ImageDraw.Draw(img).text((30, 70), text, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf


@needs_tesseract
def test_ocr_reads_text():
    r = client.post(
        "/ocr",
        data={"image": (_image_with_text("Update your KYC now"), "msg.png")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 200
    assert "KYC" in r.get_json()["text"].upper()


def test_ocr_rejects_fake_image():
    r = client.post(
        "/ocr",
        data={"image": (io.BytesIO(b"not an image"), "x.png")},
        content_type="multipart/form-data",
    )
    assert r.status_code in (415, 422)


def test_ocr_requires_file():
    r = client.post("/ocr", data={}, content_type="multipart/form-data")
    assert r.status_code == 400