// =======================
// KIOSK CAMERA + RECOGNITION
// Enhanced with Advanced Animations
// =======================

// -------- DOM ELEMENTS --------
const video = document.getElementById("kioskVideo");
const startBtn = document.getElementById("startCameraBtn");
const stopBtn = document.getElementById("stopCameraBtn");
const cameraSelect = document.getElementById("cameraSelect");
const adminCameraSelect = document.getElementById("adminCameraSelect");
const exitKioskBtn = document.getElementById("exitKioskBtn");
const statusText = document.getElementById("cameraStatus");
const statusDot = document.getElementById("statusDot");

const scanRing = document.getElementById("scanRing");
const scanBorderEffect = document.getElementById("scanBorderEffect");
const scanStatusText = document.getElementById("scanStatusText");
const scanSubText = document.getElementById("scanSubText");
const waitingBlock = document.getElementById("waiting-block");
const employeeCard = document.getElementById("employee-card");
const empPhoto = document.getElementById("emp-photo");
const empName = document.getElementById("emp-name");
const empDept = document.getElementById("emp-dept");
const empStatus = document.getElementById("emp-status");
const unknownCard = document.getElementById("unknown-card");
const resultsPlaceholder = document.getElementById("resultsPlaceholder");
const logsList = document.getElementById("logs-list");

// -------- STATE --------
let stream = null;
let cameraRunning = false;
let startingCamera = false;
let recognitionRunning = false;
let selectedDeviceId = null;
let sendingFrame = false;

// Confetti fired flag to ensure confetti runs only once
let confettiFired = false;

let lastSpokenName = null;
let lastSpokenTime = 0;
const VOICE_COOLDOWN_MS = 5000;
let hardCooldownUntil = 0;

const RECOGNITION_COOLDOWN_MS = parseInt(localStorage.getItem('recognitionCooldownMs') || '4000', 10);

// Settings state
let voiceEnabled = true;
let cameraSwitchAllowed = true;
let showCameraStatus = true;

// ===== Enhanced Scan Ring State Helpers with Animations =====
function setScanIdle() {
    scanRing.className = "relative w-56 h-56 rounded-full border-3 border-gray-400 flex items-center justify-center transition-all duration-500 shadow-lg";
    
    if (scanBorderEffect) {
        scanBorderEffect.style.opacity = '0';
    }
    
    scanStatusText.textContent = "CAMERA INACTIVE";
    scanSubText.textContent = "Tap Start Camera to begin";
    scanStatusText.className = "text-white font-bold text-base drop-shadow-2xl tracking-wide";
    
    // Do not replace DOM nodes here. Update existing text nodes only.
    
    if (waitingBlock) {
        const primary = waitingBlock.querySelector('p');
        const secondary = waitingBlock.querySelector('p.text-sm');
        if (primary) primary.textContent = 'Ready for identification';
        if (secondary) secondary.textContent = 'Please look directly at the camera';
    }
    if (resultsPlaceholder) resultsPlaceholder.classList.remove('hidden');
}

function setScanScanning() {
    scanRing.className = "relative w-56 h-56 rounded-full border-3 border-blue-500 flex items-center justify-center transition-all duration-500 shadow-lg animate-pulse-slow";
    
    // Enable rotating border effect
    if (scanBorderEffect) {
        scanBorderEffect.style.opacity = '0.5';
    }
    
    scanStatusText.textContent = "VERIFYING IDENTITY";
    scanSubText.textContent = "Please keep your face steady";
    scanStatusText.className = "text-blue-400 font-bold text-base drop-shadow-2xl tracking-wide animate-pulse";
    
    // Do not recreate DOM nodes; only update text and classes to preserve element references
    
    if (waitingBlock) {
        const primary = waitingBlock.querySelector('p');
        const secondary = waitingBlock.querySelector('p.text-sm');
        if (primary) primary.textContent = 'Scanning face';
        if (secondary) secondary.textContent = 'Please keep your face steady';
        waitingBlock.classList.remove('hidden');
        if (employeeCard) employeeCard.classList.add('hidden');
        if (unknownCard) unknownCard.classList.add('hidden');
    }
    if (resultsPlaceholder) resultsPlaceholder.classList.add('hidden');
}

