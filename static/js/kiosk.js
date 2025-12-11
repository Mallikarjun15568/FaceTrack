// ---------------- FULLSCREEN AUTO-ENABLE ----------------
function enableFullscreen() {
    const elem = document.documentElement;
    if (elem.requestFullscreen) {
        elem.requestFullscreen().catch(() => {});
    } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
    } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
    }
}
// try once after load (browsers often require user gesture; it's ok if denied)
setTimeout(() => {
    if (!document.fullscreenElement) enableFullscreen();
}, 2000);
document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement) setTimeout(enableFullscreen, 3000);
});


// ---------------- SOUND FEEDBACK ----------------
// Reuse AudioContext where possible (some browsers disallow creating many)
const _sharedAudio = { ctx: null };
function getAudioCtx() {
    if (_sharedAudio.ctx) return _sharedAudio.ctx;
    try {
        _sharedAudio.ctx = new (window.AudioContext || window.webkitAudioContext)();
        return _sharedAudio.ctx;
    } catch (e) {
        return null;
    }
}
function playBeep(frequency = 800, duration = 200) {
    const audioContext = getAudioCtx();
    if (!audioContext) return;
    try {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.frequency.value = frequency;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration / 1000);
        oscillator.start();
        oscillator.stop(audioContext.currentTime + duration / 1000);
    } catch (e) {
        // Audio playback failed silently
    }
}
const sounds = {
    success: () => playBeep(1000, 150),
    error: () => playBeep(400, 300),
    unknown: () => playBeep(600, 200)
};


// ---------------- CAMERA START ----------------
const video = document.getElementById("video");
async function startCamera() {
    if (!video) return console.error("Video element not found");
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480, facingMode: "user" }
        });
        video.srcObject = stream;
        // ensure video plays (some browsers require play call)
        try { await video.play(); } catch (e) { /* ignore */ }
    } catch (error) {
        console.error("Camera Error:", error);
        // Show user-friendly UI if desired
    }
}
startCamera();


// ---------------- UI ELEMENTS ----------------
const waitingBlock = document.getElementById("waiting-block");
const waitingBlockDefaultContent = waitingBlock ? waitingBlock.innerHTML : "";
const employeeCard = document.getElementById("employee-card");
const empPhoto = document.getElementById("emp-photo");
const empName = document.getElementById("emp-name");
const empDept = document.getElementById("emp-dept");
const statusArea = document.getElementById("status-area");
const logsList = document.getElementById("logs-list");

// guard: if essential DOM missing, stop
if (!waitingBlock || !employeeCard || !video) {
    console.error("Kiosk DOM missing elements — check HTML IDs.");
}


// ---------------- STATUS BADGES ----------------
const BADGE = {
    "check-in":  { text:"CHECK-IN SUCCESS",  cls:"bg-green-500 text-white" },
    "check-out": { text:"CHECK-OUT SUCCESS", cls:"bg-sky-500 text-white" },
    "already":   { text:"ALREADY MARKED",    cls:"bg-yellow-400 text-black" },
    "unknown":   { text:"UNKNOWN FACE",      cls:"bg-red-500 text-white" },
};


// ---------------- HELPER FUNCTIONS ----------------
function getCurrentTime() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function makeBadge(status) {
    const div = document.createElement("div");
    const meta = BADGE[status] || { text: status, cls: "bg-gray-200" };
    div.className = `px-6 py-2 rounded-full text-sm font-semibold shadow ${meta.cls}`;
    div.textContent = meta.text;
    return div;
}
function addLog(name, status, time, photo) {
    if (!logsList) return;
    const row = document.createElement("div");
    row.className = "flex items-center gap-3 bg-gray-50 border border-gray-200 p-2 rounded-lg";
    const img = document.createElement("img");
    img.src = photo || "/static/default_user.png";
    img.className = "w-10 h-10 rounded-md border object-cover";
    const meta = document.createElement("div");
    const n = document.createElement("p");
    const s = document.createElement("p");
    n.className = "font-semibold text-gray-800";
    s.className = "text-sm text-gray-500";
    n.textContent = name || "Unknown";
    s.textContent = `${(BADGE[status]||{text:status}).text} • ${time || getCurrentTime()}`;
    meta.appendChild(n); meta.appendChild(s);
    row.appendChild(img); row.appendChild(meta);
    logsList.prepend(row);
    if (logsList.children.length > 5) logsList.removeChild(logsList.lastChild);
}


