// =======================
// KIOSK CAMERA + RECOGNITION
// Enhanced with Advanced Animations
// =======================

// -------- DOM ELEMENTS --------
const video = document.getElementById("kioskVideo");
const kioskFaceCanvas = document.getElementById("kioskFaceCanvas");
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

// Face detection UI elements
const distanceMeter = document.getElementById("distanceMeter");
const distanceIcon = document.getElementById("distanceIcon");
const distanceText = document.getElementById("distanceText");
const lightingMeter = document.getElementById("lightingMeter");
const lightingIcon = document.getElementById("lightingIcon");
const lightingText = document.getElementById("lightingText");
const confidenceScore = document.getElementById("confidenceScore");
const confidenceValue = document.getElementById("confidenceValue");
const guidanceText = document.getElementById("guidanceText");

// Centralized scan message setter — single source of truth for scanSubText
function setScanMessage(text) {
    if (scanSubText) scanSubText.textContent = text;
    // Also mirror important guidance to the guidanceText element so
    // backend liveness messages appear without being overwritten.
    if (guidanceText) {
        guidanceText.textContent = text;
        guidanceText.style.display = "block";
        guidanceText.style.visibility = "visible";
    }
}

// Safe text setter to avoid "Cannot set properties of null" errors
function safeText(el, text) {
    if (el) el.textContent = text;
}

// Safe class setter to avoid null errors
function safeClass(el, className) {
    if (el) el.className = className;
}

// Camera inactive overlay helpers
function showCameraInactive() {
    const el = document.getElementById("cameraInactiveOverlay");
    if (el) el.classList.remove("hidden");
}

function hideCameraInactive() {
    const el = document.getElementById("cameraInactiveOverlay");
    if (el) el.classList.add("hidden");
}

// -------- STATE --------
let stream = null;
let cameraRunning = false;
let startingCamera = false;
let recognitionRunning = false;
let selectedDeviceId = null;
let sendingFrame = false;
let currentFacingMode = 'user'; // 'user' = front, 'environment' = back