function setScanSuccess() {
    scanRing.className = "relative w-56 h-56 rounded-full border-3 border-green-500 flex items-center justify-center transition-all duration-500 shadow-lg shadow-green-500/30 animate-scale-in";
    
    if (scanBorderEffect) {
        scanBorderEffect.style.opacity = '0';
    }
    
    scanStatusText.textContent = "✓ ID VERIFIED";
    scanSubText.textContent = "Attendance recorded";
    scanStatusText.className = "text-green-400 font-bold text-xl drop-shadow-2xl tracking-wide";
    
    // Preserve DOM nodes; update text instead of replacing elements
    
    if (resultsPlaceholder) resultsPlaceholder.classList.add('hidden');
    
    // Confetti effect
    createConfetti();
    
    setTimeout(() => {
        if (cameraRunning) setScanScanning();
    }, 2500);
}

function setScanError() {
    scanRing.className = "relative w-56 h-56 rounded-full border-4 border-red-500 flex items-center justify-center transition-all duration-500 shadow-2xl shadow-red-500/50 animate-shake";
    
    if (scanBorderEffect) {
        scanBorderEffect.style.opacity = '0';
    }
    
    scanStatusText.textContent = "FACE NOT RECOGNIZED";
    scanSubText.textContent = "Please try again";
    scanStatusText.className = "text-red-400 font-bold text-xl drop-shadow-2xl tracking-wide";
    
    // Preserve DOM nodes; update text instead of replacing elements
    
    if (resultsPlaceholder) resultsPlaceholder.classList.add('hidden');
    
    setTimeout(() => {
        if (cameraRunning) setScanScanning();
    }, 2500);
}

// ===== Confetti Animation =====
function createConfetti() {
    if (confettiFired) return;
    confettiFired = true;
    const colors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'];
    const confettiCount = 30;
    
    for (let i = 0; i < confettiCount; i++) {
        const confetti = document.createElement('div');
        confetti.style.position = 'fixed';
        confetti.style.width = '10px';
        confetti.style.height = '10px';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.left = '50%';
        confetti.style.top = '50%';
        confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
        confetti.style.zIndex = '9999';
        confetti.style.pointerEvents = 'none';
        
        document.body.appendChild(confetti);
        
        const angle = (Math.PI * 2 * i) / confettiCount;
        const velocity = 3 + Math.random() * 4;
        const tx = Math.cos(angle) * velocity * 50;
        const ty = Math.sin(angle) * velocity * 50;
        
        confetti.animate([
            { transform: 'translate(0, 0) rotate(0deg)', opacity: 1 },
            { transform: `translate(${tx}px, ${ty}px) rotate(${Math.random() * 360}deg)`, opacity: 0 }
        ], {
            duration: 800 + Math.random() * 400,
            easing: 'cubic-bezier(0, .9, .57, 1)'
        }).onfinish = () => confetti.remove();
    }
}

// =======================
// CLOCK UPDATE with Animation
// =======================
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });
    const clockEl = document.getElementById('currentTime');
    if (clockEl) {
        if (clockEl.textContent !== timeStr) {
            clockEl.style.transform = 'scale(1.05)';
            setTimeout(() => clockEl.style.transform = 'scale(1)', 200);
        }
        clockEl.textContent = timeStr;
    }
}
setInterval(updateClock, 1000);
updateClock();

// =======================
// AUDIO & SOUND
// =======================
const _sharedAudio = { ctx: null };
function getAudioCtx() {
    if (_sharedAudio.ctx) return _sharedAudio.ctx;
    try {
        _sharedAudio.ctx = new (window.AudioContext || window.webkitAudioContext)();
        return _sharedAudio.ctx;
    } catch {
        return null;
    }
}

function playBeep(freq = 800, dur = 200) {
    // Disabled per request
    return;
}

// =======================
// SPEAK with Animation
// =======================
function canSpeak(name) {
    if (!voiceEnabled) return false;
    
    const now = Date.now();
    if (lastSpokenName === name && (now - lastSpokenTime) < VOICE_COOLDOWN_MS) {
        return false;
    }
    lastSpokenName = name;
    lastSpokenTime = now;
    return true;
}

window.speak = function (msg) {
    if (!voiceEnabled) return;
    if (!("speechSynthesis" in window)) return;
    const u = new SpeechSynthesisUtterance(msg);
    u.lang = "en-IN";
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
};

