"""
Cadence — AI Music Coach
Voice-driven practice companion. Student describes their practice.
AI coach responds with personalized, Oclef-method feedback.

Priority: Featherless API > Groq (free tier) > Mock (keyword-match)
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from ai_client import get_client
import numpy as np

app = Flask(__name__)
CORS(app)

_client = get_client()


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/favicon.ico")
@app.route("/favicon.png")
def favicon():
    return send_from_directory("static", "favicon.png", mimetype="image/png")


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
        except (ValueError, OSError, RuntimeError) as e:
            audio_metrics = {"error": f"Audio analysis failed ({type(e).__name__}), using text only"}

    enriched_context = context
    if audio_metrics and audio_metrics.get("success"):
        m = audio_metrics
        quality = m.get("signal_quality", "good")

        if quality in ("silence", "poor"):
            # ── NO MEANINGFUL MUSIC DETECTED ──
            enriched_context += (
                f"\n\n[🎹 AUDIO RECEIVED — BUT NO MEANINGFUL PIANO PLAYING WAS DETECTED]"
                f"\n- Signal quality: {quality.upper()}"
                f"\n- Notes detected: {m.get('note_count', 0)} (likely noise artifacts)"
                f"\n- Duration: {m.get('duration_seconds', 0)}s"
                f"\n\n⚠️ CRITICAL INSTRUCTION: You did NOT hear any real piano playing. "
                f"The student may have recorded silence, background noise, or non-piano sounds. "
                f"DO NOT fabricate feedback about notes, mistakes, rhythm, or technique — "
                f"there is no musical data to analyze. "
                f"Tell the student honestly that you couldn't hear any piano playing, "
                f"and ask them to record again while playing something on the piano."
            )
        else:
            notes = ", ".join(m.get("detected_notes", [])[:15])
            enriched_context += (
                f"\n\n[🎹 LIVE AUDIO ANALYSIS — You just HEARD the student play:]"
                f"\n- Notes detected: {notes}"
                f"\n- Total notes: {m.get('note_count', 0)}"
                f"\n- Tempo: ~{m.get('tempo_bpm', '?')} BPM"
                f"\n- Hesitations detected: {m.get('hesitation_count', 0)}"
                f"\n- Off-pitch notes (30+ cents): {m.get('off_pitch_notes', 0)}"
                f"\n- Duration: {m.get('duration_seconds', 0)}s"
                f"\n- Musical summary: {m.get('musical_summary', '')}"
                f"\n\nIMPORTANT: Reference these specific notes in your coaching. "
                f"If there are hesitations or off-pitch notes, point them out specifically. "
                f"Tell the student exactly WHICH notes need work and what to practice next."
                f"\nYou HEARD them play — respond as if you were sitting next to them at the piano."
            )
    elif audio_metrics and audio_metrics.get("error"):
        enriched_context += f"\n[Audio was recorded but analysis failed: {audio_metrics['error']}]"

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
    Analyze piano audio: FFT pitch detection, note identification,
    onset timing, tempo estimation, hesitation detection.
    """
    import base64
    import io
    import struct
    import wave

    raw = base64.b64decode(b64_data)
    metrics: dict = {"format": mime_type, "success": False}

    decoded = _decode_wav(raw)
    if decoded is None:
        metrics.update({
            "duration_seconds": round(len(raw) / 16000, 1),
            "note": "Audio received but could not decode to WAV. Try recording again.",
            "detected_notes": [],
            "tempo_bpm": 0,
            "hesitation_count": 0,
        })
        return metrics

    samples, sr = decoded
    duration = len(samples) / sr
    metrics["duration_seconds"] = round(duration, 1)
    metrics["success"] = True

    # ── FFT-based note detection ──
    window_size = 4096
    hop_size = window_size // 2
    note_names = _note_names()

    detected_notes = []
    onset_times = []
    prev_freq = 0
    silence_threshold = 0.03  # normalized: room noise ~0.001-0.01, quiet playing ~0.03+

    # ── Overall signal check: if nearly all windows are silent, flag it ──
    total_windows = 0
    active_windows = 0

    for start in range(0, len(samples) - window_size, hop_size):
        window = np.array(samples[start:start + window_size], dtype=np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(window ** 2)))
        total_windows += 1

        if rms < silence_threshold:
            continue  # silence

        active_windows += 1

        # Hann window + FFT
        hann = 0.5 * (1 - np.cos(2 * np.pi * np.arange(window_size) / (window_size - 1)))
        fft = np.abs(np.fft.rfft(window * hann))
        freqs = np.fft.rfftfreq(window_size, 1.0 / sr)

        # Find dominant frequency in piano range (27.5 Hz A0 — 4186 Hz C8)
        mask = (freqs >= 27.5) & (freqs <= 4200)
        if not np.any(mask):
            continue
        peak_idx = int(np.argmax(fft[mask]))
        peak_freq = float(freqs[mask][peak_idx])
        peak_mag = float(fft[mask][peak_idx])

        if peak_mag < 15:
            continue

        # ── Harmonic structure check: is this a piano note or noise/voice? ──
        if not _is_piano_like(fft, freqs, peak_freq, sr):
            continue  # voice hum, tap, or broadband noise — not a piano note

        # Map frequency to note
        midi = 69 + 12 * np.log2(peak_freq / 440.0)
        midi_note = int(round(midi))
        note_name = note_names[midi_note % 12] + str(midi_note // 12 - 1)
        cents_off = int(round(100 * (midi - midi_note)))

        # Detect onset (new note started)
        if abs(peak_freq - prev_freq) > peak_freq * 0.05 or not detected_notes:
            onset_time = start / sr
            detected_notes.append({
                "note": note_name,
                "freq_hz": round(peak_freq, 1),
                "cents_off": cents_off,
                "time_sec": round(onset_time, 1),
                "velocity": round(min(100, rms * 1000), 1),
            })
            onset_times.append(onset_time)
            prev_freq = peak_freq

    # ── Deduplicate adjacent repeated notes ──
    unique_notes = []
    for n in detected_notes:
        if not unique_notes or unique_notes[-1]["note"] != n["note"]:
            unique_notes.append(n)
    detected_notes = unique_notes

    # ── Tempo estimation from onsets ──
    tempo_bpm = 0
    if len(onset_times) >= 3:
        iois = [onset_times[i+1] - onset_times[i] for i in range(len(onset_times)-1)]
        iois = [i for i in iois if 0.15 < i < 3.0]  # filter outliers
        if iois:
            median_ioi = float(np.median(iois))
            tempo_bpm = int(round(60.0 / median_ioi)) if median_ioi > 0 else 0

    # ── Hesitation detection ──
    hesitations = 0
    if len(onset_times) >= 2:
        for i in range(1, len(onset_times)):
            gap = onset_times[i] - onset_times[i-1]
            if gap > 1.5:  # gap > 1.5 seconds = hesitation
                hesitations += 1

    # ── Note sequence analysis ──
    played_sequence = [n["note"] for n in detected_notes]
    off_notes = [n for n in detected_notes if abs(n["cents_off"]) > 30]

    # ── Build musical summary ──
    note_list = ", ".join(played_sequence[:12])
    if len(played_sequence) > 12:
        note_list += f" ... ({len(played_sequence)} notes total)"

    # ── Signal quality assessment ──
    signal_ratio = active_windows / max(total_windows, 1)
    if signal_ratio < 0.05:
        quality = "silence"       # effectively no playing detected
    elif signal_ratio < 0.10:
        quality = "poor"          # very little signal — likely noise
    elif len(played_sequence) == 0:
        quality = "poor"          # signal present but no piano-like notes found
    else:
        quality = "good"

    metrics.update({
        "detected_notes": played_sequence,
        "note_count": len(played_sequence),
        "tempo_bpm": tempo_bpm,
        "hesitation_count": hesitations,
        "off_pitch_notes": len(off_notes),
        "signal_quality": quality,
        "velocity_range": f"{min(n['velocity'] for n in detected_notes) if detected_notes else 0}-{max(n['velocity'] for n in detected_notes) if detected_notes else 0}%",
        "musical_summary": f"Detected {len(played_sequence)} notes: {note_list}. Tempo: ~{tempo_bpm} BPM. Hesitations: {hesitations}. Off-pitch notes: {len(off_notes)}.",
    })

    return metrics


def _decode_wav(raw: bytes) -> tuple | None:
    """Decode WAV bytes to (samples, sample_rate). Returns None on failure."""
    import io
    import struct
    import wave

    try:
        with wave.open(io.BytesIO(raw), 'rb') as wf:
            n_frames = wf.getnframes()
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            n_channels = wf.getnchannels()

            frames = wf.readframes(min(n_frames, sample_rate * 30))

            if sample_width == 2:
                fmt = f"<{len(frames)//2}h"
                raw_samples = struct.unpack(fmt, frames[:len(frames)//2*2])
            elif sample_width == 1:
                raw_samples = [b - 128 for b in frames]
            else:
                return None

            # Convert to mono float if multi-channel
            if n_channels > 1:
                mono = []
                for i in range(0, len(raw_samples), n_channels):
                    mono.append(raw_samples[i])
                raw_samples = mono

            return (list(raw_samples), sample_rate)
    except (struct.error, wave.Error, EOFError, OSError, ValueError):
        return None


def _note_names() -> list:
    """Return list of 12 note names starting from C."""
    return ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _is_piano_like(fft_magnitudes: np.ndarray, freqs: np.ndarray, fundamental: float,
                   sr: int = 44100) -> bool:
    """
    Check whether a detected peak has piano-like harmonic structure.

    A real piano note has energy distributed across multiple harmonics
    (2f, 3f, 4f, 5f) with characteristic decay. Voice/humming has energy
    concentrated in the fundamental (pure tone). Taps/clicks have broadband
    noise with no clear harmonic series.

    Returns True if the spectrum looks like a struck string, not a voice or noise.
    """
    # Collect energy at harmonic positions (1f through 5f)
    harmonic_energies = []
    nyquist = sr / 2

    for h in range(1, 6):
        target = fundamental * h
        if target >= nyquist:
            break
        # Find bins within ±3.5% of harmonic target (accounts for inharmonicity)
        mask = (freqs >= target * 0.965) & (freqs <= target * 1.035)
        if not np.any(mask):
            break
        harmonic_energies.append(float(np.max(fft_magnitudes[mask])))

    # Need at least 3 detectable harmonics for a piano-like sound
    if len(harmonic_energies) < 3:
        return False

    total_harmonic = sum(harmonic_energies)

    # Criterion 1: fundamental shouldn't dominate (>75% = too pure, likely voice/whistle)
    fundamental_ratio = harmonic_energies[0] / total_harmonic if total_harmonic > 0 else 1.0
    if fundamental_ratio > 0.75:
        return False

    # Criterion 2: energy should decay across harmonics (piano characteristic)
    # Check that h2 <= h1 * 0.9 (second harmonic ≤ 90% of fundamental)
    if len(harmonic_energies) >= 2:
        if harmonic_energies[1] > harmonic_energies[0] * 0.95:
            return False  # second harmonic stronger than fundamental — not piano

    # Criterion 3: check harmonic energy is a meaningful fraction of total spectrum
    # Get total energy across piano range (27.5Hz - 4200Hz)
    piano_mask = (freqs >= 27.5) & (freqs <= 4200)
    total_spectral = float(np.sum(fft_magnitudes[piano_mask] ** 2))
    harmonic_power = sum(e ** 2 for e in harmonic_energies)

    if total_spectral > 0 and harmonic_power / total_spectral < 0.15:
        return False  # harmonic energy is drowned in noise — likely percussive/ambient

    return True


if __name__ == "__main__":
    print(f"Provider: {_client.provider}")
    app.run(debug=False, port=5000)
