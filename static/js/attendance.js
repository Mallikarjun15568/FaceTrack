// =============================================
//             ATTENDANCE LOGS (FIXED)
// =============================================

// Calendar variables (global scope)
let calendarOpen = false;
let currentCalendarDate = new Date();

document.addEventListener("DOMContentLoaded", () => {

    // Safely load usernames only if dropdown exists
    if (document.getElementById("userFilter")) {
        loadUsernames();
    }

    loadAttendance();
    // Load current month summary on page load
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1;
    
    let userFilter = document.getElementById("userFilter");
    const employeeName = userFilter && userFilter.value ? userFilter.value : "";
    
    let summaryUrl = `/attendance/api/monthly-summary?year=${year}&month=${month}`;
    if (employeeName) {
        summaryUrl += `&employee_name=${encodeURIComponent(employeeName)}`;
    }
    
    fetch(summaryUrl)
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok") {
                updateSummaryCards(data);
            }
        })
        .catch(err => console.error("Failed to load initial summary:", err));

    const applyBtn = document.getElementById("applyFilters");
    if (applyBtn) {
        applyBtn.addEventListener("click", () => {
            loadAttendance();
            loadMonthlySummary(); // Refresh summary when filters applied
            // Refresh calendar if it's open
            const calendarContent = document.getElementById("calendarContent");
            if (calendarContent && !calendarContent.classList.contains("hidden")) {
                loadCalendar(new Date(currentCalendarDate));
            }
        });
    }

    // Reuse userFilter variable instead of re-declaring
    if (userFilter) {
        userFilter.addEventListener("change", () => {
            loadAttendance();
            loadMonthlySummary(); // Refresh summary when user changes
            // Refresh calendar if it's open
            const calendarContent = document.getElementById("calendarContent");
            if (calendarContent && !calendarContent.classList.contains("hidden")) {
                loadCalendar(new Date(currentCalendarDate));
            }
        });
    }

    const dateFilter = document.getElementById("dateFilter");
    if (dateFilter) dateFilter.addEventListener("change", loadAttendance);

    const exportBtn = document.getElementById("exportCSV");
    if (exportBtn) exportBtn.addEventListener("click", exportToCSV);

    const resetBtn = document.getElementById("resetFilters");
    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            if (userFilter) userFilter.value = "";
            if (dateFilter) dateFilter.value = "";
            loadAttendance();
            loadMonthlySummary();
            // Refresh calendar if it's open
            const calendarContent = document.getElementById("calendarContent");
            if (calendarContent && !calendarContent.classList.contains("hidden")) {
                loadCalendar(new Date(currentCalendarDate));
            }
        });
    }

    // Calendar toggle
    const toggleCalendarBtn = document.getElementById("toggleCalendar");
    const calendarContent = document.getElementById("calendarContent");
    const calendarBtnText = document.getElementById("calendarBtnText");
    const calendarIcon = document.getElementById("calendarIcon");

    if (toggleCalendarBtn) {
        toggleCalendarBtn.addEventListener("click", () => {
            calendarOpen = !calendarOpen;
            if (calendarOpen) {
                calendarContent.classList.remove("hidden");
                calendarContent.classList.add("animate-fadeIn");
                calendarBtnText.textContent = "Hide Calendar";
                if (calendarIcon) calendarIcon.className = "fas fa-calendar-minus";
                loadCalendar(currentCalendarDate); // Load when opening
            } else {
                calendarContent.classList.add("hidden");
                calendarContent.classList.remove("animate-fadeIn");
                calendarBtnText.textContent = "Show Calendar";
                if (calendarIcon) calendarIcon.className = "fas fa-calendar-plus";
            }
        });
    }

    // Calendar navigation
    const prevMonthBtn = document.getElementById("prevMonth");
    const nextMonthBtn = document.getElementById("nextMonth");
    if (prevMonthBtn) {
        prevMonthBtn.addEventListener("click", () => {
            currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
            loadCalendar(new Date(currentCalendarDate));
        });
    }
    if (nextMonthBtn) {
        nextMonthBtn.addEventListener("click", () => {
            currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
            loadCalendar(new Date(currentCalendarDate));
        });
    }
});


// =============================================
//   LOAD DISTINCT USERNAMES (ADMIN / HR ONLY)
// =============================================
function loadUsernames() {
    const userFilter = document.getElementById("userFilter");
    if (!userFilter) return;

    fetch("/attendance/api/usernames")
        .then(res => res.json())
        .then(data => {
            userFilter.innerHTML = `<option value="">All</option>`;

            if (data.status !== "ok") return;

            data.users.forEach(user => {
                const opt = document.createElement("option");
                opt.value = user.full_name;
                opt.textContent = user.full_name;
                userFilter.appendChild(opt);
            });
        })
        .catch(err => console.error("Failed to load usernames:", err));
}