// ---------------- UPDATE UI AFTER RECOGNITION ----------------
function updateUI(result) {
    console.log("updateUI called with:", result);
    if (!waitingBlock) return;
    
    waitingBlock.innerHTML = waitingBlockDefaultContent;
    waitingBlock.classList.add("hidden");
    employeeCard.classList.remove("hidden");
    
    empName.textContent = result.name || "Unknown";
    empDept.textContent = result.dept || "";
    empPhoto.src = result.photoUrl || "/static/default_user.png";
    
    statusArea.innerHTML = "";
    statusArea.appendChild(makeBadge(result.status));
    
    if (result.status === "check-in" || result.status === "check-out") sounds.success();
    else if (result.status === "already") sounds.error();
    
    if (result.status !== "already") addLog(result.name, result.status, result.time, result.photoUrl);
    
    console.log("UI updated successfully");
}

function showUnknownAlert(time) {
    if (!waitingBlock) return;
    waitingBlock.classList.remove("hidden");
    employeeCard.classList.add("hidden");
    waitingBlock.innerHTML = `
        <p class="font-semibold text-gray-900">Unknown face detected</p>
        <p class="text-xs text-gray-500">Please center your face in the frame and hold still.</p>
        <p class="text-xs text-gray-400 mt-1">Last seen at ${time || getCurrentTime()}</p>
    `;
    sounds.unknown();
}


// ---------------- LIVENESS DETECTION ----------------
let livenessCheckActive = false;
let livenessPassed = true; // always allow recognition
let currentChallenge = null;

// display messages for challenges
function getChallengeMessage(challenge) {
    const messages = {
        "blink": "👁️ Please blink naturally",
        "head_left": "⬅️ Turn your head LEFT",
        "head_right": "➡️ Turn your head RIGHT"
    };
    return messages[challenge] || "Verifying...";
}
function showLivenessChallenge(challenge, progress, message) {
    if (!waitingBlock) return;
    waitingBlock.classList.remove("hidden");
    employeeCard.classList.add("hidden");
    const progressBar = Math.max(0, Math.min(100, progress || 0));
    waitingBlock.innerHTML = `
        <div class="text-center">
            <p class="text-2xl mb-2">${getChallengeMessage(challenge)}</p>
            <p class="text-sm text-gray-600 mb-3">${message || ""}</p>
            <div class="w-full bg-gray-200 rounded-full h-2">
                <div class="bg-blue-500 h-2 rounded-full transition-all" style="width: ${progressBar}%"></div>
            </div>
        </div>
    `;
}


// ---------------- NETWORK + LIVENESS CHECK with backoff ----------------
let consecutiveErrors = 0;
let lastSuccessTime = 0;
const MAX_BACKOFF = 3000; // ms
async function checkLiveness(frameData) {
    return true;  // always pass - liveness disabled
}


// ---------------- POLLING LOOP ----------------
const POLLING_DELAY_MS = 650;  // interval between loops (reduced CPU usage)
let sendingFrame = false;

async function sendFrame() {
    if (sendingFrame) return;
    if (!video || !video.videoWidth || !video.videoHeight) return;

    sendingFrame = true;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);
    const frameData = canvas.toDataURL("image/jpeg", 0.7);

    try {
        // Liveness disabled - always proceed to recognition

        // Step 2: Recognition

        // small debounce: if last success very recent, wait a bit
        const now = Date.now();
        if (now - lastSuccessTime < 500) return;

        const res = await fetch("/kiosk/recognize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ frame: frameData })
        });

        if (!res.ok) {
            // try to display server message if present
            const data = await res.json().catch(() => null);
            // Recognition server error (silent in production)
            // If session expired or forbidden, optionally reload / redirect
            if (res.status === 403 && data && data.message === "Liveness check required") {
                // UI fallback: require liveness again
                resetLiveness();
                showLivenessChallenge("blink", 0, "Session expired — please verify again");
                return;
            }
            return;
        }

        const data = await res.json().catch(() => null);
        if (!data) return;

        if (data.status === "ignore") {
            return;
        }
        if (data.status === "unknown") {
            showUnknownAlert(data.time);
            resetLiveness();
            return;
        }

        // Matched — update UI
        console.log("Recognition result:", data);
        updateUI(data);

        // Reset liveness after showing UI for a short while
        setTimeout(resetLiveness, 3000);

    } catch (err) {
        // Recognition error (silent in production)
    } finally {
        sendingFrame = false;
    }
}

function resetLiveness() {
    livenessCheckActive = false;  // keep liveness disabled
    livenessPassed = true;  // always allow recognition
    currentChallenge = null;
    // restore waitingBlock default (prevents stuck hidden)
    if (waitingBlock) waitingBlock.innerHTML = waitingBlockDefaultContent;
}

// loop driver with setInterval-like scheduling that tolerates drift
async function startRecognitionLoop() {
    while (true) {
        await sendFrame();
        await new Promise(r => setTimeout(r, POLLING_DELAY_MS));
    }
}

startRecognitionLoop();
