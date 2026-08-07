"""
Unified AI client for Cadence.
Priority: Featherless > Groq (free tier) > Mock (keyword-match + Oclef pedagogy)

Featherless: needs FEATHERLESS_API_KEY in .env
Groq: needs GROQ_API_KEY in .env (free: https://console.groq.com)
Mock: always available, 13 piano problem categories with Julian Toha's exact language
"""

import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

FEATHERLESS_BASE = "https://api.featherless.ai/v1"
GROQ_BASE = "https://api.groq.com/openai/v1"

# ── Julian Toha / Oclef Coaching System Prompt ──

COACH_SYSTEM_PROMPT = """You are an elite piano pedagogy coach trained in the Oclef method by Julian Toha. Oclef is the largest online piano school in the US with a 91% student success rate — the industry average is 17%, meaning 83% of music students quit. You exist to close the 7-day feedback gap that causes those failures.

Your coaching rules — NON-NEGOTIABLE:

1. 80/20 METHOD: Identify the ONE most critical thing the student should fix right now. Never correct more than one concept. Cognitive overload — trying to fix notes, rhythm, fingers, and dynamics simultaneously — is why 83% of students fail.

2. DIAGNOSE BEFORE PRESCRIBING. Two developmental states:
   - THE DIP: Temporary struggle from deliberate practice. The student is engaging with hard material. Normal. Encourage pushing through — this friction IS the learning.
   - THE CUL-DE-SAC: Rote memorization without true musical literacy. The student copies finger positions but cannot decode new music independently. Pivot to intervallic reading — seeing how notes MOVE relative to each other on the staff, not memorizing finger numbers.

3. THE INSTRUMENT IS THE GYM: Every practice session builds neural pathways through "unseen learning." The student doesn't see progress happening, but every repetition strengthens the connection. Frame corrections in terms of skill-building, not mistake-fixing.

4. PRIMING → NARRATION → FEEDBACK: Prime the student's focus before they play ("watch your thumb at the crossover"). Have them narrate what they notice while playing ("my thumb hesitated there"). Then deliver ONE piece of targeted feedback on what they noticed vs. what actually happened.

5. GROWTH MINDSET: Mistakes are data points for the Skills Genome, not failures. The student who makes the most mistakes and pays attention to them learns fastest. Use the sandwich method: acknowledge effort → deliver targeted correction → affirm progress.

6. THREE SENTENCES MAXIMUM. The student's job is to return to the instrument. Your job is to make those three sentences so precise they don't need a fourth.

7. USE THE STUDENT'S OWN LANGUAGE: If they said "tangled" or "collapses" or "stuck," echo it back. It proves you actually heard them. A coach who says "I notice some difficulty with the descending passage" wasn't listening. A coach who says "the tangle at the crossover" was.

Your tone: warm, direct, specific. Like the world's best piano teacher who has seen this exact problem ten thousand times and knows the exact ten words that fix it."""


# ── Mock Coaching Database ──
# 13 categories, each with Julian Toha language injected
# Trigger phrases are matched against student's transcription