// =============================================
//   LOAD ATTENDANCE WITH FILTERS (ROLE SAFE)
// =============================================
function loadAttendance() {

    const userFilter = document.getElementById("userFilter");
    const dateFilter = document.getElementById("dateFilter");

    const user = userFilter ? userFilter.value : "";
    const date = dateFilter ? dateFilter.value : "";

    let url = "/attendance/api/attendance";
    const params = [];

    if (user) params.push(`user=${encodeURIComponent(user)}`);
    if (date) params.push(`date=${encodeURIComponent(date)}`);

    if (params.length > 0) url += "?" + params.join("&");

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") return;
            renderAttendance(data.records);
        })
        .catch(err => console.error("Failed to load attendance:", err));
}


// =============================================
//        RENDER ATTENDANCE TABLE
// =============================================
function renderAttendance(records) {
    const tbody = document.getElementById("attendanceTableBody");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!records || records.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="p-4 text-center text-gray-500">
                    No attendance records found.
                </td>
            </tr>
        `;
        return;
    }

    records.forEach(r => {
        const tr = document.createElement("tr");
        tr.className = "border-b border-gray-100 hover:bg-gray-50 transition";

        const photo = r.photo || "/static/default_user.png";
        const snapshot = r.snapshot || "/static/default_snapshot.png";

        // Format date-time split
        const formatDateTime = (datetime) => {
            if (!datetime || datetime === "-") return "<span class='text-gray-400'>-</span>";
            try {
                const date = new Date(datetime);
                const dateStr = date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
                const timeStr = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });
                return `<div class='text-sm'><div class='font-medium text-gray-900'>${dateStr}</div><div class='text-gray-500 text-xs mt-0.5'>${timeStr}</div></div>`;
            } catch {
                return datetime;
            }
        };

        // Format working hours
        const formatWorkingHours = (hours) => {
            if (!hours || hours === "-") return "<span class='text-gray-400'>-</span>";
            const h = parseFloat(hours);
            if (isNaN(h)) return hours;
            
            if (h >= 1) {
                return `<span class='text-sm text-gray-900'>${h.toFixed(2)} hrs</span>`;
            } else {
                const minutes = Math.round(h * 60);
                return `<span class='text-sm text-gray-900'>${minutes} min</span>`;
            }
        };

        // Soft color status badges with consistent size - right aligned
        let statusBadge = `<span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-600 min-w-[90px] text-center">-</span>`;
        if (r.status === "present") statusBadge = `<span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-green-50 text-green-600 min-w-[90px] text-center">Present</span>`;
        else if (r.status === "late") statusBadge = `<span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-amber-50 text-amber-600 min-w-[90px] text-center">Late</span>`;
        else if (r.status === "early_leave") statusBadge = `<span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-rose-50 text-rose-600 min-w-[90px] text-center">Early Leave</span>`;
        else if (r.status === "check-in") statusBadge = `<span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-sky-50 text-sky-600 min-w-[90px] text-center">Check-in</span>`;
        else if (r.status === "check-out") statusBadge = `<span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-emerald-50 text-emerald-600 min-w-[90px] text-center">Check-out</span>`;
        else if (r.status === "already") statusBadge = `<span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-slate-50 text-slate-600 min-w-[90px] text-center">Marked</span>`;
        else if (r.status === "on_leave") statusBadge = `<span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-blue-50 text-blue-600 min-w-[90px] text-center">On Leave</span>`;
        else if (r.status === "holiday") statusBadge = `<span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-purple-50 text-purple-600 min-w-[90px] text-center">Holiday</span>`;
        else if (r.status === "absent") statusBadge = `<span class="inline-block px-3 py-1 text-xs font-medium rounded-full bg-red-50 text-red-600 min-w-[90px] text-center">Absent</span>`;

        tr.innerHTML = `
            <td class="py-3 px-4">
                <img src="${photo}" class="w-10 h-10 rounded-full object-cover border-2 border-gray-100 shadow-sm">
            </td>
            <td class="py-3 px-4">
                <div class="font-semibold text-gray-900 text-sm">${r.name}</div>
            </td>
            <td class="py-3 px-4">
                <img src="${snapshot}" class="w-12 h-12 rounded-lg object-cover border border-gray-200 shadow-sm cursor-pointer hover:scale-105 transition-transform"
                     onclick="openSnapshotModal('${snapshot}')">
            </td>
            <td class="py-3 px-4">${formatDateTime(r.check_in_time)}</td>
            <td class="py-3 px-4">${formatDateTime(r.check_out_time)}</td>
            <td class="py-3 px-4">${formatWorkingHours(r.working_hours)}</td>
            <td class="py-3 px-4 text-right">${statusBadge}</td>
        `;

        tbody.appendChild(tr);
    });
}


