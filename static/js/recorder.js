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
let loadingTimer = null;

// --- Onboarding ---

(function initOnboarding() {
    var overlay = document.getElementById("onboarding-overlay");
    var btnStart = document.getElementById("btn-onboard-start");
    var btnSkip = document.getElementById("btn-onboard-skip");

    if (!overlay) return;

    // Show on first visit only
    if (!localStorage.getItem("cadence_onboarded")) {
        overlay.hidden = false;
    }

    function dismiss() {
        overlay.hidden = true;
        localStorage.setItem("cadence_onboarded", "1");
    }

    if (btnStart) btnStart.addEventListener("click", dismiss);
    if (btnSkip) btnSkip.addEventListener("click", dismiss);
})();

// DOM — Record screen
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
const promptText = document.querySelector(".prompt");
const btnBackProgress = document.getElementById("btn-back-progress");
const navBtns = document.querySelectorAll(".nav-btn");

// DOM — Feedback screen
const transcriptDisplay = document.getElementById("transcript-display");
const coachingDisplay = document.getElementById("coaching-display");
const planContent = document.getElementById("plan-content");

// DOM — Loading
const stepTranscribe = document.getElementById("step-transcribe");
const stepAnalyze = document.getElementById("step-analyze");
const stepCoach = document.getElementById("step-coach");
const neuralAnimation = document.getElementById("neural-animation");

// DOM — Error recovery
const errorRecovery = document.getElementById("error-recovery");
const errorMessage = document.getElementById("error-message");
const btnRetry = document.getElementById("btn-retry");
const btnTypeMode = document.getElementById("btn-type-mode");
const typeInputArea = document.getElementById("type-input-area");
const typePractice = document.getElementById("type-practice");
const btnSendType = document.getElementById("btn-send-type");

// DOM — Progress screen
const streakCount = document.getElementById("streak-count");
const statSessions = document.getElementById("stat-sessions");
const statPieces = document.getElementById("stat-pieces");
const statSkills = document.getElementById("stat-skills");

// DOM — Quote, Listen, Badges, Heatmap, Export, Scan
const julianQuote = document.getElementById("julian-quote");
const btnListen = document.getElementById("btn-listen");
const badgesGrid = document.getElementById("badges-grid");
const badgesSubtitle = document.getElementById("badges-subtitle");
const heatmapGrid = document.getElementById("heatmap-grid");
const heatmapSubtitle = document.getElementById("heatmap-subtitle");
const btnExport = document.getElementById("btn-export");
const btnScan = document.getElementById("btn-scan");
const sheetFile = document.getElementById("sheet-file");
const scanResult = document.getElementById("scan-result");
const scanText = document.getElementById("scan-text");

// DOM — Audio Recording
var btnRecordAudio = document.getElementById("btn-record-audio");
var audioStatus = document.getElementById("audio-status");
var audioLevel = document.getElementById("audio-level");
var mediaRecorder = null;
var audioChunks = [];
var audioBlob = null;
var isRecordingAudio = false;
var audioContext = null;
var audioAnalyser = null;

// DOM — Kaizen Timer
var kaizenTime = document.getElementById("kaizen-time");
var btnKaizenStart = document.getElementById("btn-kaizen-start");
var btnKaizenReset = document.getElementById("btn-kaizen-reset");
var kaizenSeconds = 900;
var kaizenInterval = null;
var isKaizenRunning = false;
var kaizenTotalMinutes = parseInt(localStorage.getItem("cadence_kaizen_minutes") || "0", 10);

// --- Speech Recognition Setup ---

function createRecognition() {
    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        promptText.innerHTML = '<span style="color: #e07070;">Speech recognition not supported. Use Chrome or Edge.</span>';
        return null;
    }

    var rec = new SpeechRecognition();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";
    rec.maxAlternatives = 1;

    // Visual feedback: mic is hot
    var statusHint = document.querySelector(".recording-hint");
    var dot = document.querySelector(".recording-dot");

    rec.onaudiostart = function () {
        if (dot) dot.classList.add("recording-dot--hot");
        if (statusHint) statusHint.textContent = "Microphone active — start speaking!";
    };

    rec.onsoundstart = function () {
        if (dot) dot.classList.add("recording-dot--pulse");
        if (statusHint) statusHint.textContent = "Hearing you... keep talking.";
    };

    rec.onspeechstart = function () {
        if (statusHint) statusHint.textContent = "Capturing your words...";
    };

    rec.onspeechend = function () {
        if (statusHint) statusHint.textContent = "Listening... tell me more.";
    };

    rec.onresult = function (event) {
        var interim = "";
        var final = "";

        for (var i = event.resultIndex; i < event.results.length; i++) {
            var result = event.results[i];
            if (result.isFinal) {
                final += result[0].transcript + " ";
            } else {
                interim += result[0].transcript;
            }
        }

        transcribedText += final;

        if (promptText) {
            var display = '<span style="color: var(--accent);">' + transcribedText + '</span>';
            if (interim) {
                display += '<span style="color: #888; font-style: italic;">' + interim + '</span>';
            }
            if (transcribedText || interim) {
                promptText.innerHTML = display;
            }
        }
    };

    rec.onerror = function (event) {
        var msg = "";
        switch (event.error) {
            case "not-allowed":
                msg = "Microphone access blocked. Click the lock/camera icon in your browser address bar and allow the mic.";
                break;
            case "no-speech":
                msg = "No speech detected. Check if your mic is plugged in and not muted.";
                break;
            case "audio-capture":
                msg = "No microphone found. Connect a mic and try again.";
                break;
            case "network":
                msg = "Network error. Speech recognition needs internet.";
                break;
            case "aborted":
                return; // Normal stop — no error
            default:
                msg = "Speech error: " + event.error + ". Try again or use text input.";
        }
        if (promptText) {
            promptText.innerHTML = '<span style="color: #e07070;">' + msg + '</span>';
        }
        isRecording = false;
        clearInterval(recordingTimer);
        recordingTimer = null;
        recordingStatus.hidden = true;
        btnStop.hidden = true;
        btnRecord.hidden = false;
    };

    rec.onend = function () {
        if (dot) {
            dot.classList.remove("recording-dot--hot", "recording-dot--pulse");
        }
        if (isRecording) {
            // Auto-restart on unexpected end (but not on manual stop)
            try { rec.start(); } catch (e) { /* restart failed, stop */ }
        }
    };

    return rec;
}

