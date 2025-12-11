document.addEventListener("DOMContentLoaded", function () {

    // =======================
    // ELEMENTS
    // =======================
    const selectAll = document.getElementById("selectAll");
    const globalSearch = document.getElementById("globalSearch");
    const clearSearch = document.getElementById("clearSearch");
    const bulkDeleteBtn = document.getElementById("bulkDeleteBtn");
    const selectedCountEl = document.getElementById("selectedCount");

    function rowCheckboxes() {
        return Array.from(document.querySelectorAll(".rowCheckbox"));
    }


    // =======================
    // UPDATE SELECTED COUNT
    // =======================
    function updateSelectedCount() {
        const count = rowCheckboxes().filter(cb => cb.checked).length;
        selectedCountEl.innerText = count;
        bulkDeleteBtn.disabled = count === 0;
    }


    // =======================
    // SELECT ALL CHECKBOX
    // =======================
    selectAll?.addEventListener("change", (e) => {
        rowCheckboxes().forEach(cb => cb.checked = e.target.checked);
        updateSelectedCount();
    });

    document.addEventListener("change", (e) => {
        if (e.target && e.target.classList.contains("rowCheckbox")) {
            updateSelectedCount();
        }
    });


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
    // BULK DELETE
    // =======================
    bulkDeleteBtn?.addEventListener("click", async () => {

        const ids = rowCheckboxes().filter(c => c.checked).map(c => c.value);

        if (ids.length === 0) return;

        Swal.fire({
            title: "Delete Selected?",
            text: `${ids.length} employees will be permanently deleted.`,
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Yes, delete",
        }).then(async (result) => {

            if (!result.isConfirmed) return;

            try {
                const resp = await fetch("/employees/bulk_delete", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ ids })
                });

                const data = await resp.json();

                if (data.success) {
                    Swal.fire({
                        icon: "success",
                        title: "Deleted!",
                        timer: 1200,
                        showConfirmButton: false
                    });
                    setTimeout(() => location.reload(), 1200);
                }

            } catch (err) {
                Swal.fire("Error", "Could not delete selected employees", "error");
                console.error(err);
            }

        });
    });


    // =======================
    // SINGLE DELETE FUNCTION
    // (Used directly in employees.html)
    // =======================
    window.deleteSingle = function (empId) {

        Swal.fire({
            title: "Confirm Delete",
            text: "Employee will be permanently deleted.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Delete",
        }).then(async (result) => {

            if (!result.isConfirmed) return;

            try {
                const resp = await fetch("/employees/delete/" + empId, {
                    method: "POST"
                });
                const data = await resp.json();

                if (data.success) {
                    Swal.fire({
                        icon: "success",
                        title: "Employee Deleted",
                        timer: 1300,
                        showConfirmButton: false
                    });
                    setTimeout(() => location.reload(), 1300);
                }

            } catch (err) {
                Swal.fire("Error", "Failed to delete employee", "error");
                console.error(err);
            }

        });

    };


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

});