// =======================
// CAMERA DETECTION
// =======================
async function loadCameras() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        if (!cameraSelect) return;
        
        const currentValue = cameraSelect.value;
        cameraSelect.innerHTML = '<option value="">📹 Select Camera Device</option>';
        
        devices.forEach((d, idx) => {
            if (d.kind === "videoinput") {
                const o = document.createElement("option");
                o.value = d.deviceId;
                o.textContent = d.label || `Camera ${idx + 1}`;
                cameraSelect.appendChild(o);
            }
        });
        
        if (currentValue) cameraSelect.value = currentValue;
    } catch (err) {
        console.error("Error loading cameras:", err);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadCameras();
    // Add initial page load animation
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s';
        document.body.style.opacity = '1';
    }, 100);
});

navigator.mediaDevices.ondevicechange = async () => {
    await loadCameras();
    console.log("📹 Camera devices updated");
};

// =======================
// START CAMERA with Animation
// =======================
if (startBtn) {
    startBtn.addEventListener("click", async () => {
        if (cameraRunning || startingCamera) return;
        // Kiosk mode: use browser default camera (no employee-facing select)
        
        // Add loading animation to button
        startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
        startBtn.disabled = true;
        
        try {
            if (stream) {
                stream.getTracks().forEach(t => t.stop());
                video.srcObject = null;
                stream = null;
            }

            startingCamera = true;

            stream = await navigator.mediaDevices.getUserMedia({ video: true });

            video.muted = true;
            video.playsInline = true;
            video.srcObject = stream;

            try {
                await video.play();
            } catch (playErr) {
                if (playErr.name === 'AbortError') {
                    await new Promise(r => setTimeout(r, 120));
                    await video.play();
                } else {
                    throw playErr;
                }
            }

            startingCamera = false;
            cameraRunning = true;
            
            startBtn.classList.add("hidden");
            if (stopBtn) stopBtn.classList.remove("hidden");
            
            if (cameraSelect) {
                if (!cameraSwitchAllowed) {
                    cameraSelect.disabled = true;
                    cameraSelect.classList.add("opacity-50", "cursor-not-allowed");
                } else {
                    cameraSelect.classList.add("hidden");
                }
            }
            
            if (statusText) {
                statusText.textContent = "Camera Active";
                statusText.classList.add('animate-pulse-slow');
            }
            if (statusDot) {
                statusDot.classList.remove("bg-red-500");
                statusDot.classList.add("bg-green-500");
            }

            setScanScanning();
            await loadCameras();

            startRecognitionLoop();
        } catch (err) {
            alert("❌ Camera access denied or unavailable");
            console.error("Camera error:", err);
            startingCamera = false;
            startBtn.innerHTML = '<i class="fas fa-play text-sm"></i> Start Camera';
            startBtn.disabled = false;
        }
    });
}

// =======================
// STOP CAMERA
// =======================
if (stopBtn) {
    stopBtn.addEventListener("click", () => {
        if (!stream) return;

        stopRecognitionLoop();
        stream.getTracks().forEach(t => t.stop());
        video.srcObject = null;
        stream = null;

        cameraRunning = false;
        stopBtn.classList.add("hidden");
        if (startBtn) {
            startBtn.classList.remove("hidden");
            startBtn.innerHTML = '<i class="fas fa-play text-sm"></i> Start Camera';
            startBtn.disabled = false;
        }
        
        if (cameraSelect) {
            cameraSelect.disabled = false;
            cameraSelect.classList.remove("opacity-50", "cursor-not-allowed", "hidden");
        }
        
        if (statusText) {
            statusText.textContent = "Camera Off";
            statusText.classList.remove('animate-pulse-slow');
        }
        if (statusDot) {
            statusDot.classList.remove("bg-green-500");
            statusDot.classList.add("bg-red-500");
        }

        setScanIdle();
        
        if (waitingBlock) waitingBlock.classList.remove("hidden");
        if (employeeCard) employeeCard.classList.add("hidden");
        if (unknownCard) unknownCard.classList.add("hidden");
    });
}