// Expose to window for mobile flip script
window.stream = stream;
window.cameraRunning = cameraRunning;
window.startingCamera = startingCamera;
window.currentFacingMode = currentFacingMode;

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
    safeText(scanStatusText, "CAMERA INACTIVE");
    // scanSubText is controlled centrally via setScanMessage()
    safeClass(scanStatusText, "text-white font-bold text-base drop-shadow-2xl tracking-wide");

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
    safeText(scanStatusText, "VERIFYING IDENTITY");
    // scanSubText is controlled centrally via setScanMessage()
    safeClass(scanStatusText, "text-blue-400 font-bold text-base drop-shadow-2xl tracking-wide animate-pulse");

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
    safeText(scanStatusText, "✓ ID VERIFIED");
    // scanSubText is controlled centrally via setScanMessage()
    safeClass(scanStatusText, "text-green-400 font-bold text-xl drop-shadow-2xl tracking-wide");

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
    safeText(scanStatusText, "FACE NOT RECOGNIZED");
    // scanSubText is controlled centrally via setScanMessage()
    safeClass(scanStatusText, "text-red-400 font-bold text-xl drop-shadow-2xl tracking-wide");

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
        // Request permission first to get device labels
        let permissionGranted = false;
        try {
            const testStream = await navigator.mediaDevices.getUserMedia({ video: true });
            testStream.getTracks().forEach(track => track.stop());
            permissionGranted = true;
            console.log('📹 Camera permission granted');
        } catch (permErr) {
            console.warn('📹 Camera permission needed:', permErr);
        }

        const devices = await navigator.mediaDevices.enumerateDevices();
        if (!cameraSelect) return;

        const videoDevices = devices.filter(d => d.kind === "videoinput");
        console.log(`📹 Found ${videoDevices.length} camera device(s)`);

        const currentValue = cameraSelect.value;
        cameraSelect.innerHTML = '<option value="">📹 Select Camera Device</option>';

        videoDevices.forEach((d, idx) => {
            const o = document.createElement("option");
            o.value = d.deviceId;

            // Better labeling with mobile-friendly names
            let label = d.label;
            if (!label || label === '') {
                // Detect front/back on mobile
                if (idx === 0) {
                    label = `🤳 Front Camera`;
                } else if (idx === 1) {
                    label = `📸 Back Camera`;
                } else {
                    label = `📹 Camera ${idx + 1}`;
                }
            } else if (label.toLowerCase().includes('front')) {
                label = `🤳 ${label}`;
            } else if (label.toLowerCase().includes('back') || label.toLowerCase().includes('rear')) {
                label = `📸 ${label}`;
            }

            o.textContent = label;
            cameraSelect.appendChild(o);
            console.log(`   📹 ${label}`);
        });

        if (currentValue && videoDevices.some(d => d.deviceId === currentValue)) {
            cameraSelect.value = currentValue;
        }
    } catch (err) {
        console.error("❌ Error loading cameras:", err);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadCameras();

    // Hide all status indicators on load
    if (distanceMeter) {
        distanceMeter.classList.add("hidden");
        distanceMeter.style.display = "none";
    }
    if (lightingMeter) {
        lightingMeter.classList.add("hidden");
        lightingMeter.style.display = "none";
    }
    if (guidanceText) guidanceText.style.display = "none";

    // Add initial page load animation
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s';
        document.body.style.opacity = '1';
    }, 100);

    // Show camera count after loading
    setTimeout(() => {
        if (cameraSelect && cameraSelect.options.length > 1) {
            console.log(`✅ ${cameraSelect.options.length - 1} camera(s) available for selection`);
        }
    }, 1000);
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

            // Get selected device ID from admin camera select (if available)
            let selectedDevice = null;
            if (adminCameraSelect && adminCameraSelect.value) {
                selectedDevice = adminCameraSelect.value;
                console.log('📹 Using admin selected camera:', selectedDevice);
            }

            // Mobile-friendly camera constraints
            const constraints = {
                video: selectedDevice ? {
                    deviceId: { exact: selectedDevice },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } : {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user' // Front camera for face recognition
                },
                audio: false
            };

            console.log('📱 Requesting camera access (mobile-friendly)...');
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            window.stream = stream;

            video.muted = true;
            video.playsInline = true; // Critical for iOS
            video.setAttribute('playsinline', ''); // iOS Safari fix
            video.setAttribute('webkit-playsinline', ''); // Old iOS fix
            video.srcObject = stream;

            try {
                await video.play();

                // Hide the camera-inactive overlay as soon as playback starts
                try {
                    hideCameraInactive();
                } catch (e) { /* ignore */ }

                // Smooth fade-in animation
                setTimeout(() => {
                    video.style.opacity = '1';
                }, 100);
            } catch (playErr) {
                if (playErr.name === 'AbortError') {
                    await new Promise(r => setTimeout(r, 120));
                    await video.play();
                    try {
                        hideCameraInactive();
                    } catch (e) { /* ignore */ }
                    setTimeout(() => {
                        video.style.opacity = '1';
                    }, 100);
                } else {
                    throw playErr;
                }
            }

            startingCamera = false;
            cameraRunning = true;
            window.cameraRunning = true;
            window.startingCamera = false;

            // Initialize canvas for face box
            if (kioskFaceCanvas) {
                const rect = video.getBoundingClientRect();
                kioskFaceCanvas.width = rect.width;
                kioskFaceCanvas.height = rect.height;
                console.log('✅ Canvas initialized:', kioskFaceCanvas.width, 'x', kioskFaceCanvas.height);

                // Draw static guide box once on camera start
                try {
                    drawKioskFaceBox();
                } catch (e) { /* ignore */ }

                // Show simple guidance when camera is on
                if (guidanceText) {
                    guidanceText.textContent = "Align your face inside the box";
                    guidanceText.style.display = 'block';
                    guidanceText.style.visibility = 'visible';
                }
            }

            startBtn.classList.add("hidden");
            if (stopBtn) stopBtn.classList.remove("hidden");

            // Show flip button on mobile
            const flipBtn = document.getElementById("flipCameraBtn");
            if (flipBtn && window.innerWidth < 1024) {
                flipBtn.classList.remove("hidden");
            }

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

        // Clear all detection UI (clear static guide box)
        if (kioskFaceCanvas) {
            const ctx = kioskFaceCanvas.getContext('2d');
            if (ctx) ctx.clearRect(0, 0, kioskFaceCanvas.width, kioskFaceCanvas.height);
        }

        if (distanceMeter) {
            distanceMeter.classList.add("hidden");
            distanceMeter.style.display = "none";
        }
        if (lightingMeter) {
            lightingMeter.classList.add("hidden");
            lightingMeter.style.display = "none";
        }
        if (guidanceText) guidanceText.style.display = "none";

        // Show camera inactive overlay when camera is stopped
        try {
            showCameraInactive();
        } catch (e) { /* ignore */ }

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
    console.log('Updating UI with:', data);

    // Hide all status cards first
    if (waitingBlock) {
        waitingBlock.classList.add("hidden");
        waitingBlock.style.display = 'none';
    }
    if (unknownCard) {
        unknownCard.classList.add("hidden");
        unknownCard.style.display = 'none';
    }
    if (resultsPlaceholder) {
        resultsPlaceholder.classList.add("hidden");
        resultsPlaceholder.style.display = 'none';
    }

    // Update employee data BEFORE showing card
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

    // NOW show the employee card with multiple methods
    if (employeeCard) {
        employeeCard.classList.remove("hidden");
        employeeCard.style.display = 'block';
        employeeCard.style.visibility = 'visible';
        employeeCard.style.opacity = '1';
        employeeCard.classList.add("animate-scale-in");
        console.log('Employee card should be visible now', {
            display: employeeCard.style.display,
            classList: employeeCard.classList.toString(),
            visibility: employeeCard.style.visibility
        });
    }

    if (data.status === "check-in") {
        playBeep(1000, 150);
        if (canSpeak(data.name)) speak(`Welcome ${data.name}`);
        setScanMessage(`Welcome ${data.name}`);
        setScanSuccess();
    } else if (data.status === "check-out") {
        playBeep(900, 150);
        if (canSpeak(data.name)) speak(`Goodbye ${data.name}`);
        setScanMessage(`Goodbye ${data.name}`);
        setScanSuccess();
    } else if (data.status === "already") {
        playBeep(400, 300);
        if (canSpeak(data.name)) speak(`${data.name}, already marked`);
        setScanMessage(`${data.name}, already marked`);
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
// FACE DETECTION FEEDBACK
// =======================

// Calculate distance from camera based on face box size
function calculateDistance(faceBox) {
    if (!faceBox || !faceBox.width || !faceBox.height) return "unknown";
    const faceSize = (faceBox.width + faceBox.height) / 2;
    const videoWidth = video.videoWidth || 640;
    const relativeFaceSize = faceSize / videoWidth;

    // Thresholds: < 0.15 = too far, 0.15-0.4 = perfect, > 0.4 = too close
    if (relativeFaceSize < 0.15) return "far";
    if (relativeFaceSize > 0.4) return "close";
    return "perfect";
}

// Analyze lighting quality from image data
function analyzeLighting(canvas) {
    if (!canvas) return "unknown";
    const ctx = canvas.getContext("2d");
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    let totalBrightness = 0;
    const sampleSize = Math.min(10000, data.length / 4); // Sample pixels

    for (let i = 0; i < sampleSize * 4; i += 4) {
        const brightness = (data[i] + data[i+1] + data[i+2]) / 3;
        totalBrightness += brightness;
    }

    const avgBrightness = totalBrightness / sampleSize;

    // Thresholds: < 60 = dark, 60-200 = good, > 200 = bright
    if (avgBrightness < 60) return "dark";
    if (avgBrightness > 200) return "bright";
    return "good";
}

// Update face detection UI with real-time feedback
function updateFaceDetection(detected, faceBox, confidence, canvas) {
    // Oval frame removed - only canvas box and indicators remain

    if (detected && faceBox) {
        // Calculate and show distance - clean compact panel
        const distance = calculateDistance(faceBox);
        if (distanceMeter && distanceText && cameraRunning) {
            distanceMeter.classList.remove("hidden");
            distanceMeter.style.display = "inline-block";

            if (distance === "far") {
                distanceText.textContent = "↓ Move Closer";
                distanceText.className = "text-orange-600 font-medium";
            } else if (distance === "close") {
                distanceText.textContent = "↑ Move Back";
                distanceText.className = "text-orange-600 font-medium";
            } else if (distance === "perfect") {
                distanceText.textContent = "✓ Distance OK";
                distanceText.className = "text-green-600 font-medium";
            }
        }

        // Calculate and show lighting - clean compact panel
        const lighting = analyzeLighting(canvas);
        if (lightingMeter && lightingText && cameraRunning) {
            lightingMeter.classList.remove("hidden");
            lightingMeter.style.display = "inline-block";

            if (lighting === "dark") {
                lightingText.textContent = "🌙 Too Dark";
                lightingText.className = "text-orange-600 font-medium";
            } else if (lighting === "bright") {
                lightingText.textContent = "☀ Too Bright";
                lightingText.className = "text-orange-600 font-medium";
            } else if (lighting === "good") {
                lightingText.textContent = "✓ Lighting OK";
                lightingText.className = "text-green-600 font-medium";
            }
        }

        // Confidence score hidden to reduce clutter

        // Update guidance text - only for critical issues
        if (guidanceText && cameraRunning) {
            let guidance = "";
            // Only show if there's a problem
            if (distance === "far") {
                guidance = "📏 Move Closer";
            } else if (distance === "close") {
                guidance = "⚠️ Move Back";
            } else if (lighting === "dark") {
                guidance = "🌙 Too Dark";
            } else if (lighting === "bright") {
                guidance = "☀️ Too Bright";
            } else if (distance === "perfect" && lighting === "good") {
                guidance = "✨ Verifying...";
            }

            if (guidance) {
                guidanceText.textContent = guidance;
                guidanceText.className = "text-white text-sm font-semibold drop-shadow-lg";
                guidanceText.style.display = "block";
                guidanceText.style.visibility = "visible";
            } else {
                guidanceText.style.display = "none";
            }
        }

    } else {
        // Hide detection UI when no face
        if (distanceMeter) distanceMeter.classList.add("hidden");
        if (lightingMeter) lightingMeter.classList.add("hidden");
        if (guidanceText) {
            guidanceText.textContent = "Position your face in the frame";
            guidanceText.style.display = "block";
            guidanceText.style.visibility = "visible";
        }
    }
}

/* Draw face detection box on kiosk canvas */
function drawKioskFaceBox() {
    const canvas = kioskFaceCanvas;
    const videoEl = video;

    if (!canvas || !videoEl) {
        console.warn('❌ Canvas or video not found');
        return;
    }

    // Match canvas size to video display size
    const rect = videoEl.getBoundingClientRect();
    if (canvas.width !== rect.width || canvas.height !== rect.height) {
        canvas.width = rect.width;
        canvas.height = rect.height;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // ALWAYS DRAW STATIC BOX (guide) while camera is ON
    const boxSize = Math.min(canvas.width, canvas.height) * 0.6;
    const x = (canvas.width - boxSize) / 2;
    const y = (canvas.height - boxSize) / 2;

    // Outer glow stroke
    ctx.save();
    ctx.strokeStyle = "#10b981";
    ctx.lineWidth = 5;
    ctx.shadowColor = "rgba(16,185,129,0.9)";
    ctx.shadowBlur = 14;
    ctx.strokeRect(x, y, boxSize, boxSize);
    ctx.restore();

    // Inner subtle stroke for definition
    ctx.strokeStyle = "rgba(16,185,129,0.25)";
    ctx.lineWidth = 2;
    ctx.strokeRect(x + 3, y + 3, boxSize - 6, boxSize - 6);
}

// =======================
// RECOGNITION LOOP
// =======================
const POLLING_DELAY_MS = 400; // Faster polling for better UX - ~0.4 seconds

async function sendFrame() {
    if (!cameraRunning || sendingFrame || !video.videoWidth) return;
    sendingFrame = true;

    try {
        if (Date.now() < hardCooldownUntil) return;

        // (Intentionally left blank) do not overwrite backend messages here

        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);

        const frame = canvas.toDataURL("image/jpeg", 0.75); // Better quality

        const res = await fetch("/kiosk/recognize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ frame })
        });

        const data = await res.json();
        console.log('🎯 Recognition response:', JSON.stringify(data));
        console.log('🔍 Face detected:', data.face_detected, '| Recognized:', data.recognized, '| Similarity:', data.similarity, '| Status:', data.status);

        if (!data) return;

        // Detect if face is present based on explicit face_detected flag from backend
        const hasFace = Boolean(data.face_detected);
        console.log('📦 Should draw box?', hasFace, '| face_detected=', data.face_detected);

        // Update face detection UI with feedback
        // Delegate draw/clear responsibility solely to updateFaceDetection()
        // Provide a dummy centered box when backend doesn't provide face_box
        updateFaceDetection(
            hasFace,
            data.face_box || { width: 1, height: 1 },
            data.similarity || 0,
            canvas
        );

        // --- UI mapping for liveness WAIT messages ---
        if (data.status === "WAIT") {
            const msg = (data.message || "").toLowerCase();
            setScanScanning();

            if (msg.includes("no face")) {
                setScanIdle();
                setScanMessage("Please face the camera");
                updateFaceDetection(false, null, 0, null);
            } else if (msg.includes("multiple")) {
                setScanIdle();
                setScanMessage("Only one person at a time");
            } else if (msg.includes("analyzing")) {
                setScanMessage("Hold still • Verifying liveness");
            } else if (msg.includes("pass ratio")) {
                const m = msg.match(/pass ratio:\s*([0-9.]+)/i);
                const ratio = m ? parseFloat(m[1]) : 0;
                if (ratio < 0.4) {
                    setScanMessage("Please blink or move slightly");
                } else if (ratio < 0.6) {
                    setScanMessage("Almost there… Keep looking");
                } else {
                    setScanMessage("Verified! Marking attendance…");
                }
            } else {
                setScanMessage("Verifying…");
            }

            return; // stop recognition flow on liveness WAIT
        }

        if (data.status === "unknown") {
            playBeep(600, 200);
            if (canSpeak("unknown")) speak("Face not recognized. Please try again");
            showUnknownCard();
            setScanMessage("Face not recognized. Please try again");
            setScanError();
            hardCooldownUntil = Date.now() + RECOGNITION_COOLDOWN_MS;

            // Clear detection UI (static box remains until camera stop)
            if (distanceMeter) distanceMeter.classList.add("hidden");
            if (lightingMeter) lightingMeter.classList.add("hidden");
            if (guidanceText) guidanceText.style.display = "none";

            return;
        }

        // Success - clear all detection UI (static box remains until camera stop)
        if (distanceMeter) distanceMeter.classList.add("hidden");
        if (lightingMeter) lightingMeter.classList.add("hidden");
        if (guidanceText) guidanceText.style.display = "none";

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

    // Clear all detection UI when stopping
    if (kioskFaceCanvas) {
        const ctx = kioskFaceCanvas.getContext('2d');
        if (ctx) ctx.clearRect(0, 0, kioskFaceCanvas.width, kioskFaceCanvas.height);
    }
    if (distanceMeter) {
        distanceMeter.classList.add("hidden");
        distanceMeter.style.display = "none";
    }
    if (lightingMeter) {
        lightingMeter.classList.add("hidden");
        lightingMeter.style.display = "none";
    }
    if (guidanceText) guidanceText.style.display = "none";
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

        // Smooth modal animation
        const modalContent = document.getElementById("pinModalContent");
        setTimeout(() => {
            if (modalContent) {
                modalContent.style.transform = "scale(1)";
                modalContent.style.opacity = "1";
            }
            pinInput.focus();
        }, 50);
    });
}

