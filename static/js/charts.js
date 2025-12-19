// ============================================
// FaceTrack Pro - Advanced Charts Module (PHASE 1)
// ============================================

class FaceTrackCharts {
    constructor() {
        this.charts = {};
        this.colors = {
            primary: '#3b82f6',
            success: '#10b981',
            warning: '#f59e0b',
            danger: '#ef4444',
            info: '#06b6d4',
            purple: '#8b5cf6'
        };
    }

    destroy(id) {
        if (this.charts[id]) {
            this.charts[id].destroy();
        }
    }

    // 1️⃣ TODAY ATTENDANCE (DONUT)
    renderTodayAttendance(id, d) {
        const ctx = document.getElementById(id);
        if (!ctx) return;
        this.destroy(id);

        this.charts[id] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Present', 'Absent', 'Late', 'On Leave'],
                datasets: [{
                    data: [d.present, d.absent, d.late, d.onLeave],
                    backgroundColor: [
                        this.colors.success,
                        this.colors.danger,
                        this.colors.warning,
                        this.colors.purple
                    ],
                    borderWidth: 2
                }]
            },
            options: { responsive: true }
        });
    }

    // 2️⃣ DEPARTMENT WISE BAR
    renderDepartmentChart(id, rows) {
        const ctx = document.getElementById(id);
        if (!ctx) return;
        this.destroy(id);

        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: rows.map(r => r.department),
                datasets: [{
                    label: 'Present',
                    data: rows.map(r => r.present),
                    backgroundColor: this.colors.success
                }]
            },
            options: { responsive: true }
        });
    }

    // 3️⃣ WORKING HOURS PIE
    renderWorkingHours(id, d) {
        const ctx = document.getElementById(id);
        if (!ctx) return;
        this.destroy(id);

        this.charts[id] = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['<4 hrs', '4–6 hrs', '6–8 hrs', '8+ hrs'],
                datasets: [{
                    data: [
                        d.lessThan4,
                        d.between4And6,
                        d.between6And8,
                        d.moreThan8
                    ],
                    backgroundColor: [
                        this.colors.danger,
                        this.colors.warning,
                        this.colors.success,
                        this.colors.info
                    ]
                }]
            },
            options: { responsive: true }
        });
    }

    // 4️⃣ WEEKLY TREND
    renderWeeklyTrend(id, d) {
        const ctx = document.getElementById(id);
        if (!ctx) return;
        this.destroy(id);

        this.charts[id] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: d.labels,
                datasets: [{
                    label: 'Present',
                    data: d.present,
                    borderColor: this.colors.success,
                    fill: false,
                    tension: 0.4
                }]
            },
            options: { responsive: true }
        });
    }

    // 5️⃣ MONTHLY COMPARISON
    renderMonthlyComparison(id, d) {
        const ctx = document.getElementById(id);
        if (!ctx) return;
        this.destroy(id);

        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: d.months,
                datasets: [{
                    data: d.attendanceRate,
                    backgroundColor: this.colors.primary
                }]
            },
            options: {
                responsive: true,
                scales: { y: { max: 100, beginAtZero: true } }
            }
        });
    }

    // 6️⃣ EMPLOYEE PERFORMANCE (FIXED)
    renderEmployeeRates(id, rows) {
        const ctx = document.getElementById(id);
        if (!ctx) return;
        this.destroy(id);

        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: rows.map(r => r.name),
                datasets: [{
                    data: rows.map(r => r.rate),
                    backgroundColor: this.colors.info
                }]
            },
            options: {
                indexAxis: 'y',
                scales: { x: { max: 100 } }
            }
        });
    }
}

const chartManager = new FaceTrackCharts();
