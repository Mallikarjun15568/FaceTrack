// =====================================
// INITIAL LOAD
// =====================================
// Calendar navigation
let currentCalendarDate = new Date();
let selectedEmployeeId = null;

document.addEventListener("DOMContentLoaded", function() {
    // Attach event listeners
    document.getElementById("applyFilters")?.addEventListener("click", loadTable);
    document.getElementById("exportCsv")?.addEventListener("click", exportCSV);
    document.getElementById("exportPdf")?.addEventListener("click", exportPDF);
    document.getElementById("loadEmployeeData")?.addEventListener("click", loadEmployeeAnalysis);
    
    // Calendar navigation buttons
    document.getElementById("prevMonth")?.addEventListener("click", () => {
        if (selectedEmployeeId) {
            currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
            loadEmployeeCalendar(selectedEmployeeId, currentCalendarDate);
        }
    });
    
    document.getElementById("nextMonth")?.addEventListener("click", () => {
        if (selectedEmployeeId) {
            currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
            loadEmployeeCalendar(selectedEmployeeId, currentCalendarDate);
        }
    });
    
    // Initialize
    initReports();
});

async function initReports() {
    // Check if this is employee view
    const isEmployeeView = window.isEmployeeView || false;
    
    if (isEmployeeView) {
        // Employee view: Auto-load their own data
        await loadEmployeeSelfData();
    } else {
        // Admin/HR view: Load all data
        await loadSummary();
        await loadCharts();
        await loadDepartments();
        await loadEmployees();
        await loadEmployeeDropdown();
        await loadTable();
    }
    
    // Set default month to current
    const now = new Date();
    const monthSelector = document.getElementById("monthSelector");
    if (monthSelector) {
        monthSelector.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    }
}

// Load employee's own data automatically
async function loadEmployeeSelfData() {
    try {
        // Get current employee name from session (passed via backend)
        const response = await fetch('/auth/current-user');
        const userData = await response.json();
        
        if (userData.status === 'ok') {
            const employeeName = userData.full_name;
            const now = new Date();
            const year = now.getFullYear();
            const month = now.getMonth() + 1;
            
            // Update UI with employee name
            const selectedNameEl = document.getElementById("selectedEmployeeName");
            if (selectedNameEl) selectedNameEl.textContent = employeeName;
            
            const selectedMonthEl = document.getElementById("selectedMonth");
            if (selectedMonthEl) selectedMonthEl.textContent = `${year}-${String(month).padStart(2, '0')}`;
            
            // Load their summary and calendar
            await loadEmployeeMonthlySummary(employeeName, year, month);
            
            currentCalendarDate = new Date(year, month - 1, 1);
            selectedEmployeeId = employeeName;
            await loadEmployeeCalendar(employeeName, currentCalendarDate);
            
            // Load their table records
            await loadTable();
        }
    } catch (err) {
        console.error("Failed to load employee data:", err);
    }
}



// =====================================
// SUMMARY API
// =====================================
async function loadSummary() {
    fetch("/reports/api/summary")
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") return;

            const presentCount = document.getElementById("presentCount");
            const absentCount = document.getElementById("absentCount");
            const lateCount = document.getElementById("lateCount");
            const attendancePercent = document.getElementById("attendancePercent");

            if (presentCount) presentCount.textContent = data.summary.present;
            if (absentCount) absentCount.textContent = data.summary.absent;
            if (lateCount) lateCount.textContent = data.summary.late;
            if (attendancePercent) attendancePercent.textContent = data.summary.attendance_percent + "%";
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
// EMPLOYEE DROPDOWN (for analysis)
// =====================================
async function loadEmployeeDropdown() {
    fetch("/reports/api/employees")
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") return;

            const emp = document.getElementById("employeeSelector");
            emp.innerHTML = `<option value="">-- Select Employee --</option>`;

            data.employees.forEach(e => {
                const opt = document.createElement("option");
                opt.value = e.full_name;
                opt.dataset.id = e.id;
                opt.textContent = e.full_name;
                emp.appendChild(opt);
            });
        })
        .catch(err => console.error("Failed to load employees:", err));
}