// --- Recording Controls ---

btnRecord.addEventListener("click", function() {
    // If text is typed, send it directly — no voice needed
    var text = typeDirect ? typeDirect.value.trim() : "";
    if (text) {
        transcribedText = text;
        typeDirect.value = "";
        document.getElementById("context").value = "";
        document.getElementById("type-input-block").hidden = true;
        sendToCoach();
        return;
    }
    // Otherwise start voice recording
    startRecording();
});
btnStop.addEventListener("click", stopRecording);
btnSend.addEventListener("click", sendToCoach);
btnAgain.addEventListener("click", resetToRecord);
btnRetry.addEventListener("click", function () {
    errorRecovery.hidden = true;
    sendToCoach();
});
btnTypeMode.addEventListener("click", function () {
    errorRecovery.hidden = true;
    typeInputArea.hidden = false;
    typePractice.value = transcribedText || "";
});
btnSendType.addEventListener("click", sendTypedToCoach);

// Direct type input on main record screen
var typeDirect = document.getElementById("type-direct");

// Update button label when text is typed
if (typeDirect) {
    typeDirect.addEventListener("input", function() {
        var hasText = typeDirect.value.trim().length > 0;
        var btnText = document.querySelector(".btn-record__text");
        var btnIcon = document.querySelector(".btn-record__icon");
        if (btnText) {
            btnText.textContent = hasText ? "Send to Coach" : "Tap to Record";
        }
        if (btnIcon) {
            btnIcon.innerHTML = hasText
                ? '<use href="#icon-send"/>'
                : '<use href="#icon-mic"/>';
        }
    });
}

// Listen, Export, Scan
if (btnListen) btnListen.addEventListener("click", toggleSpeech);
if (btnExport) btnExport.addEventListener("click", downloadReport);
if (btnScan) btnScan.addEventListener("click", function () { sheetFile.click(); });
if (sheetFile) sheetFile.addEventListener("change", handleSheetUpload);

// Audio recording button
if (btnRecordAudio) {
    btnRecordAudio.addEventListener("click", toggleAudioRecording);
}

// Kaizen Timer
if (btnKaizenStart) btnKaizenStart.addEventListener("click", toggleKaizenTimer);
if (btnKaizenReset) btnKaizenReset.addEventListener("click", resetKaizenTimer);

// Demo button — simulates live audio analysis with detected notes
var btnDemo = document.getElementById("btn-demo");
if (btnDemo) {
    btnDemo.addEventListener("click", function() {
        transcribedText = "I practiced my C major scale today. Going up is fine, but on the way down my fingers get all tangled up at the thumb crossover. I don't know what I'm doing wrong.";

        // Simulate audio analysis — makes AI respond as if it heard the playing
        var demoContext = (
            "\n\n[🎹 LIVE AUDIO ANALYSIS — You just HEARD the student play:]" +
            "\n- Notes detected: C4, D4, E4, F4, G4, A4, B4, C5" +
            "\n- Total notes: 8" +
            "\n- Tempo: ~120 BPM" +
            "\n- Hesitations detected: 1 (at the descending crossover between E4 and D4)" +
            "\n- Off-pitch notes (30+ cents): 0" +
            "\n- Duration: 12s" +
            "\n- Musical summary: Detected 8 notes: C4, D4, E4, F4, G4, A4, B4, C5. Clean ascending scale. One hesitation on descent at the thumb-under crossover." +
            "\n\nIMPORTANT: Reference these specific notes in your coaching. The student played C4 through C5 clean on the way up but hesitated at the thumb crossover on the way down. Tell them exactly which notes to isolate."
        );

        document.getElementById("context").value = demoContext;
        document.getElementById("demo-hint").style.opacity = "0.4";
        sendToCoach();
    });
}

function startRecording() {
    transcribedText = "";

    recognition = createRecognition();
    if (!recognition) return;

    try {
        recognition.start();
    } catch (e) {
        promptText.innerHTML = '<span style="color: #e07070;">Mic access blocked. Allow microphone in browser settings and reload.</span>';
        return;
    }

    isRecording = true;
    btnRecord.hidden = true;
    btnStop.hidden = false;
    recordingStatus.hidden = false;
    document.getElementById("type-input-block").hidden = true;
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
    var min = Math.floor(recordingSeconds / 60);
    var sec = recordingSeconds % 60;
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
    recordingTimer = null;

    recordingStatus.hidden = true;
    btnStop.hidden = true;
    recordingTime.textContent = "0:00";

    if (transcribedText.trim()) {
        contextArea.hidden = false;
        // Show type input block for context, keep text input available
        document.getElementById("type-input-block").hidden = false;
    } else {
        // Non-blocking: show inline hint instead of alert()
        if (promptText) {
            promptText.innerHTML = '<span style="color: #e07070;">I didn\'t catch anything. Try again — speak clearly into your mic, or type below.</span>';
        }
        resetToRecord();
    }
}

