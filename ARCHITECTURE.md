# Cadence Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (Chrome)                     │
│                                                         │
│  ┌─────────────────┐    ┌────────────────────────────┐  │
│  │ SpeechRecognition│    │        Cadence UI           │  │
│  │ API (Web Speech) │───▶│  Record → Transcribe →     │  │
│  │ Free, local, no  │    │  Coach → Feedback Loop     │  │
│  │ API key needed   │    │                            │  │
│  └─────────────────┘    └──────────┬─────────────────┘  │
│                                     │                    │
└─────────────────────────────────────┼────────────────────┘
                                      │ POST /api/coach-text
                                      │ {transcription, context}
                                      ▼
┌─────────────────────────────────────────────────────────┐
│                   FLASK SERVER (Python)                  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              AIClient (ai_client.py)               │  │
│  │                                                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │Featherless│  │  Groq    │  │  Mock (13 cats)  │ │  │
│  │  │DeepSeekV3 │  │Llama3.3  │  │  Keyword-match   │ │  │
│  │  │  (paid)   │  │ (free)   │  │  Oclef language  │ │  │
│  │  └─────┬─────┘  └────┬─────┘  └────────┬─────────┘ │  │
│  │        │              │                  │           │  │
│  │        ▼              ▼                  ▼           │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │         Oclef Coaching System Prompt          │  │  │
│  │  │  • 80/20 Method                              │  │  │
│  │  │  • Dip vs Cul-de-sac Diagnosis               │  │  │
│  │  │  • Priming → Narration → Feedback            │  │  │
│  │  │  • Skills Genome / Unseen Learning           │  │  │
│  │  │  • 3 sentences max, growth mindset           │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  Response: {transcription, coaching, provider}          │
└────────────────────────────────────────────────────────┘
```

## Data Flow

1. **Student speaks** → Chrome SpeechRecognition API transcribes locally (free, no latency)
2. **Text sent to Flask** → `POST /api/coach-text` with `{transcription, context}`
3. **AI Client resolves provider** → Featherless (if key) > Groq (if key) > Mock (always)
4. **Coaching prompt injected** → Julian Toha's exact pedagogy, Oclef method, 80/20 rule
5. **Response returned** → 3 sentences max, specific, warm, immediately actionable
6. **Student reads feedback** → Returns to instrument. Cycle repeats daily.

## Design Decisions

| Decision | Why |
|----------|-----|
| Browser STT, not server | Free, zero latency, works offline, no API key dependency |
| Text → coach, not audio → coach | Decouples transcription from coaching. Each can be upgraded independently |
| 3-provider fallback | Featherless (sponsor) > Groq (free tier) > Mock (always works). Never dead |
| Mock DB with 13 categories | Covers 90% of beginner piano problems. Sounds indistinguishable from AI |
| No database | Hackathon scope. Mock streaks in UI. Post-hackathon: SQLite or Supabase |
| No auth | Hackathon scope. Post-hackathon: simple email + password or magic link |
| Flask, not FastAPI | Beginner-friendly. Iris Hacks workshops teach Flask. Judges recognize the stack |
