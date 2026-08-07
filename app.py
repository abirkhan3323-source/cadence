"""
Cadence — AI Music Coach
Voice-driven practice companion. Student describes their practice.
AI coach responds with personalized, Oclef-method feedback.

Priority: Featherless API > Groq (free tier) > Mock (keyword-match)
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from ai_client import get_client

app = Flask(__name__)
CORS(app)

_client = get_client()


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/api/coach-text", methods=["POST"])
def coach_text():
    """
    Text-based coaching endpoint.
    Browser handles speech-to-text via Web Speech API (free, local).
    Server handles AI coaching only.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    transcription = data.get("transcription", "").strip()
    user_context = data.get("context", "")

    if not transcription:
        return jsonify({"error": "No transcription provided"}), 400

    result = _client.coach(transcription, user_context)
    return jsonify({
        "transcription": transcription,
        "coaching": result["coaching"],
        "practice_plan": result["practice_plan"],
        "provider": _client.provider,
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "provider": _client.provider,
    })


@app.route("/api/scan-sheet", methods=["POST"])
def scan_sheet():
    """
    Analyze a sheet music photo via AI vision or mock fallback.
    Accepts base64-encoded image + filename.
    Returns {analysis: string}.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    image_b64 = data.get("image", "")
    filename = data.get("filename", "sheet.jpg")

    if not image_b64:
        return jsonify({"error": "No image provided"}), 400

    result = _client.scan_sheet(image_b64, filename)
    return jsonify({
        "analysis": result["analysis"],
        "provider": _client.provider,
    })


if __name__ == "__main__":
    print(f"Provider: {_client.provider}")
    app.run(debug=True, port=5000)