// --- Loading Step Indicator ---

function startLoadingSteps() {
    neuralAnimation.hidden = false;
    setStepState(stepTranscribe, "active");
    setStepState(stepAnalyze, "pending");
    setStepState(stepCoach, "pending");

    loadingTimer = setTimeout(function () {
        setStepState(stepTranscribe, "done");
        setStepState(stepAnalyze, "active");
        loadingTimer = setTimeout(function () {
            setStepState(stepAnalyze, "done");
            setStepState(stepCoach, "active");
        }, 1000);
    }, 800);
}

function stopLoadingSteps() {
    if (loadingTimer) clearTimeout(loadingTimer);
    // Mark all as done
    [stepTranscribe, stepAnalyze, stepCoach].forEach(function (s) {
        setStepState(s, "done");
    });
}

function setStepState(stepEl, state) {
    stepEl.classList.remove("loading-step--active", "loading-step--done");
    if (state === "active") stepEl.classList.add("loading-step--active");
    if (state === "done") stepEl.classList.add("loading-step--done");
}

// --- Send to Coach ---

function sendToCoach() {
    if (!transcribedText.trim() && !audioBlob) return;

    var context = document.getElementById("context").value;

    contextArea.hidden = true;
    btnRecord.hidden = true;
    loading.hidden = false;
    typeInputArea.hidden = true;
    errorRecovery.hidden = true;
    startLoadingSteps();

    var payload = {
        transcription: transcribedText.trim(),
        context: context,
    };

    // Include audio if recorded — convert to WAV for proper analysis
    if (audioBlob) {
        convertBlobToWav(audioBlob, function(wavBlob) {
            var reader = new FileReader();
            reader.onload = function(e) {
                payload.audio = e.target.result.split(",")[1];
                payload.audio_mime = "audio/wav";
                doSendToCoach(payload);
            };
            reader.readAsDataURL(wavBlob);
        });
        return;
    }

    doSendToCoach(payload);
}

function doSendToCoach(payload) {
    // Inject persona context
    var personaLevel = "intermediate";
    var personaSelect = document.getElementById("persona-level");
    if (personaSelect) personaLevel = personaSelect.value;

    if (personaLevel === "beginner") {
        payload.context = "Student is a BEGINNER (Stage 1 — Learn to Read). Use gentle encouragement, fundamental framing. " + (payload.context || "");
    } else if (personaLevel === "advanced") {
        payload.context = "Student is ADVANCED (Stage 3 — Learn to Perform). Use rigorous critique, treat as serious performer. " + (payload.context || "");
    } else if (personaLevel === "apprentice") {
        payload.context = "Student is a STAGE 4 APPRENTICE (Learn to Build). Treat as a peer. Expect excellence. " + (payload.context || "");
    }

    var endpoint = payload.audio ? "/api/coach-audio" : "/api/coach-text";

    fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    })
        .then(function (resp) { return resp.json(); })
        .then(function (data) {
            stopLoadingSteps();

            if (data.error) {
                showError(data.error);
                return;
            }

            // Populate feedback sections
            transcriptDisplay.textContent = '"' + (data.transcription || payload.transcription) + '"';
            coachingDisplay.textContent = data.coaching;
            planContent.textContent = data.practice_plan || "";
            updateProviderBadge(data.provider);
            rotateQuote();

            // Update progress
            updateProgress(data);

            // Reset speech state
            if (btnListen) {
                btnListen.innerHTML = '<svg width="16" height="16"><use href="#icon-mic"/></svg> Listen to Coaching';
                btnListen.classList.remove("listening");
            }
            window.speechSynthesis.cancel();

            loading.hidden = true;
            screenRecord.hidden = true;
            screenFeedback.hidden = false;
        })
        .catch(function (err) {
            stopLoadingSteps();
            showError("Connection error. Make sure the server is running on port 5000.");
        });
}

function sendTypedToCoach() {
    transcribedText = typePractice.value.trim();
    if (!transcribedText) {
        alert("Please describe your practice first.");
        return;
    }
    document.getElementById("context").value = "";
    sendToCoach();
}

function showError(msg) {
    loading.hidden = true;
    errorMessage.textContent = msg;
    errorRecovery.hidden = false;
}

// --- localStorage Progress Tracking ---

function updateProgress(data) {
    try {
        var sessions = parseInt(localStorage.getItem("cadence_sessions") || "0", 10) + 1;
        var pieces = parseInt(localStorage.getItem("cadence_pieces") || "0", 10);
        var skills = parseInt(localStorage.getItem("cadence_skills") || "0", 10);

        // Calculate streak
        var today = new Date().toISOString().split("T")[0];
        var lastDate = localStorage.getItem("cadence_last_date") || "";
        var streak = parseInt(localStorage.getItem("cadence_streak") || "0", 10);

        if (lastDate === today) {
            // Already practiced today, don't increment streak
        } else if (lastDate === getYesterday()) {
            streak += 1;
        } else if (lastDate === "") {
            streak = 1;
        } else {
            streak = 1; // Streak broken
        }

        // Seed realistic demo stats on first session
        if (sessions === 1) {
            pieces = 3;
            skills = 12;
            if (!localStorage.getItem("cadence_seeded")) {
                localStorage.setItem("cadence_seeded", "1");
                sessions = 47; // Jump-start for demo
                streak = Math.max(streak, 22);
            }
        }

        localStorage.setItem("cadence_sessions", String(sessions));
        localStorage.setItem("cadence_pieces", String(pieces));
        localStorage.setItem("cadence_skills", String(skills));
        localStorage.setItem("cadence_streak", String(streak));
        localStorage.setItem("cadence_last_date", today);

        // Track heatmap and unlock first-session badge
        trackHeatmapDay();
        unlockBadge("first-session");
    } catch (e) {
        // localStorage unavailable — silent fail
    }
}