// =======================
// UI UPDATE with Animations
// =======================
function updateUI(data) {
    if (waitingBlock) waitingBlock.classList.add("hidden");
    if (unknownCard) unknownCard.classList.add("hidden");
    
    if (employeeCard) {
        employeeCard.classList.remove("hidden");
        employeeCard.classList.add("animate-scale-in");
    }

    if (empName) empName.textContent = data.name || "Unknown";
    if (empDept) empDept.textContent = data.dept || "";
    if (empPhoto) {
        empPhoto.src = data.photoUrl || "/static/default_user.png";
        empPhoto.classList.add("animate-scale-in");
    }

    if (empStatus) {
        empStatus.className = 'px-4 py-2 text-sm font-bold rounded-xl shadow-lg';
        
        if (data.status === "check-in") {
            empStatus.textContent = "✓ CHECKED IN";
            empStatus.classList.add('bg-gradient-to-r', 'from-green-600', 'to-emerald-600', 'text-white', 'animate-pulse-slow');
        } else if (data.status === "check-out") {
            empStatus.textContent = "→ CHECKED OUT";
            empStatus.classList.add('bg-gradient-to-r', 'from-blue-600', 'to-indigo-600', 'text-white', 'animate-pulse-slow');
        } else if (data.status === "already") {
            empStatus.textContent = "⚠ ALREADY MARKED";
            empStatus.classList.add('bg-gradient-to-r', 'from-amber-600', 'to-orange-600', 'text-white');
        } else {
            empStatus.textContent = data.status || "";
        }
    }

    if (data.status === "check-in") {
        playBeep(1000, 150);
        if (canSpeak(data.name)) speak(`Welcome ${data.name}`);
        setScanSuccess();
    } else if (data.status === "check-out") {
        playBeep(900, 150);
        if (canSpeak(data.name)) speak(`Goodbye ${data.name}`);
        setScanSuccess();
    } else if (data.status === "already") {
        playBeep(400, 300);
        if (canSpeak(data.name)) speak(`${data.name}, already marked`);
    }

    addLog(data.name, data.status, data.time, data.photoUrl);
}

// =======================
// LOGS with Slide Animation
// =======================
function addLog(name, status, time, photo) {
    if (!status) return;
    if (!logsList) return;
    
    const row = document.createElement("div");
    row.className = "flex items-center gap-4 bg-gradient-to-r from-gray-50 to-white border-2 border-gray-200 p-4 rounded-xl hover:shadow-xl transition-all duration-300 hover:scale-[1.02] animate-fade-in";

    const img = document.createElement("img");
    img.src = photo || "/static/default_user.png";
    img.className = "w-12 h-12 rounded-xl border border-gray-200 object-cover shadow-lg";

    const meta = document.createElement("div");
    meta.className = "flex-1 min-w-0";

    const nameEl = document.createElement("p");
    nameEl.className = "font-bold text-gray-900 text-base truncate";
    nameEl.textContent = name || "Unknown";

    const statusEl = document.createElement("p");
    statusEl.className = "text-xs text-gray-600 mt-1 font-medium";
    const statusIcon = status === "check-in" ? "✓" : status === "check-out" ? "→" : "⚠";
    statusEl.textContent = `${statusIcon} ${status.toUpperCase()} • ${time || new Date().toLocaleTimeString()}`;

    meta.appendChild(nameEl);
    meta.appendChild(statusEl);
    row.appendChild(img);
    row.appendChild(meta);

    logsList.prepend(row);
    
    while (logsList.children.length > 4) {
        logsList.removeChild(logsList.lastChild);
    }
}

// =======================
// RECOGNITION LOOP
// =======================
const POLLING_DELAY_MS = 1200;

