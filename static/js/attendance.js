// =============================================
//             ATTENDANCE LOGS (CLEAN)
// =============================================

document.addEventListener("DOMContentLoaded", () => {

    // Safely load usernames only if dropdown exists
    if (document.getElementById("userFilter")) {
        loadUsernames();
    }

    loadAttendance();

    const applyBtn = document.getElementById("applyFilters");
    if (applyBtn) {
        applyBtn.addEventListener("click", loadAttendance);
    }

    const userFilter = document.getElementById("userFilter");
    if (userFilter) {
        userFilter.addEventListener("change", loadAttendance);
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

        // Format date-time split (MySQL datetime string - no timezone conversion)
        const formatDateTime = (datetime) => {
            if (!datetime || datetime === "-") return "<span class='text-gray-400'>-</span>";
            try {
                // MySQL returns datetime in format: "2026-01-03 22:16:14"
                // Parse manually to avoid timezone conversion issues
                const parts = datetime.split(' ');
                if (parts.length !== 2) return datetime;
                
                const dateParts = parts[0].split('-');  // [2026, 01, 03]
                const timeParts = parts[1].split(':');  // [22, 16, 14]
                
                if (dateParts.length !== 3 || timeParts.length !== 3) return datetime;
                
                const year = parseInt(dateParts[0]);
                const month = parseInt(dateParts[1]);
                const day = parseInt(dateParts[2]);
                const hour = parseInt(timeParts[0]);
                const minute = parseInt(timeParts[1]);
                
                // Month names
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                
                // Create date to get day of week
                const date = new Date(year, month - 1, day);
                const dayName = dayNames[date.getDay()];
                
                // Format: "Sat, 03 Jan 2026" (top line)
                const dateStr = `${dayName}, ${day.toString().padStart(2, '0')} ${monthNames[month - 1]} ${year}`;
                
                // Format: "22:16" (bottom line)
                const timeStr = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
                
                return `<div class='text-sm'><div class='font-medium text-gray-900'>${dateStr}</div><div class='text-gray-500 text-xs mt-0.5'>${timeStr}</div></div>`;
            } catch (e) {
                console.error('Date parse error:', e, datetime);
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
