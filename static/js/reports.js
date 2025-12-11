// =====================================
// INITIAL LOAD
// =====================================
document.addEventListener("DOMContentLoaded", initReports);
document.getElementById("applyFilters").addEventListener("click", loadTable);
document.getElementById("exportCsv").addEventListener("click", exportCSV);
document.getElementById("exportPdf").addEventListener("click", exportPDF);

async function initReports() {
    await loadSummary();
    await loadCharts();
    await loadDepartments();
    await loadEmployees();
    await loadTable();
}



// =====================================
// SUMMARY API
// =====================================
async function loadSummary() {
    fetch("/reports/api/summary")
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") return;

            document.getElementById("presentCount").textContent = data.summary.present;
            document.getElementById("absentCount").textContent  = data.summary.absent;
            document.getElementById("lateCount").textContent    = data.summary.late;

            document.getElementById("attendancePercent").textContent =
                data.summary.attendance_percent + "%";
        })
        .catch(err => console.error("Summary load error:", err));
}



// =====================================
// CHART DATA
// =====================================
let lineChartRef = null;
let barChartRef = null;

async function loadCharts() {
    fetch("/reports/api/chart-data")
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") return;

            renderLineChart(data.chart.daily);
            renderBarChart(data.chart.departments);
        })
        .catch(err => console.error("Chart load error:", err));
}



// =====================================
// LINE CHART (DAILY ATTENDANCE)
// =====================================
function renderLineChart(chartData) {
    if (!chartData || chartData.length === 0) return;

    const ctx = document.getElementById("lineChart").getContext("2d");

    if (lineChartRef) lineChartRef.destroy();

    const labels  = chartData.map(d => d.date);
    const present = chartData.map(d => d.present);
    const absent  = chartData.map(d => d.absent);
    const late    = chartData.map(d => d.late);

    lineChartRef = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Present",
                    data: present,
                    borderColor: "#2563eb",
                    backgroundColor: "rgba(37, 99, 235, 0.15)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35
                },
                {
                    label: "Absent",
                    data: absent,
                    borderColor: "#ef4444",
                    backgroundColor: "rgba(239, 68, 68, 0.15)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35
                },
                {
                    label: "Late",
                    data: late,
                    borderColor: "#eab308",
                    backgroundColor: "rgba(234, 179, 8, 0.15)",
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35
                }
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true } }
        }
    });
}



// =====================================
// BAR CHART (DEPARTMENT-WISE)
// =====================================
function renderBarChart(chartData) {
    if (!chartData || chartData.length === 0) return;

    const ctx = document.getElementById("barChart").getContext("2d");

    if (barChartRef) barChartRef.destroy();

    const labels  = chartData.map(d => d.department);
    const present = chartData.map(d => d.present);

    barChartRef = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Present Count",
                    data: present,
                    backgroundColor: "#10b981",
                    borderColor: "#059669",
                    borderWidth: 1,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true } }
        }
    });
}



// =====================================
// DEPARTMENT DROPDOWN
// =====================================
async function loadDepartments() {
    fetch("/reports/api/departments")
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") return;

            const dept = document.getElementById("departmentFilter");
            dept.innerHTML = `<option value="">All</option>`;

            data.departments.forEach(d => {
                const opt = document.createElement("option");
                opt.value = d.name;
                opt.textContent = d.name;
                dept.appendChild(opt);
            });
        })
        .catch(err => console.error("Failed to load departments:", err));
}



// =====================================
// EMPLOYEE DROPDOWN
// =====================================
async function loadEmployees() {
    fetch("/reports/api/employees")
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") return;

            const emp = document.getElementById("employeeFilter");
            emp.innerHTML = `<option value="">All</option>`;

            data.employees.forEach(e => {
                const opt = document.createElement("option");
                opt.value = e.full_name;
                opt.textContent = e.full_name;
                emp.appendChild(opt);
            });
        })
        .catch(err => console.error("Failed to load employees:", err));
}



// =====================================
// TABLE API (FILTERS)
// =====================================
async function loadTable() {
    const from = document.getElementById("fromDate").value;
    const to   = document.getElementById("toDate").value;
    const user = document.getElementById("employeeFilter").value;
    const dept = document.getElementById("departmentFilter").value;

    let url = "/reports/api/table?";

    if (from) url += `from=${encodeURIComponent(from)}&`;
    if (to)   url += `to=${encodeURIComponent(to)}&`;
    if (user) url += `user=${encodeURIComponent(user)}&`;
    if (dept) url += `department=${encodeURIComponent(dept)}&`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") return;
            renderTable(data.records);
        })
        .catch(err => console.error("Table load error:", err));
}



// =====================================
// TABLE RENDER
// =====================================
function renderTable(records) {
    const tbody = document.getElementById("tableBody");
    tbody.innerHTML = "";

    if (!records || records.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-gray-600">No records found.</td></tr>`;
        return;
    }

    records.forEach(r => {
        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td class="p-2">${r.date}</td>
            <td class="p-2">${r.name}</td>
            <td class="p-2">${r.department}</td>
            <td class="p-2">${r.status}</td>
            <td class="p-2">${r.entry_time || "-"}</td>
            <td class="p-2">
                ${r.snapshot ? `<img src="${r.snapshot}" class="w-12 h-12 rounded-lg border shadow-sm">` : "-"}
            </td>
        `;

        tbody.appendChild(tr);
    });
}



// =====================================
// EXPORT CSV
// =====================================
function exportCSV() {
    const from = document.getElementById("fromDate").value;
    const to   = document.getElementById("toDate").value;
    const user = document.getElementById("employeeFilter").value;
    const dept = document.getElementById("departmentFilter").value;

    let url = "/reports/api/export/csv?";

    if (from) url += `from=${encodeURIComponent(from)}&`;
    if (to)   url += `to=${encodeURIComponent(to)}&`;
    if (user) url += `user=${encodeURIComponent(user)}&`;
    if (dept) url += `department=${encodeURIComponent(dept)}&`;

    window.location.href = url;
}



// =====================================
// EXPORT PDF
// =====================================
function exportPDF() {
    const from = document.getElementById("fromDate").value;
    const to   = document.getElementById("toDate").value;
    const user = document.getElementById("employeeFilter").value;
    const dept = document.getElementById("departmentFilter").value;

    let url = "/reports/api/export/pdf?";

    if (from) url += `from=${encodeURIComponent(from)}&`;
    if (to)   url += `to=${encodeURIComponent(to)}&`;
    if (user) url += `user=${encodeURIComponent(user)}&`;
    if (dept) url += `department=${encodeURIComponent(dept)}&`;

    window.open(url, "_blank");
}