function getYesterday() {
    var d = new Date();
    d.setDate(d.getDate() - 1);
    return d.toISOString().split("T")[0];
}

function loadProgress() {
    try {
        // If data is empty, seed it now (belt + suspenders)
        if (!localStorage.getItem("cadence_sessions")) {
            seedAllDemoData();
        }

        var sessions = localStorage.getItem("cadence_sessions") || "0";
        var pieces = localStorage.getItem("cadence_pieces") || "0";
        var skills = localStorage.getItem("cadence_skills") || "0";
        var streak = localStorage.getItem("cadence_streak") || "0";

        if (streakCount) streakCount.textContent = streak;
        if (statSessions) statSessions.textContent = sessions;
        if (statPieces) statPieces.textContent = pieces;
        if (statSkills) statSkills.textContent = skills;
    } catch (e) {
        // Use defaults from HTML
    }
}

// --- Skills Genome Radar Chart ---

function renderRadarChart() {
    var svg = document.getElementById("radar-svg");
    var legend = document.getElementById("radar-legend");
    if (!svg || !legend) return;

    var axes = [
        { label: "Read", value: 65 },
        { label: "Write", value: 30 },
        { label: "Play", value: 78 },
        { label: "See", value: 45 },
        { label: "Hear", value: 60 },
        { label: "Sing", value: 25 },
        { label: "Concept", value: 50 },
    ];

    var cx = 150, cy = 150, r = 110;
    var n = axes.length;
    var angleSlice = (2 * Math.PI) / n;

    // Background rings
    var rings = [0.25, 0.5, 0.75, 1.0];
    var ringHTML = "";
    for (var ri = 0; ri < rings.length; ri++) {
        var ringR = r * rings[ri];
        var ringPoints = [];
        for (var i = 0; i < n; i++) {
            var angle = angleSlice * i - Math.PI / 2;
            ringPoints.push(
                (cx + ringR * Math.cos(angle)).toFixed(1) + "," +
                (cy + ringR * Math.sin(angle)).toFixed(1)
            );
        }
        ringHTML += '<polygon points="' + ringPoints.join(" ") + '" ' +
            'fill="none" stroke="var(--border)" stroke-width="1" opacity="0.4"/>';
    }

    // Axis lines
    var axisHTML = "";
    for (var i = 0; i < n; i++) {
        var angle = angleSlice * i - Math.PI / 2;
        var x2 = cx + r * Math.cos(angle);
        var y2 = cy + r * Math.sin(angle);
        axisHTML += '<line x1="' + cx + '" y1="' + cy + '" ' +
            'x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '" ' +
            'stroke="var(--border)" stroke-width="1" opacity="0.4"/>';

        // Axis labels
        var labelR = r + 18;
        var lx = cx + labelR * Math.cos(angle);
        var ly = cy + labelR * Math.sin(angle);
        var textAnchor = "middle";
        if (lx < cx - 10) textAnchor = "end";
        if (lx > cx + 10) textAnchor = "start";
        axisHTML += '<text x="' + lx.toFixed(1) + '" y="' + ly.toFixed(1) + '" ' +
            'text-anchor="' + textAnchor + '" dominant-baseline="middle" ' +
            'fill="var(--text-muted)" font-size="11" font-family="inherit">' +
            axes[i].label + '</text>';
    }

    // Data polygon
    var dataPoints = [];
    for (var i = 0; i < n; i++) {
        var angle = angleSlice * i - Math.PI / 2;
        var val = axes[i].value / 100;
        var dx = cx + r * val * Math.cos(angle);
        var dy = cy + r * val * Math.sin(angle);
        dataPoints.push(dx.toFixed(1) + "," + dy.toFixed(1));
    }
    var dataHTML = '<polygon points="' + dataPoints.join(" ") + '" ' +
        'fill="rgba(232, 184, 75, 0.15)" stroke="var(--primary)" stroke-width="2" ' +
        'stroke-linejoin="round"/>';

    // Data dots
    var dotsHTML = "";
    for (var i = 0; i < n; i++) {
        var angle = angleSlice * i - Math.PI / 2;
        var val = axes[i].value / 100;
        var dx = cx + r * val * Math.cos(angle);
        var dy = cy + r * val * Math.sin(angle);
        dotsHTML += '<circle cx="' + dx.toFixed(1) + '" cy="' + dy.toFixed(1) + '" ' +
            'r="4" fill="var(--primary)"/>';
    }

    svg.innerHTML = ringHTML + axisHTML + dataHTML + dotsHTML;

    // Legend
    var legendHTML = "";
    for (var i = 0; i < n; i++) {
        legendHTML +=
            '<span class="radar-legend-item">' +
            '<span class="radar-legend-dot"></span>' +
            axes[i].label + " " + axes[i].value + "%" +
            '</span>';
    }
    legend.innerHTML = legendHTML;
}

// --- Navigation ---

navBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
        var screen = btn.dataset.screen;
        navBtns.forEach(function (b) { b.classList.remove("nav-btn--active"); });
        btn.classList.add("nav-btn--active");

        screenRecord.hidden = screen !== "record";
        screenFeedback.hidden = screen !== "feedback";
        screenProgress.hidden = screen !== "progress";

        if (screen === "record" && !isRecording) {
            btnRecord.hidden = false;
        }
        if (screen === "progress") {
            loadProgress();
            renderRadarChart();
            renderBadges();
            renderHeatmap();
        }
    });
});

