        // =======================
        // ACTIVATE EMPLOYEE LOGIC
        // =======================
        window.activateEmployee = function (empId) {
            fetch(`/admin/employees/activate/${empId}`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) location.reload();
                else alert("Failed to activate employee");
            });
        };
        
        // Toggle helper used by inline buttons in the template
        window.toggleEmployee = function(empId, action) {
            if (!empId || !action) return;
            action = String(action).toLowerCase();
            if (action === 'activate') {
                if (typeof window.activateEmployee === 'function') {
                    window.activateEmployee(empId);
                } else {
                    // fallback: do direct fetch
                    fetch(`/admin/employees/activate/${empId}`, { method: 'POST', headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content } })
                        .then(r => r.json()).then(d => { if (d.success) location.reload(); else alert('Failed to activate employee'); });
                }
            } else if (action === 'deactivate') {
                if (typeof window.openDeactivateModal === 'function') {
                    window.openDeactivateModal(empId);
                } else {
                    // fallback: perform direct deactivate (without confirmation)
                    if (!confirm('Deactivate employee?')) return;
                    fetch(`/admin/employees/deactivate/${empId}`, { method: 'POST', headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content } })
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
            const isAjax = searchForm.dataset.ajax === 'true';

            // Show loading state
            // No client-side loading state: rely on normal form submission and server response.
            };

        // Close modal
            window.closeDeactivateModal = function () {
                deactivateEmpId = null;
                deactivateModal.classList.add("hidden");
                // Force repaint for Chrome overlay bug
                deactivateModal.offsetHeight;
            };

        // Confirm deactivate
        confirmDeactivateBtn?.addEventListener("click", () => {
            if (!deactivateEmpId) return;

            fetch(`/admin/employees/deactivate/${deactivateEmpId}`, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                }
            })
            .then(res => res.json())
            .then(data => {
                closeDeactivateModal();   // 🔥 MOST IMPORTANT
                if (data.success) {
                    location.reload();
                }
            })
            .catch(err => {
                console.error(err);
                closeDeactivateModal();   // 🔥 EVEN ON ERROR
            });
        });

});
