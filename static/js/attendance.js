// =============================================
//             ATTENDANCE LOGS (FIXED)
// =============================================

document.addEventListener("DOMContentLoaded", () => {

    // Safely load usernames only if dropdown exists
    if (document.getElementById("userFilter")) {
        loadUsernames();
    }

    loadAttendance();

    const applyBtn = document.getElementById("applyFilters");
    if (applyBtn) applyBtn.addEventListener("click", loadAttendance);

    const userFilter = document.getElementById("userFilter");
    if (userFilter) userFilter.addEventListener("change", loadAttendance);

    const dateFilter = document.getElementById("dateFilter");
    if (dateFilter) dateFilter.addEventListener("change", loadAttendance);

    const exportBtn = document.getElementById("exportCSV");
    if (exportBtn) exportBtn.addEventListener("click", exportToCSV);
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
        tr.className = "border-b hover:bg-gray-50 transition";

        const photo = r.photo || "/static/default_user.png";
        const snapshot = r.snapshot || "/static/default_snapshot.png";

        let statusBadge = `<span class="px-2 py-1 text-xs rounded bg-gray-200 text-gray-700">-</span>`;
        if (r.status === "present") statusBadge = `<span class="px-2 py-1 text-xs rounded bg-green-100 text-green-700">Present</span>`;
        else if (r.status === "late") statusBadge = `<span class="px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-700">Late</span>`;
        else if (r.status === "early_leave") statusBadge = `<span class="px-2 py-1 text-xs rounded bg-red-100 text-red-700">Early Leave</span>`;
        else if (r.status === "check-in") statusBadge = `<span class="px-2 py-1 text-xs rounded bg-sky-100 text-sky-700">Check-in</span>`;
        else if (r.status === "check-out") statusBadge = `<span class="px-2 py-1 text-xs rounded bg-green-100 text-green-700">Check-out</span>`;
        else if (r.status === "already") statusBadge = `<span class="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">Already marked</span>`;

        tr.innerHTML = `
            <td class="p-3">
                <img src="${photo}" class="w-10 h-10 rounded-full object-cover border shadow-sm">
            </td>
            <td class="p-3 font-medium">${r.name}</td>
            <td class="p-3">
                <img src="${snapshot}" class="w-12 h-12 rounded-lg object-cover border shadow cursor-pointer"
                     onclick="openSnapshotModal('${snapshot}')">
            </td>
            <td class="p-3">${r.check_in_time || "-"}</td>
            <td class="p-3">${r.check_out_time || "-"}</td>
            <td class="p-3">${r.working_hours || "-"}</td>
            <td class="p-3">${statusBadge}</td>
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
