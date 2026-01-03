let video = document.getElementById("camera");
let faceCanvas = document.getElementById("faceCanvas");
let captureBtn = document.getElementById("captureBtn");
let startCameraBtn = document.getElementById("startCameraBtn");
let stopCameraBtn = document.getElementById("stopCameraBtn");
let saveBtn = document.getElementById("saveBtn");
let previewImg = document.getElementById("previewImg");
let guidanceText = document.getElementById("guidanceText");

let lastImage = null;
let currentStream = null;

// Draw static green square
function drawGreenBox() {
    if (!faceCanvas || !video) return;
    
    const rect = video.getBoundingClientRect();
    if (faceCanvas.width !== rect.width || faceCanvas.height !== rect.height) {
        faceCanvas.width = rect.width;
        faceCanvas.height = rect.height;
    }
    
    const ctx = faceCanvas.getContext("2d");
    ctx.clearRect(0, 0, faceCanvas.width, faceCanvas.height);
    
    const boxSize = Math.min(faceCanvas.width, faceCanvas.height) * 0.55;
    const x = (faceCanvas.width - boxSize) / 2;
    const y = (faceCanvas.height - boxSize) / 2;
    
    ctx.strokeStyle = "#10b981"; // green
    ctx.lineWidth = 3;
    ctx.shadowColor = "#10b981";
    ctx.shadowBlur = 8;
    
    ctx.beginPath();
    ctx.rect(x, y, boxSize, boxSize);
    ctx.stroke();
    
    if (guidanceText) {
        guidanceText.textContent = "Align your face in the box";
        guidanceText.classList.remove("hidden");
    }
}

// Start Camera
function startCamera() {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            currentStream = stream;
            video.srcObject = stream;
            
            // Update buttons
            if (startCameraBtn) startCameraBtn.classList.add("hidden");
            if (stopCameraBtn) stopCameraBtn.classList.remove("hidden");
            if (captureBtn) captureBtn.disabled = false;
            
            // Draw green box when video loads
            video.addEventListener('loadeddata', () => {
                console.log("Camera started");
                drawGreenBox();
            }, { once: true });
        })
        .catch(err => {
            alert("Camera not accessible!");
            console.error(err);
        });
}

// Stop Camera
function stopCamera() {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        currentStream = null;
        
        // Update buttons
        if (stopCameraBtn) stopCameraBtn.classList.add("hidden");
        if (startCameraBtn) startCameraBtn.classList.remove("hidden");
        if (captureBtn) captureBtn.disabled = true;
        
        // Clear canvas
        if (faceCanvas) {
            const ctx = faceCanvas.getContext("2d");
            ctx.clearRect(0, 0, faceCanvas.width, faceCanvas.height);
        }
        if (guidanceText) guidanceText.classList.add("hidden");
    }
}

// Auto-start camera on load
startCamera();

// Button events
if (startCameraBtn) {
    startCameraBtn.addEventListener("click", startCamera);
}

if (stopCameraBtn) {
    stopCameraBtn.addEventListener("click", stopCamera);
}

// Capture Frame
captureBtn.onclick = () => {
    let canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    let ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    lastImage = canvas.toDataURL("image/jpeg");

    previewImg.src = lastImage;
    previewImg.classList.remove("hidden");
    saveBtn.classList.remove("hidden");
};


// Save Updated Face
saveBtn.onclick = async () => {
    if (!lastImage) {
        alert("Please capture image first.");
        return;
    }

    let employeeId = window.location.pathname.split("/").pop();

    let res = await fetch("/enroll/update_capture", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            employee_id: employeeId,
            image: lastImage
        })
    });

    let data = await res.json();

    alert(data.message);

    if (data.status === "success") {
        window.location.href = "/enroll";
    }
};
