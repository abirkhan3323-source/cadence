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


@app.route("/api/coach-audio", methods=["POST"])
def coach_audio():
    """
    Audio-based coaching endpoint.
    Accepts recorded piano audio + optional text transcription.
    Server performs basic audio analysis, then feeds metrics to AI coach.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    transcription = data.get("transcription", "").strip()
    context = data.get("context", "")
    audio_b64 = data.get("audio", "")
    audio_mime = data.get("audio_mime", "audio/webm")

    if not audio_b64 and not transcription:
        return jsonify({"error": "No audio or transcription provided"}), 400

    audio_metrics = None
    if audio_b64:
        try:
            audio_metrics = _analyze_audio(audio_b64, audio_mime)
        except Exception:
            audio_metrics = {"error": "Audio analysis failed, using text only"}

    enriched_context = context
    if audio_metrics and "error" not in audio_metrics:
        enriched_context += (
            f"\n[AUDIO ANALYSIS: Volume={audio_metrics.get('rms_level', 'unknown')}, "
            f"Tempo consistency={audio_metrics.get('tempo_consistency', 'unknown')}, "
            f"Tone quality={audio_metrics.get('tone_quality', 'unknown')}, "
            f"Note count={audio_metrics.get('onset_count', 'unknown')}]"
        )

    result = _client.coach(transcription, enriched_context)
    return jsonify({
        "transcription": transcription,
        "coaching": result["coaching"],
        "practice_plan": result["practice_plan"],
        "provider": _client.provider,
        "audio_metrics": audio_metrics,
    })


def _analyze_audio(b64_data: str, mime_type: str = "audio/webm") -> dict:
    """
    Analyze recorded piano audio for basic acoustic metrics.
    Uses wave module for WAV, falls back to heuristic analysis for webm/other.
    """
    import base64
    import io
    import struct
    import wave

    raw = base64.b64decode(b64_data)
    metrics = {"format": mime_type}

    try:
        with wave.open(io.BytesIO(raw), 'rb') as wf:
            n_frames = wf.getnframes()
            framerate = wf.getframerate()
            sample_width = wf.getsampwidth()
            n_channels = wf.getnchannels()
            duration = n_frames / framerate if framerate > 0 else 0

            frames = wf.readframes(min(n_frames, framerate * 30))
            wf.close()

            if sample_width == 2:
                fmt = f"<{len(frames)//2}h"
                samples = struct.unpack(fmt, frames[:len(frames)//2*2])
            elif sample_width == 1:
                samples = [b - 128 for b in frames]
            else:
                samples = []

            if samples:
                squared = [s*s for s in samples]
                rms = (sum(squared) / len(squared)) ** 0.5
                max_amp = max(abs(s) for s in samples)
                rms_norm = min(100, round((rms / 32768) * 100)) if sample_width == 2 else min(100, round((rms / 128) * 100))

                zcr = 0
                for i in range(1, len(samples)):
                    if (samples[i] >= 0) != (samples[i-1] >= 0):
                        zcr += 1
                zcr_rate = zcr / len(samples) if samples else 0

                onsets = 0
                threshold = rms * 1.5
                above = False
                for s in samples:
                    if abs(s) > threshold and not above:
                        onsets += 1
                        above = True
                    elif abs(s) <= threshold * 0.5:
                        above = False

                metrics.update({
                    "duration_seconds": round(duration, 1),
                    "sample_rate": framerate,
                    "rms_level": f"{rms_norm}%",
                    "zero_crossing_rate": round(zcr_rate, 4),
                    "onset_count": onsets,
                    "tempo_consistency": "steady" if onsets > 0 and onsets < duration * 4 else "variable",
                    "tone_quality": "bright" if rms_norm > 50 else "warm" if rms_norm > 20 else "soft",
                })
    except Exception:
        metrics.update({
            "duration_seconds": round(len(raw) / 16000, 1),
            "rms_level": f"{min(100, max(5, len(raw) // 1000))}%",
            "tempo_consistency": "unknown (non-WAV format)",
            "tone_quality": "unknown (non-WAV format)",
            "onset_count": max(1, len(raw) // 8000),
            "note": "Audio recorded. Full analysis requires WAV format or server-side conversion.",
        })

    return metrics


if __name__ == "__main__":
    print(f"Provider: {_client.provider}")
    app.run(debug=False, port=5000)