// =============================================
//          EXPORT CSV (ADMIN / HR ONLY)
// =============================================
function exportToCSV() {

    const userFilter = document.getElementById("userFilter");
    const dateFilter = document.getElementById("dateFilter");

    const user = userFilter ? userFilter.value : "";
    const date = dateFilter ? dateFilter.value : "";

    let url = "/attendance/api/attendance";
    const params = [];

    if (user) params.push(`user=${encodeURIComponent(user)}`);
    if (date) params.push(`date=${encodeURIComponent(date)}`);

    if (params.length > 0) url += "?" + params.join("&");

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok" || !data.records || data.records.length === 0) {
                alert("No records to export");
                return;
            }

            let csv = "Name,Check-In,Check-Out,Working Hours,Status,Date\n";
            data.records.forEach(r => {
                csv += `${r.name},${r.check_in_time || ""},${r.check_out_time || ""},${r.working_hours || ""},${r.status},${r.date}\n`;
            });

            const blob = new Blob([csv], { type: "text/csv" });
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = "attendance_filtered.csv";
            link.click();
        });
}


// =============================================
//   MONTHLY SUMMARY
// =============================================
function loadMonthlySummary() {
    // Get selected user if admin/hr
    let url = "/attendance/api/monthly-summary";
    const userFilter = document.getElementById("userFilter");
    if (userFilter && userFilter.value) {
        url += `?employee_name=${encodeURIComponent(userFilter.value)}`;
    }

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok") {
                document.getElementById("presentDays").textContent = data.present_days || 0;
                document.getElementById("leaveDays").textContent = data.leave_days || 0;
                document.getElementById("absentDays").textContent = data.absent_days || 0;
                document.getElementById("holidayDays").textContent = data.holiday_days || 0;
                document.getElementById("totalHours").textContent = (data.total_hours || 0).toFixed(1) + " hrs";
                
                // Calculate total days (present + leave + absent + holiday)
                const total = (data.present_days || 0) + (data.leave_days || 0) + (data.absent_days || 0) + (data.holiday_days || 0);
                document.getElementById("totalDays").textContent = total;
            }
        })
        .catch(err => console.error("Failed to load monthly summary:", err));
}


// =============================================
//   UPDATE SUMMARY CARDS
// =============================================
function updateSummaryCards(data) {
    document.getElementById("presentDays").textContent = data.present_days || 0;
    document.getElementById("leaveDays").textContent = data.leave_days || 0;
    document.getElementById("absentDays").textContent = data.absent_days || 0;
    document.getElementById("holidayDays").textContent = data.holiday_days || 0;
    document.getElementById("totalHours").textContent = (data.total_hours || 0).toFixed(1) + " hrs";
    
    const total = (data.present_days || 0) + (data.leave_days || 0) + (data.absent_days || 0) + (data.holiday_days || 0);
    document.getElementById("totalDays").textContent = total;
}

// =============================================
//   MONTHLY CALENDAR
// =============================================
function loadCalendar(date) {
    const year = date.getFullYear();
    const month = date.getMonth() + 1;

    // Update month display
    const monthNames = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"];
    document.getElementById("calendarMonth").textContent = `${monthNames[date.getMonth()]} ${year}`;

    // Get selected user if admin/hr
    const userFilter = document.getElementById("userFilter");
    const employeeName = userFilter && userFilter.value ? userFilter.value : "";
    
    let calendarUrl = `/attendance/api/calendar?year=${year}&month=${month}`;
    let summaryUrl = `/attendance/api/monthly-summary?year=${year}&month=${month}`;
    
    if (employeeName) {
        calendarUrl += `&employee_name=${encodeURIComponent(employeeName)}`;
        summaryUrl += `&employee_name=${encodeURIComponent(employeeName)}`;
    }

    // Fetch both calendar and summary data
    Promise.all([
        fetch(calendarUrl).then(res => res.json()),
        fetch(summaryUrl).then(res => res.json())
    ])
    .then(([calendarData, summaryData]) => {
        console.log('📅 Calendar API Response:', calendarData);
        console.log('📊 Summary API Response:', summaryData);
        console.log('📅 Calendar array length:', calendarData.calendar ? calendarData.calendar.length : 'undefined');
        console.log('📊 Summary data:', {
            present: summaryData.present_days,
            leave: summaryData.leave_days,
            absent: summaryData.absent_days,
            holiday: summaryData.holiday_days
        });
        
        if (calendarData.status === "ok") {
            renderCalendar(year, month, calendarData.calendar);
        }
        if (summaryData.status === "ok") {
            updateSummaryCards(summaryData);
        }
    })
    .catch(err => console.error("Failed to load calendar data:", err));
}

