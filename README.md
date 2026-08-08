<h1 align="center">
  <img src="https://raw.githubusercontent.com/abirkhan3323-source/cadence/master/static/cadence-logo.svg" width="300" alt="Cadence — AI Piano Coach" />
</h1>

<p align="center">
  <strong>Your daily AI piano teacher. Listens to your playing, hears every note,<br/> and tells you exactly what to fix — in three sentences or less.</strong>
</p>

<p align="center">
  <a href="https://web-production-fb735.up.railway.app"><img src="https://img.shields.io/badge/LIVE-Demo-gold?style=for-the-badge&logo=railway" alt="Live Demo" /></a>
  <a href="https://github.com/abirkhan3323-source/cadence"><img src="https://img.shields.io/badge/GitHub-Repo-black?style=for-the-badge&logo=github" alt="GitHub" /></a>
  <br/>
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/Flask-3.0-green?logo=flask" alt="Flask" />
  <img src="https://img.shields.io/badge/AI-Groq%20%7C%20Featherless-purple?logo=openai" alt="AI" />
  <img src="https://img.shields.io/badge/DSP-NumPy%20FFT-orange?logo=numpy" alt="DSP" />
  <img src="https://img.shields.io/badge/Deploy-Railway-8B2BE2?logo=railway" alt="Railway" />
</p>

<br/>

