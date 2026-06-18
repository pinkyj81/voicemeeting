from flask import Flask, jsonify, render_template, request
from deep_translator import GoogleTranslator
import os

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/iphone")
def iphone():
    return render_template("iphone.html")


@app.post("/api/translate")
def translate_text():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    source_lang = str(payload.get("source", "")).strip().lower()
    target_lang = str(payload.get("target", "")).strip().lower()

    allowed = {"ko", "ja"}
    if not text:
        return jsonify({"error": "text is required"}), 400
    if source_lang not in allowed or target_lang not in allowed:
        return jsonify({"error": "source/target must be ko or ja"}), 400

    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translated = translator.translate(text)
    except Exception as exc:
        return jsonify({"error": f"translation failed: {exc}"}), 500

    return jsonify({"translated_text": translated})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5055))
    debug = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
