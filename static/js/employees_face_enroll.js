// =====================
// DOM REFERENCES
// =====================
console.log("employees_face_enroll.js loaded");
const video = document.getElementById("camera");
const faceCanvas = document.getElementById("faceCanvas");
const capturedImg = document.getElementById("capturedImg");
const captureBtn = document.getElementById("captureBtn");
const startCameraBtn = document.getElementById("startCameraBtn");
const stopCameraBtn = document.getElementById("stopCameraBtn");
const previewBox = document.getElementById("previewBox");
const loadingBox = document.getElementById("loadingBox");
const guidanceText = document.getElementById("guidanceText");
const actionBtns = document.getElementById("actionBtns");
const retakeBtn = document.getElementById("retakeBtn");
const saveBtn = document.getElementById("saveBtn");
const cameraInactiveBox = document.getElementById("cameraInactiveBox");
const cameraControls = document.getElementById("cameraControls");

// =====================
// GLOBAL STATE (ONLY ONCE)
// =====================
let currentStream = null;
let lastCapturedImage = null;
let faceDetected = false;
let detectInterval = null;
let lastDetectState = null;
let detectSessionId = 0; // 🔒 SESSION GUARD
let isProcessing = false; // 🚨 COOLDOWN FLAG

// 🎯 FACE STABILITY & QUALITY GATES
let stabilityStartTime = null;
const STABILITY_THRESHOLD_MS = 800; // 800ms stability required
let lastFaceCount = 0;
let stabilityResetTimeout = null;

// 🎯 REQUEST MANAGEMENT - Prevent concurrent requests
let currentDetectionRequest = null;
let isDetectionInProgress = false;

// 🎯 STABILITY TIMER FUNCTIONS
function resetStabilityTimer() {
    stabilityStartTime = null;
    if (stabilityResetTimeout) {
        clearTimeout(stabilityResetTimeout);
        stabilityResetTimeout = null;
    }
}

function startStabilityTimer() {
    if (!stabilityStartTime) {
        stabilityStartTime = Date.now();
    }
}

// Check if elements exist
console.log("captureBtn element:", captureBtn);
console.log("captureBtn initial classList:", captureBtn ? captureBtn.classList : "NOT FOUND");

// Disable Capture button by default (extra hardening)
if (captureBtn) {
    captureBtn.classList.add("hidden");
    console.log("captureBtn hidden initially");
} else {
    console.error("captureBtn not found!");
}

// CSRF helper for AJAX (TOP LEVEL)
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content;
}

function showGuidance(message) {
    if (guidanceText) {
        guidanceText.textContent = message;
        guidanceText.classList.remove("hidden");
    }
}

// PURE UI FUNCTION - DISABLED for clean UX (no face boxes)
/*
function drawDetectionBox(color = "#ef4444") {
    if (!video || !faceCanvas) return;

    const rect = video.getBoundingClientRect();
    faceCanvas.width = rect.width;
    faceCanvas.height = rect.height;

    const ctx = faceCanvas.getContext("2d");
    ctx.clearRect(0, 0, faceCanvas.width, faceCanvas.height);

    const size = Math.min(rect.width, rect.height) * 0.55;
    const x = (rect.width - size) / 2;
    const y = (rect.height - size) / 2;

    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.shadowColor = color;
    ctx.shadowBlur = 8;

    ctx.strokeRect(x, y, size, size);
}
*/
function drawDetectionBox(color = "#ef4444") {
    // Disabled for clean UX - no face detection boxes
    if (!video || !faceCanvas) return;

    const rect = video.getBoundingClientRect();
    faceCanvas.width = rect.width;
    faceCanvas.height = rect.height;

    const ctx = faceCanvas.getContext("2d");
    ctx.clearRect(0, 0, faceCanvas.width, faceCanvas.height);

    // No box drawing - clean interface
}

