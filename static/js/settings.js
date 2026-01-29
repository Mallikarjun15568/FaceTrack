if (window.__settingsLoaded) {
    console.warn('settings.js already initialized');
} else {
    window.__settingsLoaded = true;

    setTimeout(() => {
    // Dirty-tracking for smart Save enable/disable
    let dirty = false;

    const markDirty = () => {
        dirty = true;
        if (typeof saveBtn !== 'undefined' && saveBtn) saveBtn.disabled = false;
        if (typeof statusEl !== 'undefined' && statusEl) {
            statusEl.textContent = "Unsaved changes";
            statusEl.className = "text-sm text-orange-600";
        }
    };
    // Ensure persistent sticky action bar exists and is appended to document.body
    // Use #stickyActions as the presence check (not #saveBtn) to avoid false negatives
    if (!document.getElementById('stickyActions')) {
        const container = document.createElement('div');
        container.id = 'stickyActions';
        Object.assign(container.style, {
            position: 'fixed',
            right: '24px',
            bottom: '24px',
            zIndex: '99999',
            pointerEvents: 'auto',
            background: 'rgba(255,255,255,0.98)',
            padding: '8px 12px',
            borderRadius: '12px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.12)'
        });

        const inner = document.createElement('div');
        inner.style.display = 'flex';
        inner.style.gap = '12px';
        inner.style.alignItems = 'center';

        const save = document.createElement('button');
        save.id = 'saveBtn';
        save.className = 'btn-primary px-6 py-3 rounded-xl shadow-md hover:shadow-lg text-lg font-semibold flex items-center gap-2';
        save.innerHTML = '<i class="fas fa-save"></i> Save';

        const reset = document.createElement('button');
        reset.id = 'resetBtn';
        reset.className = 'btn-warning px-6 py-3 rounded-xl shadow-md hover:shadow-lg text-lg font-semibold flex items-center gap-2';
        reset.innerHTML = '<i class="fas fa-undo"></i> Reset';

        const status = document.createElement('span');
        status.id = 'status';
        status.className = 'text-gray-600 text-sm ml-2';

        inner.appendChild(save);
        inner.appendChild(reset);
        inner.appendChild(status);
        container.appendChild(inner);

        document.body.appendChild(container);

        // Reset action: confirm only if there are unsaved changes
        reset.addEventListener('click', () => {
            if (!dirty || confirm('Discard all unsaved changes?')) {
                location.reload();
            }
        });
    }

    const th = document.getElementById("recognition_threshold");
    const thVal = document.getElementById("th-val");
    // Safety: ensure slider value does not exceed HTML max (protect against template errors)
    const rawV = parseFloat(th.value);
    const rawMax = parseFloat(th.max);
    if (!isNaN(rawV) && !isNaN(rawMax) && rawV > rawMax) {
        th.value = rawMax;
        thVal.textContent = String(rawMax);
    } else {
        thVal.textContent = th.value;
    }

    th.addEventListener("input", () => {
        thVal.textContent = th.value;

        const v = parseFloat(th.value);
        if (!isNaN(v) && v > 0.55) {
            thVal.className = "text-orange-600 font-bold";
        } else {
            thVal.className = "text-blue-600 font-bold";
        }
    }, 0);

        const saveBtn = document.getElementById("saveBtn");
        const statusEl = document.getElementById("status");

        // Initial save state
        if (saveBtn) saveBtn.disabled = true;

        // Attach dirty listeners to inputs
        const inputs = document.querySelectorAll(
            "#recognition_threshold, #duplicate_interval, #snapshot_mode, #late_time, #checkout_time, #min_confidence, #company_name, #camera_index, #session_timeout, #login_alert"
        );
        inputs.forEach(el => {
            if (!el) return;
            el.addEventListener("change", markDirty);
            el.addEventListener("input", markDirty);
        });

    // Attach click handler safely (guard against duplicate bindings)
    if (saveBtn && !saveBtn.dataset.handlerAttached) {
        const saveHandler = () => {
            // start saving UI
            if (saveBtn) {
                saveBtn.disabled = true;
                saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            }
            if (statusEl) {
                statusEl.textContent = "Saving...";
                statusEl.className = "text-sm text-gray-600";
            }

            const data = {
                recognition_threshold: th.value,
                duplicate_interval: document.getElementById("duplicate_interval").value,
                snapshot_mode: document.getElementById("snapshot_mode").checked ? "on" : "off",
                late_time: document.getElementById("late_time").value,
                checkout_time: document.getElementById("checkout_time").value,
                min_confidence: document.getElementById("min_confidence").value,
                company_name: document.getElementById("company_name").value,
                camera_index: document.getElementById("camera_index").value,
                session_timeout: document.getElementById("session_timeout").value,
                login_alert: document.getElementById("login_alert").value
            };

            fetch("/admin/settings/api", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            })
            .then(res => res.json())
            .then(res => {
                if (res && res.success) {
                    if (statusEl) {
                        statusEl.textContent = "✓ Settings saved";
                        statusEl.className = "text-sm text-green-600";
                    }
                    dirty = false;
                } else {
                    if (statusEl) {
                        statusEl.textContent = "⚠ Failed to save";
                        statusEl.className = "text-sm text-red-600";
                    }
                }
            })
            .catch(() => {
                if (statusEl) {
                    statusEl.textContent = "⚠ Failed to save";
                    statusEl.className = "text-sm text-red-600";
                }
            })
            .finally(() => {
                if (saveBtn) {
                    saveBtn.innerHTML = '<i class="fas fa-save"></i> Save';
                    saveBtn.disabled = !dirty;
                }
                setTimeout(() => { if (statusEl) statusEl.textContent = ""; }, 2500);
            });
        };

        saveBtn.addEventListener('click', saveHandler);
        saveBtn.dataset.handlerAttached = '1';
    }


    // LOGO UPLOAD
    document.getElementById("uploadLogoBtn").onclick = () => {
        const file = document.getElementById("company_logo").files[0];
        if (!file) return alert("Choose a file");

        const fd = new FormData();
        fd.append("company_logo", file);

        fetch("/admin/settings/upload-logo", {
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
        window.location.href = "/admin/settings/export/attendance";
    };

    document.getElementById("exportEmployees").onclick = () => {
        window.location.href = "/admin/settings/export/employees";
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

    // CHANGE PASSWORD
    const changePasswordForm = document.getElementById("changePasswordForm");
    const passwordStatus = document.getElementById("passwordStatus");

    if (changePasswordForm) {
        changePasswordForm.onsubmit = async (e) => {
            e.preventDefault();

            const oldPassword = document.getElementById("old_password").value;
            const newPassword = document.getElementById("new_password").value;
            const confirmPassword = document.getElementById("confirm_password").value;

            if (newPassword !== confirmPassword) {
                passwordStatus.textContent = "✗ Passwords do not match.";
                passwordStatus.className = "text-sm mt-2 text-red-600";
                passwordStatus.classList.remove("hidden");
                setTimeout(() => passwordStatus.classList.add("hidden"), 3000);
                return;
            }

            if (newPassword.length < 8) {
                passwordStatus.textContent = "✗ Password must be at least 8 characters.";
                passwordStatus.className = "text-sm mt-2 text-red-600";
                passwordStatus.classList.remove("hidden");
                setTimeout(() => passwordStatus.classList.add("hidden"), 3000);
                return;
            }

            const formData = new FormData();
            formData.append("old_password", oldPassword);
            formData.append("new_password", newPassword);
            formData.append("confirm_password", confirmPassword);

            try {
                const response = await fetch("/admin/settings/change-password", {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    passwordStatus.textContent = "✓ Password changed successfully!";
                    passwordStatus.className = "text-sm mt-2 text-green-600";
                    changePasswordForm.reset();
                } else {
                    passwordStatus.textContent = "✗ " + (data.error || "Failed to change password");
                    passwordStatus.className = "text-sm mt-2 text-red-600";
                }
            } catch (error) {
                passwordStatus.textContent = "✗ Network error. Try again.";
                passwordStatus.className = "text-sm mt-2 text-red-600";
            }

            passwordStatus.classList.remove("hidden");
            setTimeout(() => passwordStatus.classList.add("hidden"), 5000);
        };
    }

    });
}