async function sendFrame() {
    if (!cameraRunning || sendingFrame || !video.videoWidth) return;
    sendingFrame = true;

    try {
        if (Date.now() < hardCooldownUntil) return;

        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);
        const frame = canvas.toDataURL("image/jpeg", 0.7);

        const res = await fetch("/kiosk/recognize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ frame })
        });
        
        const data = await res.json();
        if (!data) return;

        // --- UI mapping for liveness WAIT messages ---
        if (data.status === "WAIT") {
            const msg = data.message || "";

            // No face detected
            if (msg.includes("No face") || msg.toLowerCase().includes("position your face")) {
                setScanIdle();
                if (scanSubText) scanSubText.textContent = "Please face the camera";
                if (waitingBlock) {
                    waitingBlock.classList.remove('hidden');
                    if (employeeCard) employeeCard.classList.add('hidden');
                    if (unknownCard) unknownCard.classList.add('hidden');
                }
            }
            // Multiple faces
            else if (msg.toLowerCase().includes("multiple")) {
                setScanIdle();
                if (scanSubText) scanSubText.textContent = "Only one person at a time";
            }
            // Analyzing / collecting frames
            else if (msg.toLowerCase().includes("analyzing")) {
                setScanScanning();
                if (scanSubText) scanSubText.textContent = "Please stay still... Verifying";
            }
            // Pass ratio feedback (backend: "Pass Ratio: xx.xx% | Conf: y.y")
            else if (msg.toLowerCase().includes("pass ratio")) {
                const m = msg.match(/Pass Ratio:\s*([0-9.]+)%/i);
                const ratio = m ? parseFloat(m[1]) / 100 : null;
                if (ratio !== null) {
                    if (ratio < 0.4) {
                        setScanScanning();
                        if (scanSubText) scanSubText.textContent = "Please blink once";
                    } else if (ratio < 0.6) {
                        setScanScanning();
                        if (scanSubText) scanSubText.textContent = "Good. Hold steady";
                    } else {
                        setScanSuccess();
                        if (scanSubText) scanSubText.textContent = "Verified. Marking attendance…";
                    }
                } else {
                    setScanScanning();
                    if (scanSubText) scanSubText.textContent = msg;
                }
            }
            // Generic liveness feedback
            else {
                setScanScanning();
                if (scanSubText) scanSubText.textContent = msg || "Verifying...";
            }

            // Do not proceed to recognition; poll again
            return;
        }

        if (data.status === "unknown") {
            playBeep(600, 200);
            if (canSpeak("unknown")) speak("Face not recognized. Please try again");
            showUnknownCard();
            if (scanSubText) scanSubText.textContent = "Face not recognized. Try again";
            hardCooldownUntil = Date.now() + RECOGNITION_COOLDOWN_MS;
            return;
        }

        updateUI(data);
        hardCooldownUntil = Date.now() + RECOGNITION_COOLDOWN_MS;

    } catch (err) {
        console.error("Recognition error:", err);
    } finally {
        sendingFrame = false;
    }
}

async function startRecognitionLoop() {
    if (recognitionRunning) return;
    recognitionRunning = true;
    while (recognitionRunning) {
        await sendFrame();
        await new Promise(r => setTimeout(r, POLLING_DELAY_MS));
    }
}

function stopRecognitionLoop() {
    recognitionRunning = false;
}

// =======================
// SHOW UNKNOWN CARD
// =======================
function showUnknownCard() {
    if (!unknownCard || !waitingBlock || !employeeCard) return;
    
    waitingBlock.classList.add('hidden');
    employeeCard.classList.add('hidden');
    unknownCard.classList.remove('hidden');
    unknownCard.classList.add('animate-shake');
    
    setScanError();

    setTimeout(() => {
        unknownCard.classList.add('hidden');
        unknownCard.classList.remove('animate-shake');
        waitingBlock.classList.remove('hidden');
    }, 2500);
}

// =======================
// SETTINGS + PIN LOGIC
// =======================
const openSettingsBtn = document.getElementById("openSettingsBtn");
const openExitBtn = document.getElementById("openExitBtn");
const pinModal = document.getElementById("pinModal");
const pinInput = document.getElementById("pinInput");
const pinVerify = document.getElementById("pinVerify");
const pinCancel = document.getElementById("pinCancel");
const settingsPanel = document.getElementById("settingsPanel");
const closeSettingsBtn = document.getElementById("closeSettingsBtn");

const voiceToggle = document.getElementById("voiceToggle");
const cameraSwitchToggle = document.getElementById("cameraSwitchToggle");
const cameraStatusToggle = document.getElementById("cameraStatusToggle");
const cameraStatusBlock = document.getElementById("cameraStatusBlock");

let pendingExit = false;

function updateToggleUI(toggleElement, isEnabled) {
    const toggle = toggleElement.querySelector(".toggle-switch");
    const knob = toggleElement.querySelector(".toggle-knob");
    
    if (!toggle || !knob) return;
    
    if (isEnabled) {
        toggle.classList.remove("bg-gray-400");
        toggle.classList.add("bg-green-500");
        knob.classList.remove("translate-x-0");
        knob.classList.add("translate-x-7");
    } else {
        toggle.classList.remove("bg-green-500");
        toggle.classList.add("bg-gray-400");
        knob.classList.remove("translate-x-7");
        knob.classList.add("translate-x-0");
    }
}

if (openSettingsBtn && pinModal) {
    openSettingsBtn.addEventListener("click", () => {
        pendingExit = false;
        pinInput.value = "";
        pinModal.classList.remove("hidden");
        pinModal.classList.add("flex");
        setTimeout(() => pinInput.focus(), 50);
    });
}

// Wire admin exit button inside settings panel
if (exitKioskBtn && pinModal) {
    exitKioskBtn.addEventListener("click", () => {
        pendingExit = true;
        pinInput.value = "";
        pinModal.classList.remove("hidden");
        pinModal.classList.add("flex");
        setTimeout(() => pinInput.focus(), 50);
    });
}

