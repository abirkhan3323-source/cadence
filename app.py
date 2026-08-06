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

    coaching = _client.coach(transcription, user_context)
    return jsonify({
        "transcription": transcription,
        "coaching": coaching,
        "provider": _client.provider,
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "provider": _client.provider,
    })


if __name__ == "__main__":
    print(f"Provider: {_client.provider}")
    app.run(debug=True, port=5000)