// Face Detection with Stability & Quality Gates
async function detectFaceOnce() {
    const sessionAtStart = detectSessionId;
    
    // 🚨 Prevent concurrent requests
    if (isDetectionInProgress) {
        console.log("Detection already in progress - skipping");
        return;
    }
    
    if (!currentStream || !video.videoWidth) {
        guidanceText.classList.add("hidden");
        captureBtn.classList.add("hidden");
        console.log("No stream or video not ready - hiding button");
        return;
    }

    // 🚨 Mark request as in progress
    isDetectionInProgress = true;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    try {
        console.log("Sending face detection request...");
        
        // 🚨 Store current request for potential cancellation
        currentDetectionRequest = fetch("/auth/detect_face", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({ image: canvas.toDataURL("image/jpeg") })
        });
        
        const res = await currentDetectionRequest;

        // 🔒 OLD RESPONSE → IGNORE
        if (sessionAtStart !== detectSessionId) {
            console.log("Old session - ignoring response");
            return;
        }

        const { face_count, distance, lighting } = await res.json();
        console.log(`Face detection response: face_count=${face_count}, distance=${distance}, lighting=${lighting}`);

        // 🔒 OLD RESPONSE → IGNORE
        if (sessionAtStart !== detectSessionId) {
            console.log("Old session after JSON parse - ignoring response");
            return;
        }

        let borderColor = "#ef4444"; // Default: red
        let message = "";
        let allowCapture = false;

        // 🎯 STEP 1: Basic Face Detection
        if (face_count === 0) {
            // 🔴 STATE-1: No Face
            borderColor = "#ef4444"; // Red
            message = "No face detected";
            allowCapture = false;
            resetStabilityTimer(); // Reset stability on no face
        } else if (face_count > 1) {
            // 🟠 STATE-2: Multiple Faces
            borderColor = "#f97316"; // Orange
            message = "Multiple faces detected. Only one person allowed";
            allowCapture = false;
            resetStabilityTimer(); // Reset stability on multiple faces
        } else if (face_count === 1) {
            // 🎯 STEP 2: Single Face Detected - Now Check Quality Gates

            // Distance Check
            if (distance === "far") {
                borderColor = "#f59e0b"; // Yellow
                message = "Move closer to camera";
                allowCapture = false;
                resetStabilityTimer();
            } else if (distance === "close") {
                borderColor = "#f59e0b"; // Yellow
                message = "Move back from camera";
                allowCapture = false;
                resetStabilityTimer();
            }
            // Lighting Check
            else if (lighting === "dark") {
                borderColor = "#f59e0b"; // Yellow
                message = "Lighting too dark - find better light";
                allowCapture = false;
                resetStabilityTimer();
            } else if (lighting === "bright") {
                borderColor = "#f59e0b"; // Yellow
                message = "Lighting too bright - reduce glare";
                allowCapture = false;
                resetStabilityTimer();
            }
            // 🎯 STEP 3: All Quality Gates Passed - Check Stability
            else {
                // Start/Continue stability timer
                if (!stabilityStartTime) {
                    stabilityStartTime = Date.now();
                    message = "Face detected - hold still...";
                    borderColor = "#3b82f6"; // Blue - stabilizing
                    allowCapture = false;
                } else {
                    const stableDuration = Date.now() - stabilityStartTime;

                    if (stableDuration < STABILITY_THRESHOLD_MS) {
                        // Still stabilizing
                        const progress = Math.round((stableDuration / STABILITY_THRESHOLD_MS) * 100);
                        message = `Hold still... ${progress}%`;
                        borderColor = "#3b82f6"; // Blue - stabilizing
                        allowCapture = false;
                    } else {
                        // 🎯 STEP 4: Fully Stable - Ready for Capture
                        message = "Perfect! Click capture";
                        borderColor = "#10b981"; // Green - ready
                        allowCapture = true;
                    }
                }
            }
        }

        faceDetected = allowCapture;
        drawDetectionBox(borderColor);

        // Update UI based on detection state
        guidanceText.textContent = message;
        guidanceText.classList.remove("hidden");

        // Always hide button first, then show only if capture is allowed
        console.log(`Face detection: count=${face_count}, distance=${distance}, lighting=${lighting}, allowCapture=${allowCapture}, message="${message}"`);
        captureBtn.classList.add("hidden");
        if (allowCapture) {
            captureBtn.classList.remove("hidden");
            console.log("Capture button shown");
        } else {
            console.log("Capture button hidden");
        }

    } catch (err) {
        if (sessionAtStart !== detectSessionId) return;
        captureBtn.classList.add("hidden");
        guidanceText.classList.add("hidden");
        console.error("Face detection error:", err);
    } finally {
        // 🚨 Always reset detection flag
        isDetectionInProgress = false;
        currentDetectionRequest = null;
    }
}