if (pinCancel && pinModal) {
    pinCancel.addEventListener("click", () => {
        pendingExit = false;
        pinModal.classList.add("hidden");
        pinModal.classList.remove("flex");
    });
}

if (pinVerify) {
    pinVerify.addEventListener("click", async () => {
        const pin = (pinInput.value || "").trim();
        if (!pin) {
            pinInput.classList.add('animate-shake');
            setTimeout(() => pinInput.classList.remove('animate-shake'), 500);
            alert("Enter PIN");
            pinInput.focus();
            return;
        }

        if (pendingExit) {
            pinVerify.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            pinVerify.disabled = true;
            try {
                const res = await fetch('/kiosk/exit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pin })
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.success) {
                    window.location.href = data.redirect || '/';
                } else {
                    alert(data.message || 'Invalid PIN');
                    pinInput.value = '';
                    pinInput.focus();
                }
            } catch (err) {
                console.error(err);
                alert('Network error. Try again.');
            } finally {
                pinVerify.innerHTML = 'Verify';
                pinVerify.disabled = false;
                pendingExit = false;
            }
            return;
        }

        pinVerify.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        pinVerify.disabled = true;
        try {
            const res = await fetch('/kiosk/verify_pin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin })
            });

            const data = await res.json().catch(() => ({}));

            if (res.ok && data.success) {
                pinModal.classList.add("hidden");
                pinModal.classList.remove("flex");
                // Populate admin camera list before showing settings
                try { await loadAdminCameras(); } catch (e) { console.error(e); }
                settingsPanel.classList.remove("translate-x-full");
            } else {
                alert(data.message || "Invalid PIN");
                pinInput.value = "";
                pinInput.focus();
            }
        } catch (err) {
            console.error(err);
            alert("Network error. Try again.");
        } finally {
            pinVerify.innerHTML = 'Verify';
            pinVerify.disabled = false;
        }
    });
}

if (pinInput) {
    pinInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && pinVerify) {
            pinVerify.click();
        }
    });
}

if (closeSettingsBtn && settingsPanel) {
    closeSettingsBtn.addEventListener("click", () => {
        settingsPanel.classList.add("translate-x-full");
    });
}

if (voiceToggle) {
    voiceToggle.addEventListener("click", () => {
        voiceEnabled = !voiceEnabled;
        updateToggleUI(voiceToggle, voiceEnabled);
        console.log("🔊 Voice:", voiceEnabled ? "ON" : "OFF");
    });
}

if (cameraSwitchToggle) {
    cameraSwitchToggle.addEventListener("click", () => {
        cameraSwitchAllowed = !cameraSwitchAllowed;
        updateToggleUI(cameraSwitchToggle, cameraSwitchAllowed);
        
        if (cameraSelect) {
            if (cameraRunning && !cameraSwitchAllowed) {
                cameraSelect.disabled = true;
                cameraSelect.classList.add("opacity-50", "cursor-not-allowed");
            } else if (!cameraRunning) {
                cameraSelect.disabled = false;
                cameraSelect.classList.remove("opacity-50", "cursor-not-allowed");
            }
        }
        
        console.log("📹 Camera Switch:", cameraSwitchAllowed ? "ALLOWED" : "BLOCKED");
    });
}

if (cameraStatusToggle) {
    cameraStatusToggle.addEventListener("click", () => {
        showCameraStatus = !showCameraStatus;
        updateToggleUI(cameraStatusToggle, showCameraStatus);
        if (cameraStatusBlock) {
            if (showCameraStatus) {
                cameraStatusBlock.classList.remove('hidden');
            } else {
                cameraStatusBlock.classList.add('hidden');
            }
        }
        console.log("ℹ️ Show Camera Status:", showCameraStatus ? "ON" : "OFF");
    });
}

// ===== Admin camera loader (populates admin-only select in settings) =====
async function loadAdminCameras() {
    try {
        if (!adminCameraSelect) return;
        const devices = await navigator.mediaDevices.enumerateDevices();
        adminCameraSelect.innerHTML = '';
        devices.forEach((d, idx) => {
            if (d.kind === 'videoinput') {
                const o = document.createElement('option');
                o.value = d.deviceId;
                o.textContent = d.label || `Camera ${idx + 1}`;
                adminCameraSelect.appendChild(o);
            }
        });
    } catch (err) {
        console.error('Error loading admin cameras:', err);
    }
}