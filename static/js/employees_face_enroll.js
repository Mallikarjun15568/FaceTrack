let video = document.getElementById("cameraFeed");
let capturedImg = document.getElementById("capturedImage");
let captureBtn = document.getElementById("captureBtn");
let saveBtn = document.getElementById("saveBtn");

let capturedBase64 = null;

// Start camera
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        alert("Camera not available: " + err);
    });

// Capture Frame
captureBtn.addEventListener("click", () => {
    let canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    let ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    capturedBase64 = canvas.toDataURL("image/jpeg");
    capturedImg.src = capturedBase64;

    saveBtn.disabled = false;
});

// Save to backend
saveBtn.addEventListener("click", () => {

    if (!capturedBase64) {
        alert("Please capture image first.");
        return;
    }

    let employeeId = window.location.pathname.split("/").pop();

    fetch("/enroll/capture", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            employee_id: employeeId,
            image: capturedBase64
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            alert("Face saved successfully!");
            saveBtn.disabled = true;
        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(err => {
        alert("Network error: " + err);
    });

});