btnBackProgress.addEventListener("click", function () {
    screenProgress.hidden = true;
    screenRecord.hidden = false;
    btnRecord.hidden = false;
});

// --- Julian Quote Rotation ---

var JULIAN_QUOTES = [
    "The instrument is the gym. The real output is the person.",
    "Daily feedback closes the 7-day gap that causes 83% of students to quit.",
    "Every practice session builds neural pathways through unseen learning.",
    "Kaizen — small daily improvements compound into mastery.",
    "Curiosity, patience, and persistence — the magic formula.",
    "The less I teach, the better the teacher I believe I am.",
];

function rotateQuote() {
    if (!julianQuote) return;
    var q = JULIAN_QUOTES[Math.floor(Math.random() * JULIAN_QUOTES.length)];
    var p = julianQuote.querySelector('p');
    if (p) p.textContent = '“' + q + '”';
}

// --- Provider Badge ---

function updateProviderBadge(provider) {
    var badge = document.getElementById("provider-badge");
    var nameEl = document.getElementById("provider-name");
    if (!badge || !nameEl) return;
    badge.hidden = false;
    if (provider && provider.indexOf("featherless") !== -1) {
        nameEl.textContent = "Featherless AI (DeepSeek V3)";
        badge.style.borderColor = "rgba(200, 168, 78, 0.3)";
    } else if (provider === "groq") {
        nameEl.textContent = "Groq (Llama 3.3 70B)";
    } else {
        nameEl.textContent = "Cadence Demo Cache";
    }
}

// --- Voice Synthesis ---

var isSpeaking = false;

function toggleSpeech() {
    var text = coachingDisplay.textContent;
    if (!text) return;

    if (isSpeaking) {
        window.speechSynthesis.cancel();
        isSpeaking = false;
        if (btnListen) {
            btnListen.innerHTML = '<svg width="16" height="16"><use href="#icon-mic"/></svg> Listen to Coaching';
            btnListen.classList.remove("listening");
        }
        return;
    }

    window.speechSynthesis.cancel();
    var utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 1;

    var voices = window.speechSynthesis.getVoices();
    var preferred = voices.find(function (v) {
        return v.name.indexOf("Samantha") !== -1 || v.name.indexOf("Karen") !== -1 ||
               v.name.indexOf("Female") !== -1 || v.name.indexOf("Google UK Female") !== -1;
    });
    if (preferred) utterance.voice = preferred;

    utterance.onstart = function () {
        isSpeaking = true;
        if (btnListen) {
            btnListen.innerHTML = '<svg width="16" height="16"><use href="#icon-stop"/></svg> Stop';
            btnListen.classList.add("listening");
        }
    };
    utterance.onend = function () {
        isSpeaking = false;
        if (btnListen) {
            btnListen.innerHTML = '<svg width="16" height="16"><use href="#icon-mic"/></svg> Listen to Coaching';
            btnListen.classList.remove("listening");
        }
    };
    utterance.onerror = function () {
        isSpeaking = false;
        if (btnListen) {
            btnListen.innerHTML = '<svg width="16" height="16"><use href="#icon-mic"/></svg> Listen to Coaching';
            btnListen.classList.remove("listening");
        }
    };

    window.speechSynthesis.speak(utterance);
}

// Preload voices
if (window.speechSynthesis) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = function () {
        window.speechSynthesis.getVoices();
    };
}

// --- Achievement Badges ---

var BADGES = [
    { id: "first-session", icon: "sparkle", label: "First Session" },
    { id: "7day-streak", icon: "flame", label: "7-Day Streak" },
    { id: "first-scale", icon: "note", label: "First Scale" },
    { id: "hands-together", icon: "check", label: "Hands Together" },
    { id: "memorized-piece", icon: "logo", label: "Memorized a Piece" },
    { id: "played-for-someone", icon: "mic", label: "Played for Someone" },
];

function getUnlockedBadges() {
    try {
        var data = localStorage.getItem("cadence_badges");
        return data ? JSON.parse(data) : [];
    } catch (e) {
        return [];
    }
}

function seedBadges() {
    // Seed Maria's demo badges
    var badges = getUnlockedBadges();
    if (badges.length === 0 && localStorage.getItem("cadence_seeded")) {
        // All 6 unlocked for the demo (Maria's 47 sessions)
        var allIds = BADGES.map(function (b) { return b.id; });
        localStorage.setItem("cadence_badges", JSON.stringify(allIds));
    }
}

function unlockBadge(badgeId) {
    var badges = getUnlockedBadges();
    if (badges.indexOf(badgeId) === -1) {
        badges.push(badgeId);
        localStorage.setItem("cadence_badges", JSON.stringify(badges));
    }
}

function renderBadges() {
    if (!badgesGrid || !badgesSubtitle) return;
    seedBadges();
    var unlocked = getUnlockedBadges();
    var earned = unlocked.length;
    var total = BADGES.length;

    var html = "";
    for (var i = 0; i < BADGES.length; i++) {
        var badge = BADGES[i];
        var isUnlocked = unlocked.indexOf(badge.id) !== -1;
        var iconHref = "#icon-" + badge.icon;
        html +=
            '<div class="badge-item' + (isUnlocked ? " badge-item--unlocked" : "") + '">' +
            '<div class="badge-circle' + (isUnlocked ? " badge-circle--unlocked" : "") + '">' +
            '<svg width="20" height="20"><use href="' + iconHref + '"/></svg>' +
            '</div>' +
            '<span class="badge-label">' + badge.label + '</span>' +
            '</div>';
    }
    badgesGrid.innerHTML = html;
    badgesSubtitle.textContent = earned + " achievements earned · " + (total - earned) + " to discover";
}

// --- Practice Heatmap ---