// Wire admin exit button inside settings panel
if (exitKioskBtn && pinModal) {
    exitKioskBtn.addEventListener("click", () => {
        console.log('🔴 Exit Kiosk button clicked - showing PIN modal');
        pendingExit = true;
        pinInput.value = "";
        pinModal.classList.remove("hidden");
        pinModal.classList.add("flex");

        // Animate modal
        const modalContent = document.getElementById("pinModalContent");
        if (modalContent) {
            setTimeout(() => {
                modalContent.style.transform = "scale(1)";
                modalContent.style.opacity = "1";
            }, 50);
        }
        setTimeout(() => pinInput.focus(), 100);
    });
}

if (pinCancel && pinModal) {
    pinCancel.addEventListener("click", () => {
        pendingExit = false;
        const modalContent = document.getElementById("pinModalContent");

        // Smooth close animation
        if (modalContent) {
            modalContent.style.transform = "scale(0.95)";
            modalContent.style.opacity = "0";
        }
        setTimeout(() => {
            pinModal.classList.add("hidden");
            pinModal.classList.remove("flex");
        }, 300);
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
            console.log('🔍 Exit Kiosk - Sending PIN to /kiosk/exit');
            pinVerify.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
            pinVerify.disabled = true;

            try {
                const res = await fetch('/kiosk/exit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                    },
                    body: JSON.stringify({ pin })
                });

                console.log('🔍 Exit Response Status:', res.status);
                const data = await res.json().catch(err => {
                    console.error('Failed to parse response:', err);
                    return {};
                });
                console.log('🔍 Exit Response Data:', data);

                try {
                    showCameraInactive();
                } catch (e) { /* ignore */ }

                if (res.ok && data.success) {
                    console.log('✅ Exit successful, redirecting to:', data.redirect);

                    // Professional exit notification
                    const exitMsg = document.createElement('div');
                    exitMsg.className = 'fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] animate-fadeIn';
                    exitMsg.innerHTML = `
                        <div class="bg-white rounded-2xl shadow-2xl p-8 max-w-md text-center transform animate-slideUp">
                            <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-green-400 to-green-600 mb-4 animate-bounce">
                                <i class="fas fa-check text-white text-3xl"></i>
                            </div>
                            <h3 class="text-2xl font-bold text-gray-900 mb-2">Kiosk Mode Exited</h3>
                            <p class="text-gray-600 mb-4">Redirecting to dashboard...</p>
                            <div class="flex items-center justify-center gap-2">
                                <div class="w-2 h-2 bg-indigo-600 rounded-full animate-pulse"></div>
                                <div class="w-2 h-2 bg-indigo-600 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
                                <div class="w-2 h-2 bg-indigo-600 rounded-full animate-pulse" style="animation-delay: 0.4s"></div>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(exitMsg);

                    setTimeout(() => {
                        window.location.href = data.redirect || '/dashboard';
                    }, 1500);

                } else {
                    console.error('❌ Exit failed:', data.message);

                    // Professional error notification
                    const errorMsg = document.createElement('div');
                    errorMsg.className = 'fixed top-4 right-4 bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-4 rounded-xl shadow-2xl z-[100] animate-slideInRight';
                    errorMsg.innerHTML = `
                        <div class="flex items-center gap-3">
                            <i class="fas fa-exclamation-circle text-2xl"></i>
                            <div>
                                <p class="font-bold text-sm">Exit Failed</p>
                                <p class="text-xs opacity-90">${data.message || 'Invalid PIN. Please try again.'}</p>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(errorMsg);
                    setTimeout(() => errorMsg.remove(), 4000);

                    pinInput.value = '';
                    pinInput.focus();
                }

            } catch (err) {
                console.error('❌ Network error during exit:', err);
                alert('Network error. Please check your connection and try again.');
            } finally {
                pinVerify.innerHTML = '<i class="fas fa-check-circle mr-2"></i>Verify';
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
                const modalContent = document.getElementById("pinModalContent");
                if (modalContent) {
                    modalContent.style.transform = "scale(0.95)";
                    modalContent.style.opacity = "0";
                }

                setTimeout(() => {
                    pinModal.classList.add("hidden");
                    pinModal.classList.remove("flex");
                    settingsPanel.style.transform = 'translateX(0)';

                    // Enable all controls
                    const adminControls = settingsPanel.querySelectorAll('select, button');
                    adminControls.forEach(ctrl => {
                        ctrl.disabled = false;
                        ctrl.style.opacity = '1';
                        ctrl.style.cursor = 'pointer';
                    });
                }, 300);

                console.log('✅ Admin access granted');

                // Populate admin camera list before showing settings
                try {
                    await loadAdminCameras();
                } catch (e) {
                    console.error(e);
                }

            } else {
                alert(data.message || "Invalid PIN");
                pinInput.value = "";
                pinInput.focus();
            }
        } catch (err) {
            console.error(err);
            alert("Network error. Try again.");
        } finally {
            pinVerify.innerHTML = '<i class="fas fa-check-circle mr-2"></i>Verify';
            pinVerify.disabled = false;
        }
    });
}

