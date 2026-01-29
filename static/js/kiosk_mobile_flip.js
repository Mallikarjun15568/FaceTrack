// ===== Mobile Camera Flip Feature =====
// Allows switching between front and back cameras on mobile devices

(function() {
    const flipCameraBtn = document.getElementById("flipCameraBtn");
    
    if (!flipCameraBtn) {
        console.log('No flip button found');
        return;
    }
    
    flipCameraBtn.addEventListener("click", async () => {
        // Access global variables from kiosk.js
        if (!window.cameraRunning || window.startingCamera) return;
        
        console.log('🔄 Flipping camera...');
        flipCameraBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        flipCameraBtn.disabled = true;
        
        try {
            const video = document.getElementById("kioskVideo");
            
            // Stop current stream
            if (window.stream) {
                window.stream.getTracks().forEach(t => t.stop());
                video.srcObject = null;
            }
            
            // Toggle facing mode
            window.currentFacingMode = window.currentFacingMode === 'user' ? 'environment' : 'user';
            
            // Request new camera
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: window.currentFacingMode
                },
                audio: false
            };
            
            window.stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = window.stream;
            
            await video.play();
            setTimeout(() => {
                video.style.opacity = '1';
            }, 100);
            
            const cameraName = window.currentFacingMode === 'user' ? 'Front 🤳' : 'Back 📸';
            console.log(`✅ Switched to ${cameraName} camera`);
            
            // Show toast notification
            const toast = document.createElement('div');
            toast.className = 'fixed top-20 left-1/2 -translate-x-1/2 bg-black/80 text-white px-4 py-2 rounded-lg z-50 transition-opacity';
            toast.textContent = `Switched to ${cameraName}`;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, 2000);
            
        } catch (err) {
            console.error('❌ Camera flip failed:', err);
            // Revert on error
            window.currentFacingMode = window.currentFacingMode === 'user' ? 'environment' : 'user';
            
            // Show error toast
            const toast = document.createElement('div');
            toast.className = 'fixed top-20 left-1/2 -translate-x-1/2 bg-red-600/90 text-white px-4 py-2 rounded-lg z-50';
            toast.textContent = 'Camera switch failed';
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 2000);
        } finally {
            flipCameraBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
            flipCameraBtn.disabled = false;
        }
    });
})();