// Start Camera
function startCamera() {
    detectSessionId++; // 🔥 new session
    lastDetectState = null;
    
    // 🚨 Reset detection flags
    isDetectionInProgress = false;
    currentDetectionRequest = null;
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            currentStream = stream;
            video.srcObject = stream;
            cameraInactiveBox.classList.add("hidden");
            video.classList.remove("hidden");
            faceCanvas.classList.remove("hidden");
            guidanceText.classList.remove("hidden");
            cameraControls.classList.remove("hidden");
            startCameraBtn.classList.add("hidden");
            stopCameraBtn.classList.remove("hidden");
            captureBtn.classList.add("hidden");
            previewBox.classList.add("hidden");
            actionBtns.classList.add("hidden");
            saveBtn.classList.add("hidden");
            retakeBtn.classList.add("hidden");
            video.onloadeddata = () => drawDetectionBox("#ef4444");
            if (detectInterval) clearInterval(detectInterval);
            detectInterval = setInterval(detectFaceOnce, 600);
        })
        .catch(err => {
            cameraInactiveBox.classList.remove("hidden");
            video.classList.add("hidden");
            guidanceText.classList.add("hidden");
            cameraControls.classList.remove("hidden");
            startCameraBtn.classList.remove("hidden");
            stopCameraBtn.classList.add("hidden");
            captureBtn.classList.add("hidden");
            showStatusModal("error", "Camera not accessible! Please check permissions.");
            console.error(err);
        });
}

// Stop Camera
function stopCamera() {
    detectSessionId++; // 🔥 invalidate old async calls
    isProcessing = false; // 🚨 RESET COOLDOWN
    resetStabilityTimer(); // 🎯 RESET STABILITY TIMER
    if (detectInterval) {
        clearInterval(detectInterval);
        detectInterval = null;
    }
    lastDetectState = null;
    faceDetected = false;
    if (!currentStream) {
        cameraInactiveBox.classList.remove("hidden");
        video.classList.add("hidden");
        faceCanvas.classList.add("hidden");
        guidanceText.classList.add("hidden");
        cameraControls.classList.remove("hidden");
        startCameraBtn.classList.remove("hidden");
        stopCameraBtn.classList.add("hidden");
        captureBtn.classList.add("hidden");
        return;
    }
    currentStream.getTracks().forEach(track => track.stop());
    currentStream = null;
    video.srcObject = null;
    cameraInactiveBox.classList.remove("hidden");
    video.classList.add("hidden");
    faceCanvas.classList.add("hidden");
    guidanceText.classList.add("hidden");
    cameraControls.classList.remove("hidden");
    startCameraBtn.classList.remove("hidden");
    stopCameraBtn.classList.add("hidden");
    captureBtn.classList.add("hidden");
}

// Initial state
cameraControls.classList.remove("hidden");
startCameraBtn.classList.remove("hidden");
stopCameraBtn.classList.add("hidden");
captureBtn.classList.add("hidden");
previewBox.classList.add("hidden");
actionBtns.classList.add("hidden");
saveBtn.classList.add("hidden");
retakeBtn.classList.add("hidden");
if (cameraInactiveBox) {
    cameraInactiveBox.classList.remove("hidden");
}

// Button events
startCameraBtn.addEventListener("click", startCamera);
stopCameraBtn.addEventListener("click", stopCamera);

captureBtn.onclick = () => {
    if (!currentStream || !faceDetected || isProcessing) return;

    // 🎯 STEP 1: Lock UI and show "Hold still" message
    isProcessing = true; // 🚨 COOLDOWN FLAG
    detectSessionId++; // 🔥 invalidate detect calls
    captureBtn.disabled = true;
    captureBtn.textContent = "Hold still...";
    captureBtn.classList.add("opacity-75", "cursor-not-allowed");

    showGuidance("Capturing... Hold still!");

    // 🎯 STEP 2: Wait 300ms for autofocus/settling
    setTimeout(() => {
        if (!currentStream) return; // Safety check

        // 🎯 STEP 3: Stop detection and prepare capture
        if (detectInterval) {
            clearInterval(detectInterval);
            detectInterval = null;
        }

        faceDetected = false;

        // 🎯 STEP 4: Create capture canvas (use video dimensions for quality)
        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);
        lastCapturedImage = canvas.toDataURL("image/jpeg", 0.95); // High quality

        // ===== HARD UI RESET =====
        startCameraBtn.classList.add("hidden");
        stopCameraBtn.classList.add("hidden");
        captureBtn.classList.add("hidden");
        guidanceText.classList.add("hidden");
        cameraInactiveBox.classList.add("hidden");

        video.classList.add("hidden");
        faceCanvas.classList.add("hidden");

        // Stop camera stream
        if (currentStream) {
            currentStream.getTracks().forEach(t => t.stop());
            currentStream = null;
            video.srcObject = null;
        }

        // ===== SHOW PREVIEW MODE =====
        capturedImg.src = lastCapturedImage;
        previewBox.classList.remove("hidden");
        actionBtns.classList.remove("hidden");

        // 🎯 STEP 5: Reset stability for next capture
        resetStabilityTimer();

        console.log("✅ Face captured successfully with stability gates");

        // ⭐ VERY IMPORTANT - ALLOW SAVE PHASE
        isProcessing = false;

        // Show buttons after settling delay
        retakeBtn.classList.remove("hidden");
        saveBtn.classList.remove("hidden");
        cameraControls.classList.add("hidden");

    }, 300); // 300ms delay for settling
};

