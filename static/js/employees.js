        // =======================
        // ACTIVATE EMPLOYEE LOGIC
        // =======================
        window.activateEmployee = function (empId) {
            fetch(`/employees/activate/${empId}`, {
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
document.addEventListener("DOMContentLoaded", function () {

    // =======================
    // ELEMENTS
    // =======================
    const globalSearch = document.getElementById("globalSearch");
    const clearSearch = document.getElementById("clearSearch");


    // =======================
    // UPDATE SELECTED COUNT
    // =======================
    // Bulk delete and selected count logic removed


    // =======================
    // SELECT ALL CHECKBOX
    // =======================
    // Select all and row checkbox logic removed


    // =======================
    // GLOBAL SEARCH
    // =======================
    globalSearch?.addEventListener("input", () => {
        const q = globalSearch.value.toLowerCase().trim();

        document.querySelectorAll("#employeesTbody tr").forEach(row => {
            const text = row.innerText.toLowerCase();
            row.style.display = text.includes(q) ? "" : "none";
        });
    });

    clearSearch?.addEventListener("click", () => {
        globalSearch.value = "";
        document.querySelector("#globalSearch").dispatchEvent(new Event("input"));
    });


    // =======================
    // Bulk delete and single delete logic removed


    // =======================
    // FILTER APPLY / RESET
    // =======================
    document.getElementById("applyFilters")?.addEventListener("click", () => {
        const params = new URLSearchParams(window.location.search);

        const dept = document.getElementById("filterDept")?.value || "";
        const enroll = document.getElementById("filterEnroll")?.value || "";
        const sort = document.getElementById("sortBy")?.value || "";

        if (dept) params.set("department_id", dept); else params.delete("department_id");
        if (enroll) params.set("enrolled", enroll); else params.delete("enrolled");
        if (sort) params.set("sort", sort); else params.delete("sort");

        params.set("page", "1");

        window.location.search = params.toString();
    });

    document.getElementById("resetFilters")?.addEventListener("click", () => {
        window.location.search = "";
    });


        // =======================
        // DEACTIVATE MODAL LOGIC
        // =======================
        let deactivateEmpId = null;
        const deactivateModal = document.getElementById("deactivateModal");
        const confirmDeactivateBtn = document.getElementById("confirmDeactivateBtn");
        // CSRF token
        const csrfToken = document
            .querySelector('meta[name="csrf-token"]')
            ?.getAttribute("content");

        // Open modal (called from button)
            window.openDeactivateModal = function (empId) {
                deactivateEmpId = empId;
                deactivateModal.classList.remove("hidden");
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

            fetch(`/employees/deactivate/${deactivateEmpId}`, {
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
