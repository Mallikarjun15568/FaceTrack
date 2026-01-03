// ================================
// FACE ID LOGIN — Premium Modal + Scanning
// ================================

/* Elements */
const faceBtn = document.getElementById("loginFaceID");
const modal = document.getElementById("faceModal");
const backdrop = document.getElementById("faceBackdrop");
const modalCam = document.getElementById("modalFaceCam");
const modalStatus = document.getElementById("modalStatus");
const modalCancel = document.getElementById("modalCancel");
const modalForce = document.getElementById("modalForceCapture");
const faceSuccess = document.getElementById("faceSuccess");
const scanningOverlay = document.getElementById("scanningOverlay");
const processingOverlay = document.getElementById("processingOverlay");
const faceCanvas = document.getElementById("faceCanvas");

let stream = null;
let running = false;
let matchCount = 0;
let faceDetected = false;

const REQUIRED_MATCHES = 1; // Single match for instant login
const CAPTURE_INTERVAL = 1200; // Slower for better CSRF handling - 1200ms
const JPEG_QUALITY = 0.7;
const MAX_RETRY_NETWORK = 2;

/* Helpers: show modal / hide modal */
function openModal() {
  modal.classList.remove("hidden");
  document.body.classList.add("overflow-hidden");
  faceSuccess.classList.add("hidden");
  scanningOverlay.classList.add("hidden");
  processingOverlay.classList.add("hidden");
  setStatus("Starting camera…", "muted");
  matchCount = 0;
  startCamera();
}

function closeModal() {
  stopCamera();
  modal.classList.add("hidden");
  document.body.classList.remove("overflow-hidden");
  scanningOverlay.classList.add("hidden");
  processingOverlay.classList.add("hidden");
}

/* Safe status update with icons */
function setStatus(text, type = "muted") {
  let icon = '<i class="fas fa-circle-notch fa-spin text-indigo-600 mr-2"></i>';
  
  if (type === "error") {
    icon = '<i class="fas fa-exclamation-circle text-red-600 mr-2"></i>';
    modalStatus.className = "text-sm font-medium text-red-600 min-h-[22px] text-center";
  } else if (type === "success") {
    icon = '<i class="fas fa-check-circle text-green-600 mr-2"></i>';
    modalStatus.className = "text-sm font-medium text-green-600 min-h-[22px] text-center";
  } else if (type === "scanning") {
    icon = '<i class="fas fa-radar text-indigo-600 mr-2 animate-pulse"></i>';
    modalStatus.className = "text-sm font-medium text-indigo-600 min-h-[22px] text-center";
  } else {
    modalStatus.className = "text-sm font-medium text-gray-700 min-h-[22px] text-center";
  }
  
  modalStatus.innerHTML = icon + text;
}

/* Camera control */
async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        facingMode: "user",
        width: { ideal: 640 },
        height: { ideal: 480 }
      }, 
      audio: false 
    });
    modalCam.srcObject = stream;
    running = true;
    
    // Wait for video to be ready
    modalCam.onloadedmetadata = () => {
      scanningOverlay.classList.remove("hidden");
      scanningOverlay.classList.add("flex");
      setStatus("Ready! Scanning for face...", "scanning");
      captureLoop();
    };
  } catch (err) {
    console.error("Camera start error:", err);
    setStatus("Camera permission denied or not available.", "error");
  }
}

function stopCamera() {
  running = false;
  matchCount = 0;
  faceDetected = false;
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  modalCam.srcObject = null;
  scanningOverlay.classList.add("hidden");
  processingOverlay.classList.add("hidden");
  
  // Clear canvas
  if (faceCanvas) {
    const ctx = faceCanvas.getContext("2d");
    ctx.clearRect(0, 0, faceCanvas.width, faceCanvas.height);
  }
}

/* Capture frame as compressed JPEG dataURL */
function captureFrame() {
  const v = modalCam;
  const w = v.videoWidth || 320;
  const h = v.videoHeight || 240;
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(v, 0, 0, w, h);
  return canvas.toDataURL("image/jpeg", JPEG_QUALITY);
}

/* Draw face detection box on canvas overlay */
function drawFaceBox(hasFace) {
  const canvas = faceCanvas;
  const video = modalCam;
  
  if (!canvas || !video) return;
  
  // Match canvas size to video display size
  const rect = video.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  if (hasFace) {
    // Draw centered face box (approximation since backend detects face)
    const boxSize = Math.min(canvas.width, canvas.height) * 0.7;
    const x = (canvas.width - boxSize) / 2;
    const y = (canvas.height - boxSize) / 2;
    
    // Draw rounded rectangle with pulsing effect
    ctx.strokeStyle = "#10b981"; // green-500
    ctx.lineWidth = 3;
    ctx.shadowColor = "#10b981";
    ctx.shadowBlur = 10;
    
    // Rounded corners
    const radius = 15;
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + boxSize - radius, y);
    ctx.arcTo(x + boxSize, y, x + boxSize, y + radius, radius);
    ctx.lineTo(x + boxSize, y + boxSize - radius);
    ctx.arcTo(x + boxSize, y + boxSize, x + boxSize - radius, y + boxSize, radius);
    ctx.lineTo(x + radius, y + boxSize);
    ctx.arcTo(x, y + boxSize, x, y + boxSize - radius, radius);
    ctx.lineTo(x, y + radius);
    ctx.arcTo(x, y, x + radius, y, radius);
    ctx.closePath();
    ctx.stroke();
    
    // Corner markers
    const cornerSize = 20;
    ctx.strokeStyle = "#10b981";
    ctx.lineWidth = 4;
    
    // Top-left
    ctx.beginPath();
    ctx.moveTo(x + cornerSize, y);
    ctx.lineTo(x, y);
    ctx.lineTo(x, y + cornerSize);
    ctx.stroke();
    
    // Top-right
    ctx.beginPath();
    ctx.moveTo(x + boxSize - cornerSize, y);
    ctx.lineTo(x + boxSize, y);
    ctx.lineTo(x + boxSize, y + cornerSize);
    ctx.stroke();
    
    // Bottom-left
    ctx.beginPath();
    ctx.moveTo(x, y + boxSize - cornerSize);
    ctx.lineTo(x, y + boxSize);
    ctx.lineTo(x + cornerSize, y + boxSize);
    ctx.stroke();
    
    // Bottom-right
    ctx.beginPath();
    ctx.moveTo(x + boxSize - cornerSize, y + boxSize);
    ctx.lineTo(x + boxSize, y + boxSize);
    ctx.lineTo(x + boxSize, y + boxSize - cornerSize);
    ctx.stroke();
  }
}

