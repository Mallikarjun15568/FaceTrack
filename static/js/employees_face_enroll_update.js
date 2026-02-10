// =====================
// DOM REFERENCES
// =====================
const video = document.getElementById("camera");
const faceCanvas = document.getElementById("faceCanvas");
const previewImg = document.getElementById("previewImg");
const captureBtn = document.getElementById("captureBtn");
const startCameraBtn = document.getElementById("startCameraBtn");
const stopCameraBtn = document.getElementById("stopCameraBtn");
const saveBtn = document.getElementById("saveBtn");
const guidanceText = document.getElementById("guidanceText");
const retakeBtn = document.getElementById("retakeBtn");
const cameraInactiveBox = document.getElementById("cameraInactiveBox");

// ===== INITIAL UI STATE =====
cameraInactiveBox.classList.remove("hidden");
video.classList.add("hidden");
faceCanvas.classList.add("hidden");
guidanceText.classList.add("hidden");
captureBtn.classList.add("hidden");

// =====================
// GLOBAL STATE
// =====================
let currentStream = null;
let lastImage = null;
let detectInterval = null;
let lastDetectState = null;
let faceDetected = false;
let isCaptured = false; // 🔒 GLOBAL STATE for capture lock
let detectSessionId = 0; // 🔒 SESSION GUARD
let isProcessing = false; // 🚨 COOLDOWN FLAG
let isRetaking = false; // 🎯 RETAKE FLAG

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

// CSRF helper for AJAX
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content;
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

// Scroll to camera function
function scrollToCamera() {
    const camBox = document.querySelector(".relative.w-full.h-96");
    if (!camBox) return;

    // wait until camera/video is visible
    const video = document.getElementById("camera");
    if (!video || video.classList.contains("hidden")) {
        requestAnimationFrame(scrollToCamera);
        return;
    }

    const headerOffset = 90; // fixed header height
    const elementPosition = camBox.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

    window.scrollTo({
        top: offsetPosition,
        behavior: "smooth"
    });
}

// Start Camera
function startCamera() {
    detectSessionId++;   // 🔥 NEW SESSION
    isCaptured = false; // 🔓 unlock UI
    faceDetected = false;
    lastDetectState = null;
    
    // 🚨 Reset detection flags
    isDetectionInProgress = false;
    currentDetectionRequest = null;
    
    captureBtn.style.display = "none"; // reset state on camera start
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            currentStream = stream;
            video.srcObject = stream;
            cameraInactiveBox.classList.add("hidden");
            cameraInactiveBox.style.display = "none";
            video.classList.remove("hidden");
            video.style.display = "block";
            faceCanvas.classList.remove("hidden");
            guidanceText.classList.remove("hidden");
            startCameraBtn.classList.add("hidden");
            startCameraBtn.style.display = "none";
            
            // Show camera controls
            const cameraControls = document.getElementById("cameraControls");
            if (cameraControls) {
                cameraControls.style.display = "flex";
            }
            stopCameraBtn.style.display = "flex";
            
            previewImg.classList.add("hidden");
            previewImg.style.display = "none";
            actionBtns.style.display = "none";
            saveBtn.style.display = "none";
            retakeBtn.style.display = "none";
            video.onloadeddata = () => {
                setTimeout(() => drawDetectionBox("#ef4444"), 100);
            };
            if (detectInterval) {
                clearInterval(detectInterval);
            }
            detectInterval = setInterval(detectFaceOnce, 600);

            // ⭐ YAHI PE SCROLL KARNA HAI
            requestAnimationFrame(scrollToCamera);
        })
        .catch(err => {
            cameraInactiveBox.classList.remove("hidden");
            cameraInactiveBox.style.display = "flex";
            video.classList.add("hidden");
            video.style.display = "none";
            faceCanvas.classList.add("hidden");
            guidanceText.classList.add("hidden");
            showStatusModal("error", "Camera not accessible! Please check permissions.");
            console.error(err);
        });
}

