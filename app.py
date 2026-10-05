from flask import Flask, jsonify, render_template, request

import config
from nlp.explainer import analyze
from nlp.ocr import OCRError, extract_text

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_MB * 1024 * 1024

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/analyze")
def analyze_route():
    data = request.get_json(silent=True) or {}
    text = (data.get("message") or "").strip()
    lang = data.get("lang", "en")

    if not text:
        return jsonify(error="Please paste a message first."), 400
    if len(text) > config.MAX_MESSAGE_LENGTH:
        return jsonify(error=f"Message too long (max {config.MAX_MESSAGE_LENGTH} characters)."), 400

    return jsonify(analyze(text, lang))


@app.post("/ocr")
def ocr_route():
    file = request.files.get("image")
    if file is None or not file.filename:
        return jsonify(error="Please choose a screenshot first."), 400
    if file.mimetype not in ALLOWED_IMAGE_TYPES:
        return jsonify(error="Please upload a PNG, JPG or WEBP image."), 415
    try:
        return jsonify(extract_text(file.stream))
    except OCRError as err:
        return jsonify(error=str(err)), 422


@app.errorhandler(413)
def too_large(_):
    return jsonify(error=f"Image is too large (max {config.MAX_UPLOAD_MB} MB)."), 413


if __name__ == "__main__":
    app.run(debug=True)