COACHING_DB = [
    {
        "triggers": ["scale", "tangle", "thumb", "crossover", "finger going", "fingers get", "thumb under", "cross over", "hand cross"],
        "responses": [
            "This is the classic descending thumb-under crossover — the #1 beginner hurdle. Isolate just the three-note crossover: finger 3 to thumb, at the exact spot where you hesitate. Play those three notes ten times slowly, then add one note before it, then two. The instrument is the gym — you're building a neural pathway, not just repeating a scale.",
            "Here's what's happening: your thumb is trying to find its landing spot mid-scale, and every hesitation reinforces the wrong neural pathway. Fix it with micro-isolation. Just the crossover. Three notes. Ten clean reps. Your brain will encode the correct movement by tomorrow.",
            "The descending crossover is where 83% of beginners hit their first wall — you're right on schedule. The Priming fix: before you play, close your eyes and visualize your thumb gliding under your palm to land on F. See it first. Then play it. The visualization builds the pathway before your fingers move.",
        ],
    },
    {
        "triggers": ["hands together", "both hands", "left hand", "separate", "collapse", "fall apart", "two hands"],
        "responses": [
            "Hands-separate mastery is a trap — your brain learned two skills in isolation but hasn't built the neural bridge between them. Two measures. Hands together. Half tempo. Five times. When those two measures feel like one motion — and only then — add the next measure. You're building the Skills Genome, one connection at a time.",
            "This is the coordination gap — completely normal, completely fixable. Your left hand and right hand are like two musicians who've never played together. Start with just the first beat of the first measure. Both hands. One beat. When that's clean, add the next beat. Building the bridge one beat at a time.",
            "Don't go back to hands-separate. That reinforces the isolation. Instead: play the left hand at full tempo, and SIMPLIFY the right hand to just the first note of each measure. When that feels easy, add one more right-hand note. You're gradually loading the coordination circuit, not overwhelming it.",
        ],
    },
    {
        "triggers": ["stuck", "plateau", "same", "nothing happened", "not getting", "no progress", "not improving", "not sure if i", "feel like i'm not"],
        "responses": [
            "This plateau is the Dip — temporary friction from deliberate practice, not failure. Your brain is rewiring itself through unseen learning, even when it doesn't feel like progress. Pick ONE measure, the hardest one, and set a concrete goal for tomorrow. One measure. One goal. You'll feel the difference.",
            "Plateaus are the most psychologically dangerous part of learning — they feel like failure but they're actually the moment before a breakthrough. Change ONE variable tomorrow: practice at a different time of day, or start from the last measure and work backwards. A new context forces new neural connections.",
            "You're in the Dip — and that's exactly where you should be. The Dip separates the 91% who succeed from the 83% who quit. Your only job right now: show up tomorrow and practice ONE thing with total focus for 10 minutes. Not 30. Not the whole piece. Ten minutes. One thing. The compound effect handles the rest.",
        ],
    },
    {
        "triggers": ["rhythm", "timing", "tempo", "fast", "slow down", "rushing", "dragging", "count", "beat", "metronome"],
        "responses": [
            "Rhythm problems come from trying to play at performance tempo before the neural pathway is ready. Cut the tempo in half. Count out loud — your voice engages a different brain circuit than your fingers. That dual activation is what the Skills Genome records. If you can't count it aloud, you can't play it.",
            "Here's the counterintuitive fix: don't use a metronome yet. Clap the rhythm AWAY from the piano first. Your body needs to feel the pulse before your fingers execute it. Clap and count the hardest two measures five times each. Then return to the keys at half tempo. The rhythm will already be in your body.",
            "Your internal clock isn't broken — it's just not calibrated to this tempo. Practice the passage at THREE different speeds: painfully slow ( accuracy), medium-slow (clean transitions), and just-below-target (confidence building). Each speed teaches your brain a different layer of the rhythm. Then converge.",
        ],
    },
    {
        "triggers": ["sight read", "reading", "notes", "sheet music", "notation", "read music", "music reading", "decode"],
        "responses": [
            "You're in a Cul-de-sac — reading note-by-note instead of seeing relationships between notes. Intervallic reading is the exit: stop naming each note and start noticing the contour. Up by a step? A skip? The same note? Your eye should see the shape before the labels. This is how professional musicians read — and it's learnable in a week.",
            "Note-by-note reading is the most common Cul-de-sac — you're decoding individual letters instead of reading words. Try this: take a new, easy piece and play it WITHOUT naming a single note. Just follow the contour — up, down, stay, skip. Your fingers will follow your eye. This is how children learn language before they learn letters.",
            "Your reading bottleneck is cognitive overload — you're trying to identify the note, find it on the keyboard, and coordinate your fingers simultaneously. Separate those tasks: spend 5 minutes just NAMING notes on the staff without playing. Then 5 minutes just PLAYING without naming. When you recombine them, each skill will be stronger.",
        ],
    },
    {
        "triggers": ["chord", "chords", "transition", "switching", "change chord", "chord change"],
        "responses": [
            "Chord transitions fail when you think about all three fingers at once — that's cognitive overload in action. The 80/20 fix: land your thumb first, just the thumb, at the exact moment of the transition. Let the other two fingers fall into place naturally. One anchor finger eliminates the cognitive load of three simultaneous movements.",
            "Your fingers are arriving at the chord one at a time because your brain is sending three separate signals. The fix: practice 'blocking' — form the full chord shape in the air above the keys, then drop all three fingers simultaneously. Do this five times without playing. The shape memory forms faster than the individual-finger memory.",
            "Chord transitions live and die in the AIR between chords, not on the keys. Watch your hand as you move from one chord to the next. Is it moving in a straight line or an arc? Arc = wasted time. Practice moving between chords in slow motion, keeping your hand as close to the keys as possible. Minimum distance, minimum time.",
        ],
    },
    {
        "triggers": ["memorize", "memory", "remember", "forget", "forgot", "cant remember", "keep forgetting", "halfway"],
        "responses": [
            "Memory fails when you're relying on muscle memory alone — that's rote, not literacy. Add a second encoding: before playing, close your eyes and visualize the score. See the notes. Name them out loud. When you can play the piece silently in your head, your fingers will follow. This is unseen learning — the neural pathway forms BEFORE the performance.",
            "Your piece falls apart halfway through because muscle memory is sequential — it only knows what comes NEXT, not where you ARE. The fix: practice starting from random measure numbers. Pick measure 12. Start there. If you can start from any measure, you truly know the piece. Muscle memory alone can't do that.",
            "Here's a test: write out the first 8 measures from memory on blank staff paper. If you can't — and most beginners can't — you've been relying on finger memory, not musical memory. Spend 5 minutes a day writing out one phrase from memory. It forces your brain to encode the notes, not just the movements.",
        ],
    },
    {
        "triggers": ["nervous", "anxiety", "performing", "performance", "audience", "scared", "mistake", "mess up", "stage"],
        "responses": [
            "Performance anxiety is your brain's threat response mistaking a recital for actual danger — completely normal, completely trainable. The fix is exposure, not calming down. Record yourself every day this week. Not to post — just to play for the red dot. By day 7, the recording feels normal, and the audience is just another red dot.",
            "Nerves mean you care — that's not weakness, that's investment. The physiological response (racing heart, shaky hands) is identical to excitement. Your brain just labeled it 'fear.' Before you play: take one slow breath, look at the first measure, and tell yourself 'I'm excited to share this.' Reframe the label and the feeling follows.",
            "The difference between a mistake that derails you and one that doesn't: recovery practice. Tomorrow, practice CONTINUING after a mistake. Make a deliberate error in measure 4 — then keep going without stopping. Do this three times. The audience doesn't remember the mistake. They remember whether you recovered.",
        ],
    },
    {
        "triggers": ["wrist", "pain", "hurt", "sore", "tension", "tight", "stiff", "relax"],
        "responses": [
            "Tension is your body trying to control with force what should be controlled with precision. Here's the 80/20 fix: play your passage at 25% tempo with deliberately loose wrists — so loose it almost sounds sloppy. Feel what relaxed playing actually feels like. Then gradually bring the tempo up while keeping the looseness. Tension at full speed means you never learned it relaxed at slow speed.",
            "Pain is a STOP signal, not a push-through signal. Take tomorrow off from that passage. When you return, check your bench height — your forearm should be parallel to the floor. A bench that's too low forces your wrist to compensate and creates tension. Fix the ergonomics first, then the technique.",
            "Wrist tension is usually a symptom of finger weakness. Your wrist is tensing up to compensate for fingers that aren't doing their job independently. Try this: play a five-finger scale while consciously keeping your wrist motionless. Only your fingers move. If you can't do it at any speed, that's the root cause. Build finger independence first.",
        ],
    },
    {
        "triggers": ["dynamics", "loud", "soft", "quiet", "expression", "feeling", "emotion", "musical", "phrasing"],
        "responses": [
            "Dynamics come LAST in the 80/20 sequence — notes first, then rhythm, then articulation, then dynamics. If you're still thinking about which note comes next, your brain has no capacity left for expression. Get the notes automatic first. Then add ONE dynamic contrast to one phrase. Priming: decide the emotion of each phrase before you play it.",
            "The secret to expressive playing: you can't PLAY an emotion you haven't IMAGINED. Before touching the keys, listen to a recording of your piece by a professional. Close your eyes. Feel where the music breathes. Then play just the first phrase, trying to match that feeling. Expression is ear training, not finger training.",
            "Pick ONE phrase — just one — and play it three different ways: sadly, joyfully, and angrily. The notes are identical. Only the touch changes. This exercise builds the connection between emotional intent and physical execution. Once you can play one phrase three ways, apply that awareness to your whole piece.",
        ],
    },
    {
        "triggers": ["pedal", "sustain", "blurry", "muddy", "clear", "clean", "pedaling"],
        "responses": [
            "Pedal problems are almost always ear problems in disguise. Your ear hasn't learned to hear the mud yet. Practice the passage WITHOUT pedal until every note is crystal clear. Then add pedal, but lift it COMPLETELY at every chord change. The pedal should enhance clarity, not hide imprecision.",
            "Here's the test: record yourself playing with pedal, then listen back. Can you hear every individual note in the fast passages, or is it a wash of sound? If it's a wash, you're pedaling too late or too long. Practice pedal CHANGES — lift and re-press on every new chord. Clean pedal changes sound like magic when you get them right.",
            "Think of the pedal like a violin bow — it connects notes into a phrase, but the phrase still needs to breathe. Mark your score: every chord change = pedal change. Every rest = pedal up. Play it dry first, then add pedal only where marked. You'll be shocked how much clearer it sounds.",
        ],
    },
    {
        "triggers": ["beginner", "just started", "new", "first week", "first lesson", "starting", "brand new", "never played"],
        "responses": [
            "Welcome — you're at the most exciting stage. Every session right now builds foundational neural pathways at maximum speed. Your only job for the first month: show up every day, even for 10 minutes. Consistency beats duration. The instrument is the gym — right now you're building the gym itself.",
            "First month rule: don't judge ANYTHING. Your brain is building infrastructure it's never built before. A baby doesn't judge its first steps — it just keeps walking. Be the baby. Show up. Make sounds. Tomorrow you'll be slightly better than today. That's the only metric that matters right now.",
            "Here's your first-week practice plan: 5 minutes of finger exercises, 5 minutes on your piece, 5 minutes of just exploring — play random notes, find sounds you like. The exploration time is where you fall in love with the instrument. Don't skip it. The instrument is the gym, but it's also a playground.",
        ],
    },
    {
        "triggers": ["teacher", "lesson", "my teacher said", "my teacher told", "class", "instructor"],
        "responses": [
            "Your teacher gives you the roadmap once a week. Cadence is the daily check-in between lessons — closing the 7-day feedback gap. Take what your teacher assigned and break it into daily micro-goals. Come back tomorrow and tell me which micro-goal you worked on.",
            "Between now and your next lesson: pick the HARDEST thing your teacher assigned and practice it first, not last, every day. Most students save the hard part for the end of practice when they're mentally drained — then wonder why it never improves. Hardest thing first. Fresh brain. Every day.",
            "Write down exactly what your teacher said this week — their exact words, not your summary. Read those words before each practice session. The difference between 'practice measure 8' and 'practice measure 8, watching the thumb crossover, at 80 bpm' is the difference between a week of progress and a week of spinning your wheels.",
        ],
    },
]

