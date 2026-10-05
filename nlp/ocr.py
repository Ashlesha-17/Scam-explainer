import os
import re
from functools import lru_cache
from pathlib import Path

import pytesseract
from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError
from pytesseract import Output

import config

Image.MAX_IMAGE_PIXELS = 40_000_000  # refuse absurdly large images

_cmd = Path(config.TESSERACT_CMD) if config.TESSERACT_CMD else None
if _cmd and _cmd.exists():
    pytesseract.pytesseract.tesseract_cmd = str(_cmd)
    _tessdata = _cmd.parent / "tessdata"
    if _tessdata.exists():
        # Overrides a wrong TESSDATA_PREFIX inherited from another program
        os.environ["TESSDATA_PREFIX"] = str(_tessdata)

TIME_ONLY = re.compile(r"^\W*\d{1,2}[:.]\d{2}\s*(?:am|pm)?\W*$", re.I)
TRAILING_TIME = re.compile(r"\s+\d{1,2}[:.]\d{2}\s*(?:am|pm)\s*\W*$", re.I)


class OCRError(Exception):
    """Raised with a message that is safe to show to the user."""


def ocr_ready() -> bool:
    try:
        pytesseract.get_tesseract_version()
        return True
    except pytesseract.TesseractNotFoundError:
        return False


@lru_cache(maxsize=1)
def _languages():
    wanted = config.OCR_LANGS.split("+")
    raw = pytesseract.get_languages(config="")
    # Split on any line ending, since Windows output can use \r\n or \n
    installed = {ln.strip() for ln in re.split(r"[\r\n]+", "\n".join(raw)) if ln.strip()}
    used = [lang for lang in wanted if lang in installed]
    missing = [lang for lang in wanted if lang not in installed]
    if not used:
        raise OCRError(
            "No OCR language data found. Tesseract reported: "
            + (", ".join(sorted(installed)) or "nothing")
            + ". Install the English and Hindi language data."
        )
    return used, missing


def _prepare(img: Image.Image) -> Image.Image:
    """Make a phone screenshot easier for Tesseract to read."""
    img = ImageOps.exif_transpose(img).convert("L")
    if ImageStat.Stat(img).mean[0] < 110:      # dark-mode chat: flip to dark text on light
        img = ImageOps.invert(img)
    w, h = img.size
    if w < 1200:                               # small screenshots read better when enlarged
        scale = 1200 / w
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    return ImageOps.autocontrast(img)


def _clean(text: str) -> str:
    """Drop WhatsApp timestamps that OCR picks up."""
    lines = []
    for line in text.splitlines():
        if TIME_ONLY.match(line):
            continue
        lines.append(TRAILING_TIME.sub("", line).strip())
    return "\n".join(l for l in lines if l).strip()


def extract_text(stream) -> dict:
    try:
        img = Image.open(stream)
        img.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError):
        raise OCRError("Could not open this file as an image. Please upload a PNG, JPG or WEBP screenshot.")

    img = _prepare(img)

    try:
        used, missing = _languages()
        data = pytesseract.image_to_data(
            img,
            lang="+".join(used),
            config=f"--psm {config.OCR_PSM}",
            output_type=Output.DICT,
            timeout=30,
        )
    except pytesseract.TesseractNotFoundError:
        raise OCRError("Tesseract OCR is not installed, or its path is wrong (check TESSERACT_CMD in config.py).")
    except (pytesseract.TesseractError, RuntimeError):
        raise OCRError("The OCR engine could not read this image. Try a clearer or smaller screenshot.")

    # Rebuild text paragraph by paragraph so wrapped chat lines become one sentence
    paragraphs, confs = {}, []
    for i, raw in enumerate(data["text"]):
        word = raw.strip()
        if not word:
            continue
        paragraphs.setdefault((data["block_num"][i], data["par_num"][i]), []).append(word)
        conf = float(data["conf"][i])
        if conf >= 0:
            confs.append(conf)

    text = _clean("\n".join(" ".join(words) for _, words in sorted(paragraphs.items())))
    if not text:
        raise OCRError("No text was found in this screenshot. Try a sharper image or crop to the message.")

    confidence = sum(confs) / len(confs) if confs else 0.0
    notes = []
    if missing:
        notes.append(f"OCR language data missing for: {', '.join(missing)}. Hindi text will not be read correctly.")
    if len(text) < config.OCR_MIN_CHARS:
        notes.append("Very little text was found. Please check it below.")
    elif confidence < config.OCR_MIN_CONFIDENCE:
        notes.append("The screenshot was hard to read. Please check the text below and fix any mistakes, then press Analyze.")

    return {
        "text": text[: config.MAX_MESSAGE_LENGTH],
        "confidence": round(confidence, 1),
        "warning": " ".join(notes) or None,
    }