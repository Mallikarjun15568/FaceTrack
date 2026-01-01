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

let stream = null;
let running = false;
let matchCount = 0;

const REQUIRED_MATCHES = 2;
const CAPTURE_INTERVAL = 700; // ms
const JPEG_QUALITY = 0.6;
const MAX_RETRY_NETWORK = 2;

/* Helpers: show modal / hide modal */
function openModal() {
  modal.classList.remove("hidden");
  document.body.classList.add("overflow-hidden");
  faceSuccess.classList.add("hidden");
  modalStatus.textContent = "Starting camera…";
  matchCount = 0;
  startCamera();
}

function closeModal() {
  stopCamera();
  modal.classList.add("hidden");
  document.body.classList.remove("overflow-hidden");
}

/* Safe status update */
function setStatus(text, type = "muted") {
  modalStatus.textContent = text;
  // type: muted | success | error
  modalStatus.classList.remove("text-red-600", "text-green-600", "text-gray-600");
  if (type === "error") modalStatus.classList.add("text-red-600");
  else if (type === "success") modalStatus.classList.add("text-green-600");
  else modalStatus.classList.add("text-gray-600");
}

/* Camera control */
async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
    modalCam.srcObject = stream;
    running = true;
    setStatus("Camera started. Hold still and face the camera.", "muted");
    captureLoop();
  } catch (err) {
    console.error("Camera start error:", err);
    setStatus("Camera permission denied or not available.", "error");
  }
}

function stopCamera() {
  running = false;
  matchCount = 0;
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }
  modalCam.srcObject = null;
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
  faceSuccess.classList.remove("hidden");
  setStatus("Matched! Redirecting…", "success");
  // small delay so user sees check
  setTimeout(() => {
    closeModal();
    window.location.href = url;
  }, 900);
}

/* Main loop: capture -> send -> evaluate */
async function captureLoop() {
  while (running) {
    if (modalCam.readyState >= 2) {
      const image = captureFrame();
      const result = await sendFrameToServer(image);

      if (result && result.matched) {
        matchCount++;
        setStatus(`Matched: ${result.name} (${matchCount}/${REQUIRED_MATCHES})`, "success");

        if (matchCount >= REQUIRED_MATCHES) {
          showSuccessThenRedirect(result.redirect_url || "/dashboard");
          return;
        }
      } else if (result && result.reason) {
        matchCount = 0;
        // Friendly messages for common reasons
        if (result.reason.toLowerCase().includes("no face")) setStatus("No face detected — adjust lighting.", "error");
        else if (result.reason.toLowerCase().includes("no match")) setStatus("Face not recognized — try again.", "error");
        else setStatus(result.reason, "error");
      } else if (result && result.error) {
        setStatus("Server/network error. Try again later.", "error");
      }
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
