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

// CSRF helper for AJAX
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

// Start Camera
function startCamera() {
    detectSessionId++;   // 🔥 NEW SESSION
    isCaptured = false; // 🔓 unlock UI
    faceDetected = false;
    lastDetectState = null;
    captureBtn.classList.add("hidden"); // reset state on camera start
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            currentStream = stream;
            video.srcObject = stream;
            cameraInactiveBox.classList.add("hidden");
            video.classList.remove("hidden");
            faceCanvas.classList.remove("hidden");
            guidanceText.classList.remove("hidden");
            startCameraBtn.classList.add("hidden");
            stopCameraBtn.classList.remove("hidden");
            previewImg.classList.add("hidden");
            saveBtn.classList.add("hidden");
            retakeBtn.classList.add("hidden");
            video.onloadeddata = () => {
                setTimeout(() => drawGreenBox(false), 100);
            };
            if (detectInterval) {
                clearInterval(detectInterval);
            }
            detectInterval = setInterval(detectFaceOnce, 600);
        })
        .catch(err => {
            cameraInactiveBox.classList.remove("hidden");
            video.classList.add("hidden");
            faceCanvas.classList.add("hidden");
            guidanceText.classList.add("hidden");
            alert("Camera not accessible!");
            console.error(err);
        });
}

// Stop Camera
function stopCamera() {
    detectSessionId++;   // 🔥 INVALIDATE OLD REQUESTS
    isCaptured = false; // Camera stopped, not photo captured
    faceDetected = false;
    if (detectInterval) {
        clearInterval(detectInterval);
        detectInterval = null;
    }
    lastDetectState = null;
    if (!currentStream) {
        cameraInactiveBox.classList.remove("hidden");
        video.classList.add("hidden");
        faceCanvas.classList.add("hidden");
        guidanceText.classList.add("hidden");
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
    startCameraBtn.classList.remove("hidden");
    stopCameraBtn.classList.add("hidden");
    captureBtn.classList.add("hidden");
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
video.classList.add("hidden");
faceCanvas.classList.add("hidden");
guidanceText.classList.add("hidden");
captureBtn.classList.add("hidden");

// Button events
startCameraBtn.addEventListener("click", startCamera);
stopCameraBtn.addEventListener("click", stopCamera);

captureBtn.onclick = () => {
    if (!currentStream || !faceDetected) return;

    isCaptured = true; // 🔒 LOCK UI STATE

    if (detectInterval) {
        clearInterval(detectInterval);
        detectInterval = null;
    }

    faceDetected = false;
    let canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    lastImage = canvas.toDataURL("image/jpeg");
    previewImg.src = lastImage;
    previewImg.classList.remove("hidden");
    saveBtn.classList.remove("hidden");
    retakeBtn.classList.remove("hidden");
    captureBtn.classList.add("hidden");
    guidanceText.classList.add("hidden");
    stopCameraBtn.classList.add("hidden");
    startCameraBtn.classList.add("hidden");
    if (currentStream) {
        currentStream.getTracks().forEach(t => t.stop());
        video.srcObject = null;
        currentStream = null;
    }
    video.classList.add("hidden");
    faceCanvas.classList.add("hidden");
    cameraInactiveBox.classList.add("hidden");
};

retakeBtn.onclick = () => {
    isCaptured = false;   // 🔓 UNLOCK
    lastImage = null;
    previewImg.classList.add("hidden");
    saveBtn.classList.add("hidden");
    retakeBtn.classList.add("hidden");
    startCamera();
};

saveBtn.onclick = async () => {
    if (!lastImage) return;
    const employeeId = window.location.pathname.split("/").pop();
    const csrfToken = getCSRFToken();
    let res = await fetch("/enroll/update_capture", {
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
        alert("Face updated successfully!");
        window.location.href = "/enroll";
    } else {
        alert(data.message || "Update failed");
    }
    startCameraBtn.classList.remove("hidden");
    stopCameraBtn.classList.add("hidden");
    captureBtn.classList.add("hidden");
    previewImg.classList.add("hidden");
    saveBtn.classList.add("hidden");
    retakeBtn.classList.add("hidden");
};

// Face Detection
async function detectFaceOnce() {
    const sessionAtStart = detectSessionId;
    if (isCaptured || !detectInterval) return;
    if (!currentStream || !video.videoWidth) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    try {
        const { face_count } = await (await fetch("/enroll/detect_face", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({ image: canvas.toDataURL("image/jpeg") })
        })).json();

        // 🔒 HARD GUARD — OLD RESPONSE
        if (sessionAtStart !== detectSessionId) return;

        let allowCapture = (face_count === 1);
        faceDetected = allowCapture;
        drawGreenBox(allowCapture);
        if (!isCaptured && allowCapture) {
            captureBtn.classList.remove("hidden");
        } else {
            captureBtn.classList.add("hidden");
        }

        showGuidance(
            face_count === 1
                ? "Face detected – hold still & capture"
                : face_count > 1
                    ? "Multiple faces detected. Only one person allowed"
                    : "Align your face inside the box"
        );
        lastDetectState = face_count;
    } catch (err) {
        if (sessionAtStart !== detectSessionId) return;
        captureBtn.classList.add("hidden");
        guidanceText.textContent = "Detection error";
    }
}