function renderCalendar(year, month, calendarData) {
    const grid = document.getElementById("calendarGrid");
    if (!grid) {
        console.error('Calendar grid element not found!');
        return;
    }
    grid.innerHTML = "";
    
    console.log('🔥 RENDERING CALENDAR - Year:', year, 'Month:', month);
    console.log('🔥 Calendar Data received:', calendarData);

    const firstDay = new Date(year, month - 1, 1).getDay();
    const daysInMonth = new Date(year, month, 0).getDate();

    const map = {};
    calendarData.forEach(d => {
        map[d.date] = d.final_status;
    });
    
    console.log('Calendar Data Map:', map);
    console.log('Days in month:', daysInMonth);

    // Track what's actually rendered
    const renderedStatuses = {};

    // Empty boxes before month start
    for (let i = 0; i < firstDay; i++) {
        grid.appendChild(document.createElement("div"));
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
        let status = map[dateStr];
        
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

        if (status === "present" || status === "late") {
            bg = "bg-green-50 border-green-300";
            label = "✓";
            renderedStatuses["present"] = (renderedStatuses["present"] || 0) + 1;
        } else if (status === "on_leave") {
            bg = "bg-blue-50 border-blue-300";
            label = "L";
            renderedStatuses["on_leave"] = (renderedStatuses["on_leave"] || 0) + 1;
        } else if (status === "absent") {
            bg = "bg-red-50 border-red-300";
            label = "A";
            renderedStatuses["absent"] = (renderedStatuses["absent"] || 0) + 1;
        } else if (status === "holiday") {
            bg = "bg-purple-50 border-purple-300";
            label = "H";
            renderedStatuses["holiday"] = (renderedStatuses["holiday"] || 0) + 1;
        } else if (status === "weekend") {
            bg = "bg-gray-100 border-gray-300";
            label = "W";
            renderedStatuses["weekend"] = (renderedStatuses["weekend"] || 0) + 1;
        }

        const cell = document.createElement("div");
        cell.className = `
          ${bg}
          rounded-xl border
          flex flex-col items-center justify-center
          text-sm font-semibold
          hover:shadow-md transition
        `;
        cell.innerHTML = `
          <div class="text-gray-900">${day}</div>
          <div class="text-xs mt-1">${label}</div>
        `;

        grid.appendChild(cell);
    }

    // Render dynamic legend with actual rendered statuses
    renderLegend(renderedStatuses);
}

function renderLegend(statusCount) {
    const legend = document.getElementById("calendarLegend");
    if (!legend) return;
    
    legend.innerHTML = "";

    const legendConfig = [
        { key: "present", color: "bg-green-500", label: "Present", icon: "✓" },
        { key: "on_leave", color: "bg-blue-500", label: "On Leave", icon: "L" },
        { key: "absent", color: "bg-red-500", label: "Absent", icon: "A" },
        { key: "holiday", color: "bg-purple-500", label: "Holiday", icon: "H" },
        { key: "weekend", color: "bg-gray-400", label: "Weekend", icon: "W" }
    ];

    let hasData = false;
    legendConfig.forEach(config => {
        const count = statusCount[config.key];
        if (count && count > 0) {
            hasData = true;
            const item = document.createElement("div");
            item.className = "flex items-center gap-2";
            item.innerHTML = `
                <div class="w-4 h-4 rounded-full ${config.color} shadow-sm flex items-center justify-center text-[8px] text-white font-bold">${config.icon}</div>
                <span class="text-xs font-medium text-gray-700">${config.label} <span class="font-bold">(${count})</span></span>
            `;
            legend.appendChild(item);
        }
    });

    if (!hasData) {
        legend.innerHTML = '<span class="text-xs text-gray-500 italic">No data for this month</span>';
    }
}


// =============================================
//   SNAPSHOT MODAL
// =============================================
function openSnapshotModal(src) {
    const modal = document.createElement("div");
    modal.className = "fixed inset-0 bg-black/70 flex justify-center items-center z-50";

    modal.innerHTML = `
        <div class="bg-white p-4 rounded shadow-xl">
            <img src="${src}" class="w-80 h-80 object-cover rounded mb-4">
            <button onclick="this.closest('.fixed').remove()" 
                class="bg-red-600 text-white px-4 py-2 rounded">
                Close
            </button>
        </div>
    `;

    document.body.appendChild(modal);
}
