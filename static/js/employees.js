        // =======================
        // ACTIVATE EMPLOYEE LOGIC
        // =======================
        window.activateEmployee = function (empId) {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            fetch(`/admin/employees/activate/${empId}`, {
                method: "POST",
                headers: {
                    'X-CSRFToken': csrfToken || ''
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) location.reload();
                else alert("Failed to activate employee");
            })
            .catch(err => {
                console.error("Error activating employee:", err);
                alert("Error activating employee");
            });
        };
        
        // =======================
        // DEACTIVATE EMPLOYEE LOGIC
        // =======================
        let deactivateEmpId = null;
        let deactivateModal = null;
        let confirmDeactivateBtn = null;
        
        window.openDeactivateModal = function (empId) {
            deactivateEmpId = empId;
            if (deactivateModal) {
                deactivateModal.classList.remove('hidden');
            }
        };
        
        window.closeDeactivateModal = function () {
            deactivateEmpId = null;
            if (deactivateModal) {
                deactivateModal.classList.add("hidden");
                // Force repaint for Chrome overlay bug
                deactivateModal.offsetHeight;
            }
        };
        
        // Toggle helper used by inline buttons in the template
        window.toggleEmployee = function(empId, action) {
            if (!empId || !action) return;
            action = String(action).toLowerCase();
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            if (action === 'activate') {
                if (typeof window.activateEmployee === 'function') {
                    window.activateEmployee(empId);
                } else {
                    // fallback: do direct fetch
                    fetch(`/admin/employees/activate/${empId}`, { 
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken || ''
                        }
                    })
                        .then(r => r.json()).then(d => { if (d.success) location.reload(); else alert('Failed to activate employee'); });
                }
            } else if (action === 'deactivate') {
                if (typeof window.openDeactivateModal === 'function') {
                    window.openDeactivateModal(empId);
                } else {
                    // fallback: perform direct deactivate (without confirmation)
                    if (!confirm('Deactivate employee?')) return;
                    fetch(`/admin/employees/deactivate/${empId}`, { 
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken || ''
                        }
                    })
                        .then(r => r.json()).then(d => { if (d.success) location.reload(); else alert('Failed to deactivate employee'); });
                }
            }
        };

document.addEventListener("DOMContentLoaded", function () {

    // =======================
    // SEARCH LOADING STATE
    // =======================
    const searchForm = document.querySelector('form[method="GET"]');
    const searchBtn = document.getElementById('searchBtn');
    const searchText = document.getElementById('searchText');

    if (searchForm && searchBtn) {
        const hideLoading = () => {
            try {
                searchBtn.disabled = false;
                searchBtn.classList.remove('opacity-75', 'cursor-not-allowed');
                if (searchText) searchText.textContent = 'Search & Filter';
            } catch (e) { console.error(e); }
        };

        searchForm.addEventListener('submit', function (e) {
            // Show loading state
            if (searchBtn && searchText) {
                searchBtn.disabled = true;
                searchBtn.classList.add('opacity-75', 'cursor-not-allowed');
                const icon = document.getElementById('searchIcon');
                if (icon) {
                    icon.className = 'fas fa-spinner fa-spin mr-2';
                }
                searchText.textContent = 'Searching...';
            }
            
            const isAjax = searchForm.dataset.ajax === 'true';
            // Show loading state - rely on normal form submission
        });
    }

    // =======================
    // DEACTIVATE MODAL HANDLING
    // =======================
    deactivateModal = document.getElementById('deactivateModal');
    confirmDeactivateBtn = document.getElementById('confirmDeactivateBtn');
    if (confirmDeactivateBtn) {
        confirmDeactivateBtn.addEventListener("click", () => {
            if (!deactivateEmpId) return;

            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            fetch(`/admin/employees/deactivate/${deactivateEmpId}`, {
                method: "POST",
                headers: {
                    'X-CSRFToken': csrfToken || ''
                }
            })
            .then(res => res.json())
            .then(data => {
                window.closeDeactivateModal();
                if (data.success) {
                    location.reload();
                } else {
                    alert("Failed to deactivate employee");
                }
            })
            .catch(err => {
                console.error(err);
                window.closeDeactivateModal();
                alert("Error deactivating employee");
            });
        });
    }

});