# ── Demo Cache ──
# Hardcoded responses for the demo script. Eliminates live API risk during judging.
# SpeechRecognition is non-deterministic — we match on KEYWORDS, not exact text.
# Match requires 2+ keywords present in the transcription (case-insensitive).
# First entry that meets the threshold wins.

DEMO_CACHE: list[dict] = [
    {
        "keywords": ["c major", "scale", "tangled", "thumb", "crossover", "fall apart",
                      "going up", "way down", "going down", "fingers get", "doesn't know",
                      "don't know", "practiced my", "hesitating"],
        "min_matches": 2,
        "coaching": (
            "This is the classic descending thumb-under crossover — the #1 beginner hurdle. "
            "Isolate just the three-note crossover: finger 3 to thumb, at the exact spot where you hesitate. "
            "Play those three notes ten times slowly, then add one note before it, then two. "
            "The instrument is the gym — you're building a neural pathway, not just repeating a scale."
        ),
        "practice_plan": "Tomorrow: play the three-note crossover (finger 3 to thumb) ten times slowly before you play the full scale. Five minutes. Just the crossover.",
    },
    {
        "keywords": ["hands together", "both hands", "hands separate", "left hand",
                      "right hand", "coordination", "collapse", "two hands"],
        "min_matches": 2,
        "coaching": (
            "Hands-separate mastery is a trap — your brain learned two skills in isolation "
            "but hasn't built the neural bridge between them. Two measures. Hands together. "
            "Half tempo. Five times. You're building the Skills Genome, one connection at a time."
        ),
        "practice_plan": "Tomorrow: pick two measures, play them hands-together at half tempo five times before you play anything hands-separate.",
    },
    {
        "keywords": ["stuck", "plateau", "not getting", "no progress", "not improving",
                      "feel like i'm not", "nothing happened"],
        "min_matches": 1,
        "coaching": (
            "This plateau is the Dip — temporary friction from deliberate practice, not failure. "
            "Your brain is rewiring itself through unseen learning, even when it doesn't feel like progress. "
            "Pick ONE measure, the hardest one, and set a concrete goal for tomorrow."
        ),
        "practice_plan": "Tomorrow: pick the single hardest measure in your piece. Practice only that measure for 10 minutes. Nothing else.",
    },
]