// =====================================
// LOAD EMPLOYEE ANALYSIS (Summary + Calendar)
// =====================================
async function loadEmployeeAnalysis() {
    const empSelector = document.getElementById("employeeSelector");
    const monthSelector = document.getElementById("monthSelector");
    
    const employeeName = empSelector.value;
    const monthValue = monthSelector.value;
    
    if (!employeeName) {
        alert("Please select an employee");
        return;
    }
    
    if (!monthValue) {
        alert("Please select a month");
        return;
    }
    
    // Get employee ID from selected option
    const selectedOption = empSelector.options[empSelector.selectedIndex];
    selectedEmployeeId = employeeName;
    
    // Parse month
    const [year, month] = monthValue.split('-');
    currentCalendarDate = new Date(year, month - 1, 1);
    
    // Show sections
    document.getElementById("employeeSummarySection").classList.remove("hidden");
    document.getElementById("employeeCalendarSection").classList.remove("hidden");
    
    // Update headers
    document.getElementById("selectedEmployeeName").textContent = employeeName;
    document.getElementById("selectedMonth").textContent = monthValue;
    
    // Load data
    await loadEmployeeMonthlySummary(employeeName, year, month);
    await loadEmployeeCalendar(employeeName, currentCalendarDate);
}


// =====================================
// EMPLOYEE MONTHLY SUMMARY
// =====================================
async function loadEmployeeMonthlySummary(employeeName, year, month) {
    const url = `/attendance/api/monthly-summary?year=${year}&month=${month}&employee_name=${encodeURIComponent(employeeName)}`;
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok") {
                document.getElementById("empPresentDays").textContent = data.present_days || 0;
                document.getElementById("empLeaveDays").textContent = data.leave_days || 0;
                document.getElementById("empAbsentDays").textContent = data.absent_days || 0;
                document.getElementById("empHolidayDays").textContent = data.holiday_days || 0;
                document.getElementById("empTotalHours").textContent = (data.total_hours || 0).toFixed(1) + " hrs";
                
                const total = (data.present_days || 0) + (data.leave_days || 0) + (data.absent_days || 0) + (data.holiday_days || 0);
                document.getElementById("empTotalDays").textContent = total;
            }
        })
        .catch(err => console.error("Failed to load employee summary:", err));
}


// =====================================
// EMPLOYEE CALENDAR
// =====================================
async function loadEmployeeCalendar(employeeName, date) {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;
    
    // Update month display
    const monthNames = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"];
    document.getElementById("calendarMonth").textContent = `${monthNames[date.getMonth()]} ${year}`;
    
    const url = `/attendance/api/calendar?year=${year}&month=${month}&employee_name=${encodeURIComponent(employeeName)}`;
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok") {
                renderEmployeeCalendar(year, month, data.calendar);
            }
        })
        .catch(err => console.error("Failed to load calendar:", err));
}