retakeBtn.onclick = () => {
    // ⭐ SAFETY RESET
    isProcessing = false;
    
    // 🔄 Reset capture button state
    captureBtn.textContent = "Capture Photo";
    captureBtn.classList.remove("opacity-75", "cursor-not-allowed");
    captureBtn.disabled = false;
    
    lastCapturedImage = null;
    previewBox.classList.add("hidden");
    actionBtns.classList.add("hidden");
    saveBtn.classList.add("hidden");
    retakeBtn.classList.add("hidden");
    // Do NOT show captureBtn directly; startCamera will handle it
    startCamera(); // camera start hoga → capture auto show
};

saveBtn.onclick = async () => {
    if (!lastCapturedImage || isProcessing) return;

    // 🚨 IMMEDIATE COOLDOWN
    isProcessing = true;
    saveBtn.disabled = true;
    const originalText = saveBtn.textContent;
    saveBtn.textContent = "Processing...";

    if (loadingBox) loadingBox.classList.remove("hidden");

    let employeeId = window.EMPLOYEE_ID;
    const csrfToken = getCSRFToken();

    // Use correct API based on mode
    let apiUrl = "/enroll/capture";
    if (window.ENROLL_MODE === "update") {
        apiUrl = "/enroll/update_capture";
    }

    try {
        let res = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                employee_id: employeeId,
                image: lastCapturedImage
            })
        });
        let data = await res.json();

        if (loadingBox) loadingBox.classList.add("hidden");

        if (data.status === "success") {
            showStatusModal("success", data.message || "Face enrolled successfully!");
            // 🚨 SUCCESS: LOCK UI PERMANENTLY
            setTimeout(() => {
                closeStatusModal();
                window.location.href = "/enroll";
            }, 2000);
        } else if (data.status === "quality_failed") {
            showStatusModal("warning", data.feedback || "Face quality issues detected");
            // 🚨 RE-ENABLE ON QUALITY FAIL
            isProcessing = false;
            saveBtn.disabled = false;
            saveBtn.textContent = originalText;
        } else if (data.status === "no_face") {
            showStatusModal("error", "No face detected");
            // 🚨 RE-ENABLE ON NO FACE
            isProcessing = false;
            saveBtn.disabled = false;
            saveBtn.textContent = originalText;
        } else if (data.status === "duplicate") {
            // Duplicate face detected across employees
            showStatusModal("warning", data.message || "Duplicate face detected");
            isProcessing = false;
            saveBtn.disabled = false;
            saveBtn.textContent = originalText;
        } else {
            // Covers "error" and any other cases
            showStatusModal("error", data.message || "Enrollment failed");
            // 🚨 RE-ENABLE ON ERROR
            isProcessing = false;
            saveBtn.disabled = false;
            saveBtn.textContent = originalText;
        }
    } catch (error) {
        console.error("Enrollment error:", error);
        showStatusModal("error", "Network error occurred");
        // 🚨 RE-ENABLE ON ERROR
        isProcessing = false;
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
        if (loadingBox) loadingBox.classList.add("hidden");
    }

    // Stop any ongoing detection
    if (detectInterval) {
        clearInterval(detectInterval);
        detectInterval = null;
    }
    // Stop camera and reset to initial state
    stopCamera();
    // After save, reset buttons to initial state (already done by stopCamera, but ensure)
    startCameraBtn.classList.remove("hidden");
    stopCameraBtn.classList.add("hidden");
    captureBtn.classList.add("hidden");
    previewBox.classList.add("hidden");
    actionBtns.classList.add("hidden");
    saveBtn.classList.add("hidden");
    retakeBtn.classList.add("hidden");
};