// Stop Camera
function stopCamera() {
    detectSessionId++;   // 🔥 INVALIDATE OLD REQUESTS
    isCaptured = false; // Camera stopped, not photo captured
    faceDetected = false;
    isProcessing = false; // 🚨 RESET COOLDOWN
    resetStabilityTimer(); // 🎯 RESET STABILITY TIMER
    if (detectInterval) {
        clearInterval(detectInterval);
        detectInterval = null;
    }
    lastDetectState = null;
    
    // Hide camera controls
    const cameraControls = document.getElementById("cameraControls");
    if (cameraControls) {
        cameraControls.style.display = "none";
    }
    
    if (!currentStream) {
        cameraInactiveBox.classList.remove("hidden");
        cameraInactiveBox.style.display = "flex";
        video.classList.add("hidden");
        video.style.display = "none";
        faceCanvas.classList.add("hidden");
        guidanceText.classList.add("hidden");
        startCameraBtn.classList.remove("hidden");
        startCameraBtn.style.display = "inline-flex";
        stopCameraBtn.style.display = "none";
        captureBtn.style.display = "none";
        return;
    }
    currentStream.getTracks().forEach(track => track.stop());
    currentStream = null;
    video.srcObject = null;
    cameraInactiveBox.classList.remove("hidden");
    cameraInactiveBox.style.display = "flex";
    video.classList.add("hidden");
    video.style.display = "none";
    faceCanvas.classList.add("hidden");
    guidanceText.classList.add("hidden");
    startCameraBtn.classList.remove("hidden");
    startCameraBtn.style.display = "inline-flex";
    stopCameraBtn.style.display = "none";
    captureBtn.style.display = "none";
    actionBtns.style.display = "none";
    guidanceText.classList.add("hidden");
}

// Show Guidance Text
function showGuidance(message) {
    if (isCaptured) return;   // 🔒 DO NOT SHOW AFTER CAPTURE
    guidanceText.textContent = message;

    // FORCE correct placement inside camera
    guidanceText.style.position = "absolute";
    guidanceText.style.bottom = "1.5rem";   // buttons se upar
    guidanceText.style.left = "50%";
    guidanceText.style.transform = "translateX(-50%)";
    guidanceText.style.zIndex = "20";
    guidanceText.style.pointerEvents = "none";

    guidanceText.classList.remove("hidden");
}

// Initial state (on page load)
cameraInactiveBox.classList.remove("hidden");
cameraInactiveBox.style.display = "flex";
video.classList.add("hidden");
video.style.display = "none";
faceCanvas.classList.add("hidden");
guidanceText.classList.add("hidden");
captureBtn.style.display = "none";

// Button events
startCameraBtn.addEventListener("click", startCamera);
stopCameraBtn.addEventListener("click", stopCamera);

captureBtn.onclick = () => {
    if (!currentStream || !faceDetected || isProcessing) return;

    // 🎯 STEP 1: Lock UI and show "Hold still" message
    isProcessing = true; // 🚨 COOLDOWN FLAG
    captureBtn.disabled = true;
    captureBtn.textContent = "Hold still...";
    captureBtn.classList.add("opacity-75", "cursor-not-allowed");

    showGuidance("Capturing... Hold still!");

    // 🎯 STEP 2: Wait 300ms for autofocus/settling
    setTimeout(() => {
        if (!currentStream) return; // Safety check

        // 🎯 STEP 3: Stop detection and capture
        if (detectInterval) {
            clearInterval(detectInterval);
            detectInterval = null;
        }

        faceDetected = false;
        isCaptured = true; // 🔒 LOCK UI STATE

        // 🎯 STEP 4: Create capture canvas (use video dimensions for quality)
        let canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);
        lastImage = canvas.toDataURL("image/jpeg", 0.95); // High quality

        // 🎯 STEP 5: Show preview and hide camera
        previewImg.src = lastImage;
        previewImg.classList.remove("hidden");
        previewImg.style.display = "block";
        actionBtns.style.display = "flex";
        saveBtn.style.display = "inline-flex";
        retakeBtn.style.display = "inline-flex";
        captureBtn.style.display = "none";
        guidanceText.classList.add("hidden");
        
        // Hide camera controls
        const cameraControls = document.getElementById("cameraControls");
        if (cameraControls) {
            cameraControls.style.display = "none";
        }
        stopCameraBtn.style.display = "none";
        startCameraBtn.style.display = "none";

        // Stop camera stream
        if (currentStream) {
            currentStream.getTracks().forEach(t => t.stop());
            video.srcObject = null;
            currentStream = null;
        }
        video.classList.add("hidden");

        // 🎯 STEP 6: Reset stability for next capture
        resetStabilityTimer();

        console.log("✅ Face captured successfully with stability gates");

        // 🔓 ALLOW SAVE PHASE
        isProcessing = false;

        // Show buttons after settling delay
        faceCanvas.classList.add("hidden");
        cameraInactiveBox.classList.add("hidden");

    }, 300); // 300ms delay for settling
};