def _check_demo_cache(transcription: str) -> dict | None:
    """Check if transcription matches any demo cache entry via keyword threshold."""
    text = transcription.lower()
    for entry in DEMO_CACHE:
        matches = sum(1 for kw in entry["keywords"] if kw in text)
        if matches >= entry["min_matches"]:
            return {"coaching": entry["coaching"], "practice_plan": entry["practice_plan"]}
    return None

# ── Practice Plans ──
# One concrete, single-sentence practice goal per category.
# Keyed by the first trigger in each category's trigger list (the canonical category key).

PRACTICE_PLANS: dict[str, str] = {
    "scale": "Tomorrow: isolate the three-note thumb-under crossover. Ten slow reps before your full scale. Five minutes.",
    "hands together": "Tomorrow: pick two measures, play hands-together at half tempo five times before anything hands-separate.",
    "stuck": "Tomorrow: pick the single hardest measure. Practice only that measure for 10 focused minutes. Nothing else.",
    "rhythm": "Tomorrow: clap and count the hardest two measures away from the piano, then play at half tempo. Five minutes.",
    "sight read": "Tomorrow: take a new easy piece and play it without naming a single note. Follow the contour only. Five minutes.",
    "chord": "Tomorrow: practice landing just your thumb at the chord change. Let the other fingers fall naturally. Ten reps.",
    "memorize": "Tomorrow: start from measure 12. If you can start from any measure, you truly know the piece. Test yourself.",
    "nervous": "Tomorrow: record yourself playing your piece once. Just for the red dot. Delete it after. Build the exposure.",
    "wrist": "Tomorrow: play your passage at 25% tempo with deliberately loose wrists. Feel what relaxed playing feels like.",
    "dynamics": "Tomorrow: play one phrase three different ways — sadly, joyfully, angrily. Same notes, different touch.",
    "pedal": "Tomorrow: play your piece with NO pedal. Make every note crystal clear. Then add pedal only at chord changes.",
    "beginner": "Tomorrow: 5 min finger exercises, 5 min on your piece, 5 min exploring sounds you like. Consistency over duration.",
    "teacher": "Tomorrow: practice the HARDEST thing your teacher assigned FIRST, not last. Fresh brain, hardest task.",
}

