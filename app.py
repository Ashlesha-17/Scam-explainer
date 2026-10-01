from flask import Flask, jsonify, render_template, request

import config
from nlp.explainer import analyze

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(debug=True)