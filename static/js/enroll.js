document.addEventListener("DOMContentLoaded", () => {
  // === DOM Elements ===
  const video = document.getElementById("webcam");
  const captureBtn = document.getElementById("captureBtn");
  const retakeBtn = document.getElementById("retakeBtn");
  const form = document.getElementById("enrollForm");
  const imagePreview = document.getElementById("imagePreview");
  const webcamContainer = document.querySelector(".webcam-container");
  const previewContainer = document.querySelector(".preview-container");
  const fileInput = document.getElementById("image");
  const passwordInput = document.getElementById("password");
  const togglePassword = document.querySelector(".toggle-password");
  const refreshList = document.getElementById("refreshList");

  let stream = null;

  // === Initialize Webcam ===
  async function initWebcam() {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ 
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user"
        }
      });
      video.srcObject = stream;
      captureBtn.disabled = false;
    } catch (err) {
      console.error("Webcam error:", err);
      showNotification("Could not access webcam. Please check permissions.", "error");
      captureBtn.disabled = true;
    }
  }

  initWebcam();

  // === Handle File Upload ===
  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        showPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  });

  // === Handle Drag and Drop ===
  const uploadContainer = document.querySelector(".upload-container");
  
  uploadContainer.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadContainer.classList.add("dragover");
  });

  uploadContainer.addEventListener("dragleave", () => {
    uploadContainer.classList.remove("dragover");
  });

  uploadContainer.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadContainer.classList.remove("dragover");
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      fileInput.files = e.dataTransfer.files;
      const reader = new FileReader();
      reader.onload = (e) => {
        showPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    } else {
      showNotification("Please drop an image file", "error");
    }
  });
});