function getHeatmapData() {
    try {
        var data = localStorage.getItem("cadence_heatmap");
        var map = data ? JSON.parse(data) : {};
        // Seed Maria's demo data: 22 days of practice
        if (Object.keys(map).length === 0 && localStorage.getItem("cadence_seeded")) {
            var today = new Date();
            for (var i = 0; i < 28; i++) {
                var d = new Date(today);
                d.setDate(d.getDate() - i);
                var key = d.toISOString().split("T")[0];
                // Skip some days for realism (6 days missed out of 28)
                if (i === 2 || i === 7 || i === 13 || i === 18 || i === 23 || i === 26) continue;
                // Vary intensity (1-4)
                var intensity = i === 0 ? 4 : (i < 5 ? 3 : (i < 14 ? 2 : 1));
                map[key] = intensity;
            }
            localStorage.setItem("cadence_heatmap", JSON.stringify(map));
        }
        return map;
    } catch (e) {
        return {};
    }
}

function trackHeatmapDay() {
    try {
        var today = new Date().toISOString().split("T")[0];
        var map = getHeatmapData();
        map[today] = Math.min(4, (map[today] || 0) + 1);
        localStorage.setItem("cadence_heatmap", JSON.stringify(map));
    } catch (e) {
        // silent
    }
}

function renderHeatmap() {
    if (!heatmapGrid || !heatmapSubtitle) return;
    var map = getHeatmapData();
    var dayLabels = ["Mon", "", "Wed", "", "Fri", "", "Sun"];
    var today = new Date();

    // Build 7 columns × 4 rows (last 28 days, Mon-Sun columns)
    // Find the most recent Sunday as column 6
    var dow = today.getDay(); // 0=Sun
    var daysSinceSun = dow;
    var lastSun = new Date(today);
    lastSun.setDate(lastSun.getDate() - daysSinceSun);

    var cells = [];
    var practicedDays = 0;
    var totalDays = 0;

    for (var row = 3; row >= 0; row--) {
        for (var col = 0; col < 7; col++) {
            var d = new Date(lastSun);
            d.setDate(d.getDate() - (row * 7) + col - 6); // col 0 = Mon
            if (d > today) {
                cells.push({ date: d, level: -1 }); // future
                continue;
            }
            totalDays++;
            var key = d.toISOString().split("T")[0];
            var level = map[key] || 0;
            if (level > 0) practicedDays++;
            cells.push({ date: d, level: level });
        }
    }

    var html = "";
    for (var i = 0; i < cells.length; i++) {
        var cell = cells[i];
        if (cell.level === -1) {
            html += '<div class="heatmap-cell" style="background:transparent"></div>';
        } else {
            html += '<div class="heatmap-cell heatmap-cell--l' + cell.level + '" ' +
                'title="' + cell.date.toISOString().split("T")[0] + ': ' + cell.level + ' sessions"></div>';
        }
    }
    heatmapGrid.innerHTML = html;

    // Day labels (remove old if exists)
    var oldLabels = document.getElementById("heatmap-labels");
    if (oldLabels) oldLabels.remove();

    var labelsHTML = '<div class="heatmap-labels" id="heatmap-labels">';
    for (var j = 0; j < 7; j++) {
        labelsHTML += '<span>' + dayLabels[j] + '</span>';
    }
    labelsHTML += '</div>';
    heatmapGrid.insertAdjacentHTML("afterend", labelsHTML);

    var consistency = totalDays > 0 ? Math.round((practicedDays / totalDays) * 100) : 0;
    heatmapSubtitle.textContent = practicedDays + " days of practice in the last " + totalDays +
        " days · " + consistency + "% consistency";
}

// --- Export Report ---

function downloadReport() {
    try {
        var sessions = localStorage.getItem("cadence_sessions") || "0";
        var streak = localStorage.getItem("cadence_streak") || "0";
        var pieces = localStorage.getItem("cadence_pieces") || "0";
        var skills = localStorage.getItem("cadence_skills") || "0";
        var badges = getUnlockedBadges().length;
        var lastCoaching = coachingDisplay.textContent || "No coaching feedback yet.";

        var personaSelect = document.getElementById("persona-level");
        var studentName = personaSelect ? personaSelect.options[personaSelect.selectedIndex].text.split(" (")[0] : "Student";

        var today = new Date().toISOString().split("T")[0];
        var report =
            "Cadence Practice Report\n" +
            "=======================\n" +
            "Student: " + studentName + "\n" +
            "Date: " + today + "\n" +
            "\n" +
            "--- Stats ---\n" +
            "Total Sessions: " + sessions + "\n" +
            "Day Streak: " + streak + "\n" +
            "Pieces Mastered: " + pieces + "\n" +
            "Skills Unlocked: " + skills + "\n" +
            "Achievements Earned: " + badges + "/6\n" +
            "\n" +
            "--- Last Coaching Feedback ---\n" +
            lastCoaching + "\n" +
            "\n" +
            "--- Practice Plan ---\n" +
            (planContent.textContent || "No plan yet.") + "\n" +
            "\n" +
            'Generated by Cadence — "The instrument is the gym."\n';

        var blob = new Blob([report], { type: "text/plain" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = "Maria_weekly_report_" + today + ".txt";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (e) {
        alert("Could not generate report.");
    }
}

// --- Scan Sheet Music ---

function handleSheetUpload(event) {
    var file = event.target.files[0];
    if (!file) return;

    var scanLoading = document.getElementById("scan-loading");
    scanResult.hidden = true;
    if (scanLoading) scanLoading.hidden = false;

    var reader = new FileReader();
    reader.onload = function (e) {
        var base64 = e.target.result.split(",")[1];

        fetch("/api/scan-sheet", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: base64, filename: file.name }),
        })
            .then(function (resp) { return resp.json(); })
            .then(function (data) {
                if (scanLoading) scanLoading.hidden = true;
                scanResult.hidden = false;
                if (data.error) {
                    scanText.innerHTML = '<span style=\"color: var(--danger);\">' + data.error + '</span>';
                } else {
                    // Format structured analysis with line breaks
                    var formatted = data.analysis
                        .replace(/KEY:/gi, '<strong style=\"color: var(--gold-bright);\">KEY:</strong>')
                        .replace(/WHAT I SEE:/gi, '<br><br><strong style=\"color: var(--gold-bright);\">WHAT I SEE:</strong>')
                        .replace(/HARDEST SECTION:/gi, '<br><br><strong style=\"color: var(--danger);\">HARDEST SECTION:</strong>')
                        .replace(/PRACTICE STRATEGY:/gi, '<br><br><strong style=\"color: var(--success);\">PRACTICE STRATEGY:</strong>')
                        .replace(/\\n\\n/g, '<br><br>')
                        .replace(/\\n/g, '<br>');
                    scanText.innerHTML = formatted;
                }
            })
            .catch(function () {
                if (scanLoading) scanLoading.hidden = true;
                scanResult.hidden = false;
                scanText.innerHTML = '<span style=\"color: var(--danger);\">Could not reach the server. Is Cadence running?</span>';
            });
    };
    reader.readAsDataURL(file);
}