// Skip PIN button - view-only mode
const skipPinBtn = document.getElementById("skipPin");
if (skipPinBtn && pinModal && settingsPanel) {
    skipPinBtn.addEventListener("click", () => {
        console.log('👁️ Settings opened in view-only mode');

        const modalContent = document.getElementById("pinModalContent");
        if (modalContent) {
            modalContent.style.transform = "scale(0.95)";
            modalContent.style.opacity = "0";
        }

        setTimeout(() => {
            pinModal.classList.add("hidden");
            pinModal.classList.remove("flex");
            settingsPanel.style.transform = 'translateX(0)';

            // Disable controls in view mode
            const adminControls = settingsPanel.querySelectorAll('select, button');
            adminControls.forEach(ctrl => {
                if (ctrl.id !== 'closeSettingsBtn') {
                    ctrl.disabled = true;
                    ctrl.style.opacity = '0.6';
                    ctrl.style.cursor = 'not-allowed';
                }
            });
        }, 300);
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
        // Smooth slide out animation
        settingsPanel.style.transform = 'translateX(100%)';
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

        // Request permission first for device labels
        try {
            const testStream = await navigator.mediaDevices.getUserMedia({ video: true });
            testStream.getTracks().forEach(track => track.stop());
        } catch (e) {
            console.warn('Admin camera permission needed');
        }

        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === 'videoinput');

        adminCameraSelect.innerHTML = '';
        videoDevices.forEach((d, idx) => {
            const o = document.createElement('option');
            o.value = d.deviceId;
            o.textContent = d.label || `Camera ${idx + 1} (${d.deviceId.substring(0, 8)}...)`;
            adminCameraSelect.appendChild(o);
        });

        // Add change event listener to restart camera with new device
        adminCameraSelect.addEventListener('change', async () => {
            console.log('📹 Camera changed, restarting with:', adminCameraSelect.value);
            if (cameraRunning) {
                // Stop current camera
                if (stream) {
                    stream.getTracks().forEach(t => t.stop());
                    video.srcObject = null;
                    stream = null;
                }
                cameraRunning = false;
                
                // Restart with new camera
                if (startBtn) {
                    startBtn.click();
                }
            }
        });

        console.log(`📹 Admin: Loaded ${videoDevices.length} camera(s)`);
    } catch (err) {
        console.error('❌ Error loading admin cameras:', err);
    }
}
