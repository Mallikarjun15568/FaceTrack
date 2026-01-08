// =====================
// DOM REFERENCES
// =====================
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

// Disable Capture button by default (extra hardening)
captureBtn.classList.add("hidden");

// CSRF helper for AJAX (TOP LEVEL)
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content;
}

// PURE UI FUNCTION
function drawGreenBox(isFaceDetected = false) {
    if (!video || !faceCanvas) return;

    const rect = video.getBoundingClientRect();
    faceCanvas.width = rect.width;
    faceCanvas.height = rect.height;

    const ctx = faceCanvas.getContext("2d");
    ctx.clearRect(0, 0, faceCanvas.width, faceCanvas.height);

    const size = Math.min(rect.width, rect.height) * 0.55;
    const x = (rect.width - size) / 2;
    const y = (rect.height - size) / 2;

    ctx.strokeStyle = isFaceDetected ? "#10b981" : "#ef4444";
    ctx.lineWidth = 3;
    ctx.shadowColor = ctx.strokeStyle;
    ctx.shadowBlur = 8;

    ctx.strokeRect(x, y, size, size);
}

// Face Detection (ALONE, NOT NESTED)
async function detectFaceOnce() {
    const sessionAtStart = detectSessionId;
    if (!currentStream || !video.videoWidth) {
        guidanceText.classList.add("hidden");
        return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    try {
        const res = await fetch("/enroll/detect_face", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({ image: canvas.toDataURL("image/jpeg") })
        });

        // 🔒 OLD RESPONSE → IGNORE
        if (sessionAtStart !== detectSessionId) return;

        const { face_detected, face_count } = await res.json();
        const allowCapture = (face_count === 1);
        faceDetected = allowCapture;

        drawGreenBox(allowCapture);

        if (allowCapture) {
            guidanceText.textContent = "Face detected – hold still & capture";
            guidanceText.classList.remove("hidden");
            captureBtn.classList.remove("hidden");
        } else {
            guidanceText.textContent =
                face_count > 1
                    ? "Multiple faces detected. Only one person allowed"
                    : "Align your face inside the box";
            guidanceText.classList.add("hidden");
            captureBtn.classList.add("hidden");
        }

    } catch (err) {
        if (sessionAtStart !== detectSessionId) return;
        captureBtn.classList.add("hidden");
        guidanceText.classList.add("hidden");
        console.error(err);
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
            video.onloadeddata = () => drawGreenBox(false);
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
            alert("Camera not accessible!");
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
    if (!lastCapturedImage) return;
    if (loadingBox) loadingBox.classList.remove("hidden");
    let employeeId = window.location.pathname.split("/").pop();
    const csrfToken = getCSRFToken();
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
        alert("Face enrolled successfully!");
        window.location.href = "/enroll";
    } else {
        alert(data.message || "Enrollment failed");
    }
    // After save, reset buttons to initial state
    startCameraBtn.classList.remove("hidden");
    stopCameraBtn.classList.add("hidden");
    captureBtn.classList.add("hidden");
    previewBox.classList.add("hidden");
    actionBtns.classList.add("hidden");
    saveBtn.classList.add("hidden");
    retakeBtn.classList.add("hidden");
};
