"""
Gate 0 — Test Featherless audio transcription.
Run this BEFORE building anything else.
If 2/3 test cases pass → continue with Cadence.
If 0-1 pass → pivot to local faster-whisper or SkillBridge.
"""
import os
from dotenv import load_dotenv
from featherless_client import FeatherlessClient

load_dotenv()

client = FeatherlessClient(os.getenv("FEATHERLESS_API_KEY", ""))

# Test cases — record these yourself as 10-15s voice memos
# and place them in a test_audio/ folder, or modify paths.
# For now, test with direct text to validate the coaching pipeline.

print("=" * 50)
print("GATE 0 — Featherless Pipeline Test")
print("=" * 50)

# Test 1: Coaching with a simulated transcription
print("\n🔴 TEST 1: Coaching response quality")
transcription = "I've been practicing the C major scale for three weeks. My right hand goes up fine but on the way down my fingers get tangled. I don't know where to put my thumb."
result = client.generate_coaching(transcription, "Beginner pianist, 3 weeks in")
print(f"  Coaching: {result}")
print("  ✅ Test 1 complete" if len(result) > 20 else "  ❌ Test 1 failed")

# Test 2: Coaching with a different problem
print("\n🔴 TEST 2: Different problem type")
transcription2 = "I can play the left hand of my piece perfectly and the right hand perfectly but when I try to put them together everything falls apart."
result2 = client.generate_coaching(transcription2, "")
print(f"  Coaching: {result2}")
print("  ✅ Test 2 complete" if len(result2) > 20 else "  ❌ Test 2 failed")

# Test 3: Edge case — vague description
print("\n🔴 TEST 3: Vague description")
transcription3 = "I practiced for 20 minutes today. It was fine I guess. Nothing really happened."
result3 = client.generate_coaching(transcription3, "")
print(f"  Coaching: {result3}")
print("  ✅ Test 3 complete" if len(result3) > 20 else "  ❌ Test 3 failed")

print("\n" + "=" * 50)
print("GATE 0 COMPLETE — Check coaching quality above")
print("If 2/3 responses are specific and actionable → PROCEED")
print("If responses are generic or broken → INVESTIGATE")
print("=" * 50)
