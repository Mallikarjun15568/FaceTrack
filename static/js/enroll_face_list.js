function applyFilters() {
    let deptFilter = document.getElementById("departmentFilter").value;
    let enrollFilter = document.getElementById("enrollFilter").value;
    let search = document.getElementById("search").value.toLowerCase();

    let rows = document.querySelectorAll("#tableRows tr");

    rows.forEach(row => {
        let name = row.children[2].innerText.toLowerCase();
        let dept = row.children[3].innerText;
        let status = row.children[4].innerText.trim();

        let show = true;

        if (deptFilter !== "All" && dept !== deptFilter) show = false;
        if (enrollFilter !== "All" && status !== enrollFilter) show = false;
        if (search && !name.includes(search)) show = false;

        row.style.display = show ? "" : "none";
    });
}

function resetFilters() {
    document.getElementById("departmentFilter").value = "All";
    document.getElementById("enrollFilter").value = "All";
    document.getElementById("search").value = "";

    applyFilters();
}

// Button listeners
document.getElementById("applyBtn").addEventListener("click", applyFilters);
document.getElementById("resetBtn").addEventListener("click", resetFilters);