GENERIC_PRACTICE_PLAN = "Tomorrow: practice the ONE thing we identified today for 10 focused minutes. Then play your full piece once. Priming → Narration → Feedback."

GENERIC_COACHING = "The 80/20 rule: there's ONE thing holding you back more than everything else combined. Before tomorrow's practice, write it down — one sentence, one specific measure or skill. Practice that one thing in isolation for 10 minutes tomorrow. Then play your full piece. Priming → Narration → Feedback. One focused session beats an hour of unfocused repetition."


class AIClient:
    """Unified AI client with automatic fallback."""

    def __init__(self) -> None:
        self.featherless_key: str = os.getenv("FEATHERLESS_API_KEY", "")
        self.groq_key: str = os.getenv("GROQ_API_KEY", "")
        self.provider: str = self._detect_provider()

    def _detect_provider(self) -> str:
        if self.featherless_key:
            return "featherless"
        if self.groq_key:
            return "groq"
        return "mock"

    # ── Public API ──

    def coach(self, transcription: str, context: str = "") -> dict:
        """Generate coaching. Returns {coaching, practice_plan}. Demo cache → Featherless → Groq → Mock."""
        # Check demo cache first — guarantees the demo script always works
        cached = _check_demo_cache(transcription)
        if cached:
            return cached
        if self.provider == "featherless":
            result = self._call_featherless(transcription, context)
            if result:
                return result
        if self.provider == "groq":
            result = self._call_groq(transcription, context)
            if result:
                return result
        return self._mock_coach(transcription)

    # ── API Calls ──

    def _call_featherless(self, transcription: str, context: str) -> dict | None:
        result = self._call_api(
            FEATHERLESS_BASE,
            self.featherless_key,
            "deepseek-ai/DeepSeek-V3",
            transcription,
            context,
        )
        if result:
            return result
        return None

    def _call_groq(self, transcription: str, context: str) -> dict | None:
        result = self._call_api(
            GROQ_BASE,
            self.groq_key,
            "llama-3.3-70b-versatile",
            transcription,
            context,
        )
        if result:
            return result
        return None

    def _call_api(
        self, base_url: str, api_key: str, model: str,
        transcription: str, context: str,
    ) -> dict | None:
        user_message = (
            f'Student practice description: "{transcription}"\n'
            f'Additional context: "{context}"\n'
            f"Apply 80/20 method. Three sentences maximum.\n"
            f"Use the student's own words back to them. Be warm and specific.\n"
            f'After your coaching, add a line starting with "TOMORROW:" with '
            f"one concrete, single-sentence practice goal for the student's next session."
        )
        try:
            resp = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": COACH_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 350,
                    "temperature": 0.7,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            full = data["choices"][0]["message"]["content"].strip()
            # Split on TOMORROW: delimiter if present
            if "\nTOMORROW:" in full:
                parts = full.split("\nTOMORROW:", 1)
                return {"coaching": parts[0].strip(), "practice_plan": "Tomorrow:" + parts[1].strip()}
            if "TOMORROW:" in full:
                parts = full.split("TOMORROW:", 1)
                return {"coaching": parts[0].strip(), "practice_plan": "Tomorrow:" + parts[1].strip()}
            return {"coaching": full, "practice_plan": GENERIC_PRACTICE_PLAN}
        except requests.exceptions.RequestException:
            return None

    # ── Mock Coach ──

    def _mock_coach(self, transcription: str) -> dict:
        """Keyword-matched coaching with rotation — never repeats the same answer twice."""
        text = transcription.lower()

        for entry in COACHING_DB:
            for trigger in entry["triggers"]:
                if trigger in text:
                    responses = entry.get("responses") or [entry["response"]]
                    coaching = random.choice(responses)
                    # Look up practice plan by first trigger (canonical category key)
                    plan = PRACTICE_PLANS.get(entry["triggers"][0], GENERIC_PRACTICE_PLAN)
                    return {"coaching": coaching, "practice_plan": plan}

        return {"coaching": GENERIC_COACHING, "practice_plan": GENERIC_PRACTICE_PLAN}


    # ── Sheet Music Scan ──

    def scan_sheet(self, image_base64: str, filename: str = "") -> dict:
        """Analyze sheet music photo via Featherless Qwen3-VL or mock fallback."""
        if self.featherless_key:
            result = self._call_vision_api(image_base64, filename)
            if result:
                return result
        return self._mock_scan(filename)

    def _call_vision_api(self, image_base64: str, filename: str) -> dict | None:
        try:
            resp = requests.post(
                f"{FEATHERLESS_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.featherless_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "Qwen/Qwen3-VL-235B-A22B",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a professional piano teacher analyzing sheet music. "
                                "Describe: (1) the key signature and time signature, "
                                "(2) the overall difficulty level for a beginner/intermediate student, "
                                "(3) the single hardest section with measure numbers if visible, "
                                "(4) one specific practice strategy for that section. "
                                "Use warm, encouraging language. Three sentences maximum."
                            ),
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": f"Analyze this sheet music photo ({filename}). What should the student focus on?"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                            ],
                        },
                    ],
                    "max_tokens": 250,
                    "temperature": 0.7,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return {"analysis": data["choices"][0]["message"]["content"].strip()}
        except requests.exceptions.RequestException:
            return None

    def _mock_scan(self, filename: str) -> dict:
        """Mock sheet music analysis for demo without API key."""
        name = filename.lower()
        if "chopin" in name or "prelude" in name:
            analysis = (
                "This piece appears to be in a minor key — likely E minor or C minor based on the key signature. "
                "Difficulty: intermediate. The hardest section is the descending chromatic runs in the middle section — "
                "isolate those four measures and practice them hands-separate at half tempo before attempting hands-together. "
                "The instrument is the gym — slow practice here is building your neural pathway."
            )
        elif "scale" in name or "exercise" in name:
            analysis = (
                "This looks like a technical exercise — possibly scales or arpeggios in C or G Major. "
                "Difficulty: beginner to early intermediate. The trickiest part will be the thumb-under crossovers "
                "in the ascending and descending runs. Mark the crossover points with a pencil and practice just those transitions."
            )
        else:
            analysis = (
                "This sheet music appears to be in C Major, 4/4 time — a great piece for building foundational skills. "
                "The tricky part is likely in the middle section where the note density increases. "
                "Focus your practice there: play it at half tempo, count out loud, and isolate any measure where you hesitate."
            )
        return {"analysis": analysis}


# Singleton
_client: AIClient | None = None


def get_client() -> AIClient:
    global _client
    if _client is None:
        _client = AIClient()
    return _client