// --- Seed all demo data on page load (so Progress screen never shows zeros) ---

function seedAllDemoData() {
    try {
        // Only seed once
        if (localStorage.getItem("cadence_seeded_v2")) return;
        localStorage.setItem("cadence_seeded_v2", "1");

        var today = new Date().toISOString().split("T")[0];

        // Stats
        localStorage.setItem("cadence_sessions", "47");
        localStorage.setItem("cadence_pieces", "3");
        localStorage.setItem("cadence_skills", "12");
        localStorage.setItem("cadence_streak", "22");
        localStorage.setItem("cadence_last_date", today);

        // Badges — all 6 unlocked
        var allBadges = ["first-session", "7day-streak", "first-scale",
            "hands-together", "memorized-piece", "played-for-someone"];
        localStorage.setItem("cadence_badges", JSON.stringify(allBadges));

        // Heatmap — 22 days of practice in last 28 days
        var heatmap = {};
        for (var i = 0; i < 28; i++) {
            var d = new Date();
            d.setDate(d.getDate() - i);
            var key = d.toISOString().split("T")[0];
            // 6 missed days for realism
            if (i === 2 || i === 7 || i === 13 || i === 18 || i === 23 || i === 26) continue;
            var intensity = i === 0 ? 4 : (i < 5 ? 3 : (i < 14 ? 2 : 1));
            heatmap[key] = intensity;
        }
        localStorage.setItem("cadence_heatmap", JSON.stringify(heatmap));
    } catch (e) {
        // localStorage unavailable — silent
    }
}

// Run immediately on script load
seedAllDemoData();

// --- Kaizen Timer ---

function toggleKaizenTimer() {
    if (isKaizenRunning) {
        pauseKaizenTimer();
    } else {
        startKaizenTimer();
    }
}

function startKaizenTimer() {
    isKaizenRunning = true;
    if (btnKaizenStart) {
        btnKaizenStart.innerHTML = '<svg width="14" height="14"><use href="#icon-stop"/></svg> Pause';
        btnKaizenStart.classList.add("running");
    }
    kaizenInterval = setInterval(function() {
        kaizenSeconds--;
        updateKaizenDisplay();
        if (kaizenSeconds <= 0) completeKaizenSession();
    }, 1000);
}

function pauseKaizenTimer() {
    isKaizenRunning = false;
    clearInterval(kaizenInterval);
    kaizenInterval = null;
    if (btnKaizenStart) {
        btnKaizenStart.innerHTML = '<svg width="14" height="14"><use href="#icon-flame"/></svg> Resume';
        btnKaizenStart.classList.remove("running");
    }
}

function resetKaizenTimer() {
    pauseKaizenTimer();
    kaizenSeconds = 900;
    updateKaizenDisplay();
    if (btnKaizenStart) {
        btnKaizenStart.innerHTML = '<svg width="14" height="14"><use href="#icon-flame"/></svg> Start';
        btnKaizenStart.classList.remove("running");
    }
}

function updateKaizenDisplay() {
    if (!kaizenTime) return;
    var min = Math.floor(Math.max(0, kaizenSeconds) / 60);
    var sec = Math.max(0, kaizenSeconds) % 60;
    kaizenTime.textContent = min + ":" + String(sec).padStart(2, "0");
}

function completeKaizenSession() {
    pauseKaizenTimer();
    kaizenTotalMinutes += 15;
    try { localStorage.setItem("cadence_kaizen_minutes", String(kaizenTotalMinutes)); } catch(e) {}
    if (btnKaizenStart) {
        btnKaizenStart.innerHTML = '<svg width="14" height="14"><use href="#icon-check"/></svg> Done!';
        btnKaizenStart.classList.remove("running");
    }
    if (kaizenTime) {
        kaizenTime.style.color = "var(--success)";
        setTimeout(function() {
            if (kaizenTime) kaizenTime.style.color = "var(--accent)";
            resetKaizenTimer();
        }, 2000);
    }
}

// --- Audio Recording (Piano Playing) ---

function toggleAudioRecording() {
    if (isRecordingAudio) {
        stopAudioRecording();
    } else {
        startAudioRecording();
    }
}

