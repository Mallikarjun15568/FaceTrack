// ================================
// WEEKLY ATTENDANCE CHART
// ================================

let weeklyData = window.WEEKLY_DATA || { labels: [], data: [] };

const weeklyLabels = Array.isArray(weeklyData.labels) ? weeklyData.labels : [];
const weeklyCounts = Array.isArray(weeklyData.data) ? weeklyData.data : [];

const weeklyCtx = document.getElementById("weeklyAttendanceChart");

if (weeklyCtx && typeof Chart !== "undefined" && weeklyLabels.length > 0) {
    new Chart(weeklyCtx, {
        type: "line",
        data: {
            labels: weeklyLabels,
            datasets: [{
                label: "Attendance",
                data: weeklyCounts,
                borderWidth: 3,
                borderColor: "#2563eb",
                backgroundColor: "rgba(37,99,235,0.2)",
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}



// ================================
// DEPARTMENT EMPLOYEE CHART
// ================================

let departmentData = window.DEPARTMENT_DATA || { labels: [], data: [] };

const deptLabels = Array.isArray(departmentData.labels) ? departmentData.labels : [];
const deptCounts = Array.isArray(departmentData.data) ? departmentData.data : [];

const deptCtx = document.getElementById("departmentChart");

if (deptCtx && typeof Chart !== "undefined" && deptLabels.length > 0) {
    new Chart(deptCtx, {
        type: "bar",
        data: {
            labels: deptLabels,
            datasets: [{
                label: "Employees",
                data: deptCounts,
                backgroundColor: "rgba(16,185,129,0.4)",
                borderColor: "#10b981",
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}




// ================================
// SIDEBAR TOGGLE (MOBILE FRIENDLY)
// ================================

document.getElementById("btnSidebarToggle")?.addEventListener("click", () => {
    const sidebar = document.getElementById("sidebar");
    if (sidebar) sidebar.classList.toggle("hidden");
});




// ================================
// CONFIRMATION HANDLER
// ================================

document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-confirm]");
    if (el) {
        const msg = el.getAttribute("data-confirm");
        if (!confirm(msg)) e.preventDefault();
    }
});
