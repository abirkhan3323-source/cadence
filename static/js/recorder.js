/**
 * Cadence — Voice-Driven AI Music Coach
 * Uses browser SpeechRecognition API for real-time transcription.
 * Sends transcribed text to Flask for AI coaching.
 */

// State
let recognition = null;
let isRecording = false;
let recordingSeconds = 0;
let recordingTimer = null;
let transcribedText = "";

// DOM
const screenRecord = document.getElementById("screen-record");
const screenFeedback = document.getElementById("screen-feedback");
const screenProgress = document.getElementById("screen-progress");
const btnRecord = document.getElementById("btn-record");
const btnStop = document.getElementById("btn-stop");
const btnSend = document.getElementById("btn-send");
const btnAgain = document.getElementById("btn-again");
const recordingStatus = document.getElementById("recording-status");
const recordingTime = document.getElementById("recording-time");
const contextArea = document.getElementById("context-area");
const loading = document.getElementById("loading");
const transcriptDisplay = document.getElementById("transcript-display");
const coachingDisplay = document.getElementById("coaching-display");
const promptText = document.querySelector(".prompt");
const btnBackProgress = document.getElementById("btn-back-progress");
const navBtns = document.querySelectorAll(".nav-btn");

// --- Speech Recognition Setup ---

function createRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Speech recognition not supported. Please use Chrome or Edge.");
        return null;
    }

    const rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onresult = function (event) {
        let interim = "";
        let final = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            if (result.isFinal) {
                final += result[0].transcript + " ";
            } else {
                interim += result[0].transcript;
            }
        }

        transcribedText += final;

        // Show live transcription in the prompt area
        if (promptText) {
            promptText.innerHTML = `
                <span style="color: #e8b84b;">🎙️ ${transcribedText}</span>
                <span style="color: #666; font-style: italic;">${interim}</span>
            `;
        }
    };

    rec.onerror = function (event) {
        if (event.error === "no-speech") {
            return; // silent
        }
        if (event.error === "aborted") {
            return;
        }
        console.error("Speech recognition error:", event.error);
    };

    rec.onend = function () {
        if (isRecording) {
            rec.start();
        }
    };

    return rec;
}

// --- Recording Controls ---

btnRecord.addEventListener("click", startRecording);
btnStop.addEventListener("click", stopRecording);
btnSend.addEventListener("click", sendToCoach);
btnAgain.addEventListener("click", resetToRecord);

async function startRecording() {
    transcribedText = "";

    recognition = createRecognition();
    if (!recognition) return;

    isRecording = true;
    recognition.start();

    // UI
    btnRecord.hidden = true;
    btnStop.hidden = false;
    recordingStatus.hidden = false;
    recordingSeconds = 0;
    recordingTime.textContent = "0:00";
    recordingTimer = setInterval(updateTimer, 1000);

    // Auto-stop at 60 seconds
    setTimeout(function () {
        if (isRecording) stopRecording();
    }, 60000);
}

function updateTimer() {
    recordingSeconds++;
    const min = Math.floor(recordingSeconds / 60);
    const sec = recordingSeconds % 60;
    recordingTime.textContent = min + ":" + String(sec).padStart(2, "0");
}

function stopRecording() {
    if (!isRecording) return;

    isRecording = false;
    if (recognition) {
        recognition.stop();
        recognition = null;
    }
    clearInterval(recordingTimer);

    // UI
    recordingStatus.hidden = true;
    btnStop.hidden = true;

    if (transcribedText.trim()) {
        contextArea.hidden = false;
    } else {
        alert("I didn't catch anything. Please try again — speak clearly into your mic.");
        resetToRecord();
    }
}

// --- Send to Coach ---

async function sendToCoach() {
    if (!transcribedText.trim()) return;

    const context = document.getElementById("context").value;

    // UI
    contextArea.hidden = true;
    btnRecord.hidden = true;
    loading.hidden = false;

    try {
        const resp = await fetch("/api/coach-text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                transcription: transcribedText.trim(),
                context: context,
            }),
        });

        const data = await resp.json();

        if (data.error) {
            alert(data.error);
            resetToRecord();
            return;
        }

        transcriptDisplay.textContent = '"' + data.transcription + '"';
        coachingDisplay.textContent = data.coaching;

        loading.hidden = true;
        screenRecord.hidden = true;
        screenFeedback.hidden = false;

    } catch (err) {
        alert("Connection error. Is the server running on port 5000?");
        console.error(err);
        resetToRecord();
    }
}

function resetToRecord() {
    transcribedText = "";
    isRecording = false;
    if (recognition) {
        recognition.stop();
        recognition = null;
    }
    document.getElementById("context").value = "";
    loading.hidden = true;
    contextArea.hidden = true;
    screenFeedback.hidden = true;
    screenRecord.hidden = false;
    btnRecord.hidden = false;
    btnStop.hidden = true;
    recordingStatus.hidden = true;
    if (promptText) {
        promptText.innerHTML = 'Tell Cadence what you practiced today.<br><span class="prompt-hint">What went well? What felt hard? What\'s stuck?</span>';
    }
}

// --- Navigation ---

navBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
        const screen = btn.dataset.screen;
        navBtns.forEach(function (b) { b.classList.remove("nav-btn--active"); });
        btn.classList.add("nav-btn--active");

        screenRecord.hidden = screen !== "record";
        screenFeedback.hidden = screen !== "feedback";
        screenProgress.hidden = screen !== "progress";

        if (screen === "record" && !isRecording) {
            btnRecord.hidden = false;
        }
    });
});

btnBackProgress.addEventListener("click", function () {
    screenProgress.hidden = true;
    screenRecord.hidden = false;
    btnRecord.hidden = false;
});
