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

// PURE UI FUNCTION
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

// Face Detection (ALONE, NOT NESTED)
async function detectFaceOnce() {
    const sessionAtStart = detectSessionId;
    if (!currentStream || !video.videoWidth) {
        guidanceText.classList.add("hidden");
        captureBtn.classList.add("hidden"); // Ensure button is hidden when no stream
        console.log("No stream or video not ready - hiding button");
        return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    try {
        console.log("Sending face detection request...");
        const res = await fetch("/enroll/detect_face", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({ image: canvas.toDataURL("image/jpeg") })
        });

        // 🔒 OLD RESPONSE → IGNORE
        if (sessionAtStart !== detectSessionId) {
            console.log("Old session - ignoring response");
            return;
        }

        const { face_detected, face_count } = await res.json();
        console.log(`Face detection response: face_detected=${face_detected}, face_count=${face_count}`);
        
        // 🔒 OLD RESPONSE → IGNORE
        if (sessionAtStart !== detectSessionId) {
            console.log("Old session after JSON parse - ignoring response");
            return;
        }

        let borderColor = "#ef4444"; // Default: red
        let message = "";
        let allowCapture = false;

        if (face_count === 0) {
            // 🔴 STATE-1: No Face
            borderColor = "#ef4444"; // Red
            message = "No face detected";
            allowCapture = false;
        } else if (face_count > 1) {
            // 🟠 STATE-2: Multiple Faces
            borderColor = "#f97316"; // Orange
            message = "Multiple faces detected. Only one person allowed";
            allowCapture = false;
        } else if (face_count === 1) {
            // 🟢 STATE-3: Exactly One Face
            borderColor = "#10b981"; // Green
            message = "Face detected – hold still & capture";
            allowCapture = true;
        }

        faceDetected = allowCapture;
        drawDetectionBox(borderColor);

        // Update UI based on detection state
        guidanceText.textContent = message;
        guidanceText.classList.remove("hidden");
        
        // Always hide button first, then show only if capture is allowed
        console.log(`Face detection: count=${face_count}, allowCapture=${allowCapture}, message="${message}"`);
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
    }
}

// Start Camera
function startCamera() {
    detectSessionId++; // 🔥 new session
    lastDetectState = null;
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
    detectSessionId++; // 🔥 invalidate detect calls
    if (!currentStream || !faceDetected) return;

    // Stop detection
    if (detectInterval) {
        clearInterval(detectInterval);
        detectInterval = null;
    }

    faceDetected = false;

    // Capture frame
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    lastCapturedImage = canvas.toDataURL("image/jpeg");

    // ===== HARD UI RESET (THIS WAS MISSING) =====
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
    retakeBtn.classList.remove("hidden");
    saveBtn.classList.remove("hidden");
    cameraControls.classList.add("hidden");
};

retakeBtn.onclick = () => {
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

    let employeeId = window.location.pathname.split("/").pop();
    const csrfToken = getCSRFToken();

    try {
        let res = await fetch("/enroll/capture", {
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
