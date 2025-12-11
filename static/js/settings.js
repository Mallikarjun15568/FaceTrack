document.addEventListener("DOMContentLoaded", () => {

    const th = document.getElementById("recognition_threshold");
    const thVal = document.getElementById("th-val");
    thVal.textContent = th.value;

    th.addEventListener("input", () => {
        thVal.textContent = th.value;
    });

    const saveBtn = document.getElementById("saveBtn");
    const statusEl = document.getElementById("status");

    saveBtn.onclick = () => {
        saveBtn.disabled = true;
        statusEl.textContent = "Saving...";

        const data = {
            recognition_threshold: th.value,
            duplicate_interval: document.getElementById("duplicate_interval").value,
            snapshot_mode: document.getElementById("snapshot_mode").checked ? "on" : "off",
            late_time: document.getElementById("late_time").value,
            min_confidence: document.getElementById("min_confidence").value,
            company_name: document.getElementById("company_name").value,
            camera_index: document.getElementById("camera_index").value,
            session_timeout: document.getElementById("session_timeout").value,
            login_alert: document.getElementById("login_alert").value
        };

        fetch("/settings/api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(res => {
            statusEl.textContent = res.success ? "Saved" : "Error";
        })
        .finally(() => {
            saveBtn.disabled = false;
            setTimeout(() => statusEl.textContent = "", 2000);
        });
    };


    // LOGO UPLOAD
    document.getElementById("uploadLogoBtn").onclick = () => {
        const file = document.getElementById("company_logo").files[0];
        if (!file) return alert("Choose a file");

        const fd = new FormData();
        fd.append("company_logo", file);

        fetch("/settings/upload-logo", {
            method: "POST",
            body: fd
        })
        .then(res => res.json())
        .then(res => {
            if (res.success) {
                document.getElementById("logo_preview").src = res.path + "?v=" + Date.now();
                alert("Uploaded");
            } else {
                alert("Upload failed");
            }
        });
    };


    // EXPORT BUTTONS
    document.getElementById("exportAttendance").onclick = () => {
        window.location.href = "/settings/export/attendance";
    };

    document.getElementById("exportEmployees").onclick = () => {
        window.location.href = "/settings/export/employees";
    };


    // KIOSK PIN SET
    const setPinBtn = document.getElementById("setPinBtn");
    const pinInput = document.getElementById("kiosk_pin");
    const pinStatus = document.getElementById("pinStatus");

    setPinBtn.onclick = async () => {
        const pin = pinInput.value.trim();
        
        // Validation
        if (!pin) {
            pinStatus.textContent = "Please enter a PIN.";
            pinStatus.className = "text-sm mt-1 text-red-600";
            pinStatus.classList.remove("hidden");
            return;
        }

        if (!/^\d+$/.test(pin)) {
            pinStatus.textContent = "PIN must be numeric.";
            pinStatus.className = "text-sm mt-1 text-red-600";
            pinStatus.classList.remove("hidden");
            return;
        }

        if (pin.length < 4) {
            pinStatus.textContent = "PIN must be at least 4 digits.";
            pinStatus.className = "text-sm mt-1 text-red-600";
            pinStatus.classList.remove("hidden");
            return;
        }

        // Send to backend
        setPinBtn.disabled = true;
        pinStatus.textContent = "Setting PIN...";
        pinStatus.className = "text-sm mt-1 text-gray-600";
        pinStatus.classList.remove("hidden");

        try {
            const response = await fetch("/kiosk/admin/set_pin", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pin })
            });

            const data = await response.json();

            if (data.success) {
                pinStatus.textContent = "✓ Kiosk PIN updated successfully.";
                pinStatus.className = "text-sm mt-1 text-green-600";
                pinInput.value = "";
            } else {
                pinStatus.textContent = data.message || "Failed to set PIN.";
                pinStatus.className = "text-sm mt-1 text-red-600";
            }
        } catch (error) {
            pinStatus.textContent = "Network error. Try again.";
            pinStatus.className = "text-sm mt-1 text-red-600";
        } finally {
            setPinBtn.disabled = false;
            setTimeout(() => pinStatus.classList.add("hidden"), 3000);
        }
    };


    // REMOTE UNLOCK
    const remoteUnlockBtn = document.getElementById("remoteUnlockBtn");
    const unlockStatus = document.getElementById("unlockStatus");

    remoteUnlockBtn.onclick = async () => {
        if (!confirm("Force unlock kiosk? This will allow anyone to exit kiosk mode.")) {
            return;
        }

        remoteUnlockBtn.disabled = true;
        remoteUnlockBtn.textContent = "Unlocking...";
        unlockStatus.classList.add("hidden");

        try {
            const response = await fetch("/kiosk/admin/force_unlock", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });

            const data = await response.json();

            if (data.success) {
                unlockStatus.textContent = "✓ Kiosk unlocked successfully.";
                unlockStatus.className = "text-sm mt-1 text-green-600";
            } else {
                unlockStatus.textContent = data.message || "Failed to unlock.";
                unlockStatus.className = "text-sm mt-1 text-red-600";
            }
        } catch (error) {
            unlockStatus.textContent = "Network error. Try again.";
            unlockStatus.className = "text-sm mt-1 text-red-600";
        } finally {
            remoteUnlockBtn.disabled = false;
            remoteUnlockBtn.innerHTML = '<svg class="w-4 h-4 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"></path></svg> Force Unlock Kiosk';
            unlockStatus.classList.remove("hidden");
            setTimeout(() => unlockStatus.classList.add("hidden"), 3000);
        }
    };

});