retakeBtn.onclick = () => {
    isCaptured = false;   // 🔓 UNLOCK
    isProcessing = false; // 🔓 RESET PROCESSING STATE
    
    // 🔄 Reset capture button state
    captureBtn.textContent = "Capture Photo";
    captureBtn.classList.remove("opacity-75", "cursor-not-allowed");
    captureBtn.disabled = false;
    
    lastImage = null;
    resetStabilityTimer(); // 🎯 RESET STABILITY TIMER
    guidanceText.classList.add("hidden"); // 🎯 RESET GUIDANCE
    guidanceText.textContent = ""; // 🎯 CLEAR TEXT
    isRetaking = true; // 🎯 SKIP NEXT DETECT
    previewImg.classList.add("hidden");
    previewImg.style.display = "none";
    actionBtns.style.display = "none";
    saveBtn.style.display = "none";
    retakeBtn.style.display = "none";
    startCamera();
};

saveBtn.onclick = async () => {
    if (!lastImage) {
        alert("No image captured");
        return;
    }
    if (isProcessing) {
        console.warn("Save blocked: already processing");
        return;
    }

    // 🚨 IMMEDIATE COOLDOWN
    isProcessing = true;
    saveBtn.disabled = true;
    const originalText = saveBtn.textContent;
    saveBtn.textContent = "Processing...";

    const employeeId = window.EMPLOYEE_ID;
    const csrfToken = getCSRFToken();

    // Hard-coded for update page
    const apiUrl = "/enroll/update_capture";

    try {
        let res = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },
            body: JSON.stringify({
                employee_id: employeeId,
                image: lastImage
            })
        });
        let data = await res.json();

        if (data.status === "success") {
            showStatusModal("success", data.message || "Face updated successfully!");
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
            showStatusModal("warning", data.message || "Duplicate face detected");
            // 🚨 RE-ENABLE ON DUPLICATE
            isProcessing = false;
            saveBtn.disabled = false;
            saveBtn.textContent = originalText;
        } else {
            // Covers "error" and any other cases
            showStatusModal("error", data.message || "Update failed");
            // 🚨 RE-ENABLE ON ERROR
            isProcessing = false;
            saveBtn.disabled = false;
            saveBtn.textContent = originalText;
        }
    } catch (error) {
        console.error("Update error:", error);
        showStatusModal("error", "Network error occurred");
        // 🚨 RE-ENABLE ON ERROR
        isProcessing = false;
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
    }

    // Stop any ongoing detection
    if (detectInterval) {
        clearInterval(detectInterval);
        detectInterval = null;
    }
    // Stop camera and reset to initial state
    stopCamera();
    startCameraBtn.style.display = "inline-flex";
    stopCameraBtn.style.display = "none";
    captureBtn.style.display = "none";
    previewImg.style.display = "none";
    saveBtn.style.display = "none";
    retakeBtn.style.display = "none";
};

// Face Detection with Stability & Quality Gates
async function detectFaceOnce() {
    const sessionAtStart = detectSessionId;
    
    // 🚨 Prevent concurrent requests
    if (isDetectionInProgress) {
        console.log("Detection already in progress - skipping");
        return;
    }
    
    if (isRetaking) { isRetaking = false; return; } // 🎯 SKIP AFTER RETAKE
    if (isCaptured || !currentStream) return;
    if (!currentStream || !video.videoWidth) {
        guidanceText.classList.add("hidden");
        captureBtn.style.display = "none";
        return;
    }

    // 🚨 Mark request as in progress
    isDetectionInProgress = true;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    try {
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
        const { face_count, distance, lighting } = await res.json();

        // 🔒 HARD GUARD — OLD RESPONSE
        if (sessionAtStart !== detectSessionId) return;

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
        captureBtn.style.display = "none";
        if (!isCaptured && allowCapture) {
            captureBtn.style.display = "inline-flex";
        }

        showGuidance(message);
        lastDetectState = face_count;
    } catch (err) {
        if (sessionAtStart !== detectSessionId) return;
        captureBtn.style.display = "none";
        guidanceText.textContent = "Detection error";
        resetStabilityTimer();
    } finally {
        // 🚨 Always reset detection flag
        isDetectionInProgress = false;
        currentDetectionRequest = null;
    }
}
