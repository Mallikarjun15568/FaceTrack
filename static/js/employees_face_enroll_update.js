let video = document.getElementById("camera");
let captureBtn = document.getElementById("captureBtn");
let saveBtn = document.getElementById("saveBtn");
let previewImg = document.getElementById("previewImg");

let lastImage = null;

// Start Camera
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => {
        alert("Camera not available: " + err);
    });


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