function startAudioRecording() {
    audioChunks = [];
    audioBlob = null;
    isRecordingAudio = true;

    if (btnRecordAudio) {
        btnRecordAudio.querySelector("span").textContent = "Stop Recording";
        btnRecordAudio.classList.add("recording");
    }
    if (audioStatus) {
        audioStatus.hidden = false;
        audioStatus.querySelector("span").textContent = "Recording your playing...";
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            var source = audioContext.createMediaStreamSource(stream);
            audioAnalyser = audioContext.createAnalyser();
            audioAnalyser.fftSize = 256;
            source.connect(audioAnalyser);

            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = function(e) {
                if (e.data.size > 0) audioChunks.push(e.data);
            };
            mediaRecorder.onstop = function() {
                audioBlob = new Blob(audioChunks, { type: "audio/webm" });
                stream.getTracks().forEach(function(t) { t.stop(); });
                if (audioContext) audioContext.close();
            };
            mediaRecorder.start();
            updateAudioLevel();
        })
        .catch(function(err) {
            isRecordingAudio = false;
            if (btnRecordAudio) {
                btnRecordAudio.querySelector("span").textContent = "Record Your Playing";
                btnRecordAudio.classList.remove("recording");
            }
            if (audioStatus) audioStatus.hidden = true;
            promptText.innerHTML = '<span style="color: #e07070;">Microphone access denied. Allow mic access to record your playing.</span>';
        });
}

function stopAudioRecording() {
    if (!isRecordingAudio) return;
    isRecordingAudio = false;

    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }

    if (btnRecordAudio) {
        btnRecordAudio.querySelector("span").textContent = "Record Your Playing";
        btnRecordAudio.classList.remove("recording");
    }
    if (audioStatus) audioStatus.hidden = true;
    if (audioLevel) audioLevel.style.width = "0%";
}

function updateAudioLevel() {
    if (!isRecordingAudio || !audioAnalyser) return;

    var dataArray = new Uint8Array(audioAnalyser.frequencyBinCount);
    audioAnalyser.getByteFrequencyData(dataArray);
    var sum = 0;
    for (var i = 0; i < dataArray.length; i++) sum += dataArray[i];
    var avg = sum / dataArray.length;
    var level = Math.min(100, Math.round((avg / 128) * 100));

    if (audioLevel) audioLevel.style.width = level + "%";
    if (isRecordingAudio) requestAnimationFrame(updateAudioLevel);
}

// --- WAV Conversion (for server-side note analysis) ---

function convertBlobToWav(audioBlob, callback) {
    // Decode compressed audio (webm/ogg) to raw PCM via AudioContext
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var reader = new FileReader();

    reader.onload = function(e) {
        ctx.decodeAudioData(e.target.result, function(audioBuffer) {
            var pcm = audioBuffer.getChannelData(0);         // Float32, mono
            var sampleRate = audioBuffer.sampleRate;
            var numSamples = pcm.length;
            var bitsPerSample = 16;
            var bytesPerSample = bitsPerSample / 8;
            var dataLength = numSamples * bytesPerSample;

            // Build WAV header + PCM data
            var buffer = new ArrayBuffer(44 + dataLength);
            var view = new DataView(buffer);

            // RIFF header
            writeString(view, 0, "RIFF");
            view.setUint32(4, 36 + dataLength, true);
            writeString(view, 8, "WAVE");

            // fmt subchunk
            writeString(view, 12, "fmt ");
            view.setUint32(16, 16, true);                    // PCM
            view.setUint16(20, 1, true);                     // format = 1
            view.setUint16(22, 1, true);                     // mono
            view.setUint32(24, sampleRate, true);
            view.setUint32(28, sampleRate * bytesPerSample, true);
            view.setUint16(32, bytesPerSample, true);
            view.setUint16(34, bitsPerSample, true);

            // data subchunk
            writeString(view, 36, "data");
            view.setUint32(40, dataLength, true);

            // Write samples as int16
            var offset = 44;
            for (var i = 0; i < numSamples; i++) {
                var s = Math.max(-1, Math.min(1, pcm[i]));
                view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                offset += 2;
            }

            ctx.close();
            callback(new Blob([buffer], { type: "audio/wav" }));
        }, function(err) {
            // Fallback: send original blob if decode fails
            ctx.close();
            callback(audioBlob);
        });
    };

    reader.readAsArrayBuffer(audioBlob);
}

function writeString(view, offset, str) {
    for (var i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i));
    }
}

// --- Reset ---

function resetToRecord() {
    transcribedText = "";
    isRecording = false;
    if (recognition) {
        recognition.stop();
        recognition = null;
    }
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }
    audioChunks = [];
    audioBlob = null;
    if (audioStatus) audioStatus.hidden = true;
    if (btnRecordAudio) {
        btnRecordAudio.querySelector("span").textContent = "Record Your Playing";
        btnRecordAudio.classList.remove("recording");
    }
    if (isKaizenRunning) pauseKaizenTimer();
    clearInterval(recordingTimer);
    recordingTimer = null;
    if (loadingTimer) clearTimeout(loadingTimer);
    document.getElementById("context").value = "";
    recordingTime.textContent = "0:00";
    loading.hidden = true;
    contextArea.hidden = true;
    screenFeedback.hidden = true;
    screenRecord.hidden = false;
    errorRecovery.hidden = true;
    typeInputArea.hidden = true;
    document.getElementById("type-input-block").hidden = false;
    btnRecord.hidden = false;
    btnStop.hidden = true;
    recordingStatus.hidden = true;
    if (promptText) {
        promptText.innerHTML = 'Tell Cadence what you practiced today.<br><span class="prompt-hint">What went well? What felt hard? What\'s stuck?</span>';
    }
}