/* Send to backend and parse JSON safely */
async function sendFrameToServer(imageData) {
  let tries = 0;
  while (tries <= MAX_RETRY_NETWORK) {
    tries++;
    try {
      // Get CSRF token from meta tag
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
      
      const headers = { "Content-Type": "application/json" };
      if (csrfToken) {
        headers["X-CSRFToken"] = csrfToken;
      }
      
      const resp = await fetch("/auth/face_login", {
        method: "POST",
        headers: headers,
        body: JSON.stringify({ image: imageData }),
      });
      
      if (resp.status === 403) {
        // CSRF or security error
        const json = await resp.json();
        return json; // Will have reason field
      }
      
      if (!resp.ok) {
        // server returned error page or 5xx
        const text = await resp.text();
        console.error("Server returned non-OK:", resp.status, text);
        return { error: "Server error" };
      }
      const json = await resp.json();
      return json;
    } catch (e) {
      console.warn("Network error, retrying...", e);
      if (tries > MAX_RETRY_NETWORK) return { error: "Network error" };
      await new Promise(r => setTimeout(r, 300));
    }
  }
}

/* Visual success animation */
function showSuccessThenRedirect(url) {
  scanningOverlay.classList.add("hidden");
  processingOverlay.classList.add("hidden");
  faceSuccess.classList.remove("hidden");
  faceSuccess.classList.add("flex");
  setStatus("Authentication successful!", "success");
  
  // Redirect after animation
  setTimeout(() => {
    closeModal();
    window.location.href = url;
  }, 1200);
}

/* Main loop: capture -> send -> evaluate */
async function captureLoop() {
  while (running) {
    if (modalCam.readyState >= 2) {
      // Show processing state briefly
      processingOverlay.classList.remove("hidden");
      processingOverlay.classList.add("flex");
      
      const image = captureFrame();
      const result = await sendFrameToServer(image);
      
      // Hide processing state
      processingOverlay.classList.add("hidden");

      if (result && result.matched) {
        matchCount++;
        faceDetected = true;
        drawFaceBox(true); // Show green box on match
        setStatus(`Matched: ${result.name} (${matchCount}/${REQUIRED_MATCHES})`, "success");

        if (matchCount >= REQUIRED_MATCHES) {
          showSuccessThenRedirect(result.redirect_url || "/dashboard");
          return;
        }
      } else if (result && result.not_enrolled) {
        // Special handling for non-enrolled faces
        faceDetected = false;
        drawFaceBox(false);
        setStatus("⚠️ Face not enrolled. Please enroll your face first from the Enroll page.", "error");
        matchCount = 0;
        await new Promise(r => setTimeout(r, 3000)); // Show message longer
      } else if (result && result.reason) {
        matchCount = 0;
        // Friendly messages for common reasons
        if (result.reason.toLowerCase().includes("no face")) {
          faceDetected = false;
          drawFaceBox(false);
          setStatus("Position your face in frame", "error");
        } else if (result.reason.toLowerCase().includes("security validation")) {
          setStatus("Security error. Please refresh the page.", "error");
          running = false; // Stop loop on CSRF errors
          await new Promise(r => setTimeout(r, 2000));
          closeModal();
          return;
        } else {
          faceDetected = false;
          drawFaceBox(false);
          setStatus(result.reason, "error");
        }
      } else if (result && result.error) {
        faceDetected = false;
        drawFaceBox(false);
        setStatus("Connection error. Retrying...", "error");
      }
    } else {
      setStatus("Waiting for camera...", "muted");
    }
    await new Promise(r => setTimeout(r, CAPTURE_INTERVAL));
  }
}

/* Button handlers */
faceBtn.addEventListener("click", openModal);
modalCancel.addEventListener("click", closeModal);
modalForce.addEventListener("click", async () => {
  if (!running) {
    setStatus("Camera not ready.", "error");
    return;
  }
  // Immediate single capture
  const image = captureFrame();
  const result = await sendFrameToServer(image);
  if (result && result.matched) {
    showSuccessThenRedirect(result.redirect_url || "/dashboard");
  } else {
    setStatus(result.reason || "No match", "error");
  }
});

/* cleanup on page hide */
window.addEventListener("beforeunload", () => {
  stopCamera();
  modal.classList.add("hidden");
});