// =====================================
// RENDER EMPLOYEE CALENDAR
// =====================================
function renderEmployeeCalendar(year, month, calendarData) {
    const grid = document.getElementById("calendarGrid");
    if (!grid) return;
    
    grid.innerHTML = "";
    
    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    
    const map = {};
    calendarData.forEach(d => {
        map[d.date] = d.final_status;
    });
    
    const renderedStatuses = {};
    
    // Empty boxes before month start
    for (let i = 0; i < firstDay; i++) {
        grid.appendChild(document.createElement("div"));
    }
    
    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
        let status = map[dateStr];
        
        // Format date for display
        const date = new Date(year, month - 1, day);
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const formattedDate = `${dayNames[date.getDay()]}, ${monthNames[month-1]} ${day}, ${year}`;
        
        // If no status from API, check if it's a weekend
        if (!status) {
            const dayOfWeek = new Date(year, month - 1, day).getDay();
            if (dayOfWeek === 0 || dayOfWeek === 6) {
                status = "weekend";
            } else {
                status = "none";
            }
        }
        
        let bg = "bg-white border-gray-200";
        let label = "";
        let statusText = "";
        
        if (status === "present" || status === "late") {
            bg = "bg-green-50 border-green-300";
            label = "✓";
            statusText = "Present";
            renderedStatuses["present"] = (renderedStatuses["present"] || 0) + 1;
        } else if (status === "on_leave") {
            bg = "bg-blue-50 border-blue-300";
            label = "L";
            statusText = "On Leave";
            renderedStatuses["on_leave"] = (renderedStatuses["on_leave"] || 0) + 1;
        } else if (status === "absent") {
            bg = "bg-red-50 border-red-300";
            label = "A";
            statusText = "Absent";
            renderedStatuses["absent"] = (renderedStatuses["absent"] || 0) + 1;
        } else if (status === "holiday") {
            bg = "bg-purple-50 border-purple-300";
            label = "H";
            statusText = "Holiday";
            renderedStatuses["holiday"] = (renderedStatuses["holiday"] || 0) + 1;
        } else if (status === "weekend") {
            bg = "bg-gray-100 border-gray-300";
            label = "W";
            statusText = "Weekend";
            renderedStatuses["weekend"] = (renderedStatuses["weekend"] || 0) + 1;
        }
        
        const cell = document.createElement("div");
        cell.className = `
          ${bg}
          rounded-xl border-2
          flex flex-col items-center justify-center
          text-sm font-semibold
          hover:shadow-lg hover:scale-105 transition-all duration-200
          cursor-pointer relative group
        `;
        cell.title = `${formattedDate}${statusText ? ' - ' + statusText : ''}`;
        cell.innerHTML = `
          <div class="text-gray-900 text-base font-bold">${day}</div>
          <div class="text-xs mt-1 font-bold">${label}</div>
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm rounded-xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <div class="text-white text-center px-2">
              <div class="text-xs font-bold">${formattedDate}</div>
              ${statusText ? `<div class="text-[10px] mt-1">${statusText}</div>` : ''}
            </div>
          </div>
        `;
        
        grid.appendChild(cell);
    }
    
    // Render legend with status counts
    console.log("📊 Rendering legend with statuses:", renderedStatuses);
    renderCalendarLegend(renderedStatuses);
}


// =====================================
// CALENDAR LEGEND
// =====================================
function renderCalendarLegend(statusCount) {
    const legend = document.getElementById("calendarLegend");
    if (!legend) {
        console.error("❌ calendarLegend element not found");
        return;
    }
    
    console.log("🎨 Rendering calendar legend with counts:", statusCount);
    legend.innerHTML = "";
    
    const legendConfig = [
        { key: "present", color: "bg-green-500", label: "Present", icon: "✓" },
        { key: "on_leave", color: "bg-blue-500", label: "On Leave", icon: "L" },
        { key: "absent", color: "bg-red-500", label: "Absent", icon: "A" },
        { key: "holiday", color: "bg-purple-500", label: "Holiday", icon: "H" },
        { key: "weekend", color: "bg-gray-400", label: "Weekend", icon: "W" }
    ];
    
    let hasData = false;
    let totalDays = 0;
    
    legendConfig.forEach(config => {
        const count = statusCount[config.key];
        if (count && count > 0) {
            hasData = true;
            totalDays += count;
            const item = document.createElement("div");
            item.className = "flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-all";
            item.innerHTML = `
                <div class="w-5 h-5 rounded-full ${config.color} shadow-sm flex items-center justify-center text-[10px] text-white font-bold">${config.icon}</div>
                <span class="text-xs font-semibold text-gray-700">${config.label}</span>
                <span class="text-xs font-bold text-gray-900 bg-gray-100 px-2 py-0.5 rounded-full">${count}</span>
            `;
            legend.appendChild(item);
        }
    });
    
    if (!hasData) {
        console.warn("⚠️ No legend data to display");
        legend.innerHTML = '<span class="text-xs text-gray-500 italic">No data for this month</span>';
    } else {
        // Add total count
        const totalItem = document.createElement("div");
        totalItem.className = "flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border-2 border-indigo-200 shadow-sm";
        totalItem.innerHTML = `
            <i class="fas fa-calendar-check text-indigo-600 text-sm"></i>
            <span class="text-xs font-bold text-indigo-900">Total: ${totalDays} days</span>
        `;
        legend.appendChild(totalItem);
        console.log("✅ Legend rendered successfully with", totalDays, "total days");
    }
}


// =====================================
// EMPLOYEE DROPDOWN (for table filter)
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