> **Live Demo:** [https://web-production-fb735.up.railway.app](https://web-production-fb735.up.railway.app)

---

## 🎯 The Problem

**83% of music students quit.** Not because they lack talent — because they wait 7 days between lessons. A week is long enough for bad habits to calcify and motivation to evaporate. Private lessons cost $60+/week, putting quality music education out of reach for millions.

Julian Toha, founder of Oclef (the largest online piano school in the US), proved that **daily feedback** — not accumulated practice hours — determines success. His 91% student success rate vs. the 17% industry average proves the model works.

**Cadence delivers that daily feedback loop, powered by AI, accessible to anyone with a phone.**

---

## 🧠 What It Does

| Feature | Detail |
|---------|--------|
| 🎹 **Live Audio Analysis** | Records your piano playing, runs real-time FFT note detection, identifies every note you played |
| 🔬 **Harmonic Structure Check** | Distinguishes real piano notes from voice, humming, taps, and room noise — no false positives |
| 📄 **Sheet Music Scanning** | Upload a photo of your sheet music — Groq Vision AI analyzes key, time signature, hardest section, and practice strategy |
| 🎙️ **Voice + Audio Combo** | Talk about your practice AND let the AI hear you play — it references specific notes in its feedback |
| 🧠 **Oclef Pedagogy** | 80/20 method — isolates the ONE most important thing. Never cognitive overload. Julian Toha's exact coaching philosophy |
| 🔥 **Progress Tracking** | 7-day practice streak, XP points, achievement badges, activity heatmap |
| ⏱️ **Kaizen Timer** | Built-in 15-minute focused practice timer — "small daily improvements compound into mastery" |
| 👤 **Persona Selector** | Choose your Oclef developmental stage (Learn to Read → Learn to Practice → Learn to Perform → Learn to Build) |
| 🎨 **Concert Hall at Midnight** | Piano-black & ivory design system, floating note particles, gold accents, 13 CSS animations |

---

## 🎼 How the Note Detection Works

```
Browser Microphone
    │
    ▼
MediaRecorder API → Blob
    │
    ▼
AudioContext.decodeAudioData()
    │
    ▼
PCM Float32 → Int16 → WAV Header
    │
    ▼
POST /api/coach-audio (base64 WAV)
    │
    ▼
Server: numpy FFT (4096-sample windows, Hann windowing, 50% overlap)
    │
    ▼
Peak frequency → MIDI formula → Note name
    midi = 69 + 12 × log₂(freq / 440.0)
    note = names[midi % 12] + str(midi // 12 - 1)
    │
    ▼
_is_piano_like() harmonic structure check:
    ✓ 3+ detectable harmonics required
    ✓ Fundamental ratio < 75% (rejects pure tones / humming)
    ✓ Harmonic energy > 15% of total spectrum (rejects noise / taps)
    │
    ▼
Enriched context → Groq Llama 3.3 70B → Oclef coaching
```

**Detection range:** A0 (27.5 Hz) — C8 (4186 Hz) · **Tempo estimation:** median inter-onset interval · **Hesitation detection:** gaps > 1.5s between onsets · **Pitch accuracy:** ±30 cents threshold

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (SPA)                        │
│  SpeechRecognition API  │  MediaRecorder API  │  Canvas  │
│  Persona Selector       │  Kaizen Timer       │  Upload  │
└────────────────────────────┬────────────────────────────┘
                             │
                    Flask REST API
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   /api/coach-text    /api/coach-audio    /api/scan-sheet
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  AI Coach     │   │  FFT Analysis │   │  Groq Vision  │
│               │   │  - Note ID    │   │  Llama 3.2    │
│  3-Tier       │   │  - Tempo      │   │  90B Vision   │
│  Fallback:    │   │  - Harmonics  │   │  Preview       │
│  Demo Cache   │   │  - Pitch      │   │               │
│  → Featherless│   │               │   │  Fallback:     │
│  → Groq       │   │               │   │  Mock Analysis │
│  → Mock       │   │               │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
```

**AI Fallback Chain:** Demo Cache (keyword-match with 2+ keyword threshold) → Featherless (DeepSeek V3) → Groq (Llama 3.3 70B) → Mock (13-category coaching database with rotation)

**Demo cache is automatically bypassed when audio analysis is present** — the AI always sees real note data, never cached responses.

---

## 🎨 Design System

| Token | Value | Usage |
|-------|-------|-------|
| `--piano-black` | `#0a0a0c` | Page background |
| `--piano-deep` | `#141418` | Card backgrounds |
| `--ivory` | `#f5f1e8` | Primary text |
| `--gold` | `#c8a84e` | Accents, borders, hover states |
| `--gold-bright` | `#e8c854` | Key highlights, coaching response headers |

**Animations:** `floatNote` (CSS radial-gradient particles), `cardSlideIn`, `dotPulse`, `neuralPulse` (sheet music loading), `pulseBorder`, `onboardSlideIn`, gold glow effects on streak banner and badges.

**Typography:** Playfair Display (headings) + Inter (body) via Google Fonts.

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12 · Flask 3.0 · Gunicorn |
| **Audio DSP** | NumPy FFT · Hann windowing · MIDI frequency mapping |
| **AI** | Groq (Llama 3.3 70B text, Llama 3.2 90B Vision) · Featherless (DeepSeek V3) |
| **Frontend** | Vanilla HTML/CSS/JS · Web Speech API · MediaRecorder API · AudioContext |
| **Deployment** | Railway · GitHub |
| **Browser APIs** | SpeechRecognition · AudioContext.decodeAudioData · localStorage |

---

## 🚀 Quick Start

```bash
git clone https://github.com/abirkhan3323-source/cadence.git
cd cadence
pip install -r requirements.txt

# Create .env with your API keys
echo 'GROQ_API_KEY=gsk_your_key_here' > .env

python app.py
# → http://localhost:5000
```

---

## 🏆 Iris Hacks IV

Built solo in 24 hours for Iris Hacks IV (August 2026).

**What makes it different:**
- **Actually hears notes** — not just generic audio metrics. FFT pitch detection identifies specific wrong notes
- **Won't lie to you** — harmonic structure analysis distinguishes piano from voice/taps/noise. No fabricated feedback on silence
- **Pedagogy-first** — 11-rule coaching system prompt based on Julian Toha's Oclef method. Three sentences max. One thing to fix. Every time
- **Never breaks** — 3-tier AI fallback chain. The app always responds, even without API keys

---

## 🔮 The Vision

Music education is a feedback-loop problem. The 7-day gap between lessons is the bottleneck. Cadence closes it to 7 seconds. Every practice session becomes a lesson. Every mistake becomes data. Every student — regardless of income — gets a world-class piano coach in their pocket.

*"The instrument is the gym. Every practice session builds neural pathways through unseen learning." — Julian Toha*
