// =====================================
// DATE FORMATTING HELPER
// =====================================
function formatDate(dateStr) {
    if (!dateStr) return "-";
    try {
        const date = new Date(dateStr);
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const day = date.getDate();
        const month = months[date.getMonth()];
        const year = date.getFullYear();
        return `${day} ${month} ${year}`;
    } catch (e) {
        return dateStr;
    }
}

// =====================================
// PERIOD LABEL UPDATER
// =====================================
function updatePeriodLabels(period) {
    const periodLabels = {
        'last_7_days': 'Last 7 Days',
        'this_week': 'This Week',
        'this_month': 'This Month',
        'last_month': 'Last Month',
        'this_quarter': 'This Quarter',
        'this_year': 'This Year',
        'custom': 'Custom Period'
    };
    
    const deptPeriodLabels = {
        'last_7_days': 'Last 7 Days (Weekly Summary)',
        'this_week': 'This Week (Weekly Summary)',
        'this_month': 'This Month (Monthly Summary)',
        'last_month': 'Last Month (Monthly Summary)',
        'this_quarter': 'This Quarter (Quarterly Summary)',
        'this_year': 'This Year (Yearly Summary)',
        'custom': 'Custom Period (Aggregated Data)'
    };
    
    const label = periodLabels[period] || 'Last 7 Days';
    const deptLabel = deptPeriodLabels[period] || 'Last 7 Days (Weekly Summary)';
    
    // Update all labels
    const selectedPeriodLabel = document.getElementById('selectedPeriodLabel');
    const chartPeriodBadge = document.getElementById('chartPeriodBadge');
    const deptChartPeriodLabel = document.getElementById('deptChartPeriodLabel');
    
    if (selectedPeriodLabel) selectedPeriodLabel.textContent = label;
    if (chartPeriodBadge) chartPeriodBadge.textContent = label;
    if (deptChartPeriodLabel) deptChartPeriodLabel.textContent = deptLabel;
    
    console.log('📅 Updated period labels to:', label);
}

// =====================================
// INITIAL LOAD
// =====================================
// Calendar navigation
let currentCalendarDate = new Date();
let selectedEmployeeId = null;
let overviewDateFilter = 'last_7_days'; // Default filter for overview

document.addEventListener("DOMContentLoaded", function() {
    console.log("🚀 Reports page initializing...");
    
    // Attach event listeners
    const applyBtn = document.getElementById("applyFilters");
    if (applyBtn) {
        applyBtn.addEventListener("click", () => {
            console.log("🔍 Apply Filters button clicked");
            loadTable();
        });
        console.log("✅ Apply Filters listener attached");
    } else {
        console.error("❌ applyFilters button not found!");
    }
    
    document.getElementById("loadEmployeeData")?.addEventListener("click", loadEmployeeAnalysis);
    document.getElementById("refreshData")?.addEventListener("click", () => {
        loadSummary();
        loadCharts();
    });
    
    // Overview date filter buttons
    const overviewPeriodBtns = document.querySelectorAll('.overview-period-btn');
    const overviewCustomRange = document.getElementById('overviewCustomDateRange');
    
    overviewPeriodBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            overviewPeriodBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            overviewDateFilter = this.dataset.period;
            
            // Update period labels
            updatePeriodLabels(overviewDateFilter);
            
            if (overviewDateFilter === 'custom') {
                overviewCustomRange?.classList.remove('hidden');
                // Don't auto-reload for custom, wait for user to select dates
            } else {
                overviewCustomRange?.classList.add('hidden');
                // Auto-reload charts for preset periods
                loadSummary();
                loadCharts();
            }
        });
    });
    
    document.getElementById('applyOverviewFilter')?.addEventListener('click', () => {
        // Update custom period label with selected dates
        if (overviewDateFilter === 'custom') {
            const from = document.getElementById('overviewFromDate')?.value;
            const to = document.getElementById('overviewToDate')?.value;
            if (from && to) {
                const fromFormatted = formatDate(from);
                const toFormatted = formatDate(to);
                const customLabel = `${fromFormatted} to ${toFormatted}`;
                document.getElementById('selectedPeriodLabel').textContent = customLabel;
                document.getElementById('chartPeriodBadge').textContent = 'Custom Range';
            }
        }
        loadSummary();
        loadCharts();
    });
    
    document.getElementById('resetOverviewFilter')?.addEventListener('click', () => {
        overviewDateFilter = 'last_7_days';
        overviewPeriodBtns.forEach(b => b.classList.remove('active'));
        overviewPeriodBtns[0]?.classList.add('active');
        overviewCustomRange?.classList.add('hidden');
        document.getElementById('overviewFromDate').value = '';
        document.getElementById('overviewToDate').value = '';
        updatePeriodLabels('last_7_days');
        loadSummary();
        loadCharts();
    });
    
    // Employee period type toggle
    const empPeriodType = document.getElementById('employeePeriodType');
    if (empPeriodType) {
        empPeriodType.addEventListener('change', function() {
            const monthSelector = document.getElementById('employeeMonthSelector');
            const customRange = document.getElementById('employeeCustomDateRange');
            
            if (this.value === 'custom') {
                monthSelector?.classList.add('hidden');
                customRange?.classList.remove('hidden');
            } else {
                monthSelector?.classList.remove('hidden');
                customRange?.classList.add('hidden');
            }
        });
    }
    
    // Generate report button (inline)
    document.getElementById("generateReportBtn")?.addEventListener("click", generateReport);
    
    // Reset filters button
    const resetBtn = document.getElementById("resetFilters");
    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            console.log("🔄 Reset Filters button clicked");
            resetAllFilters();
        });
        console.log("✅ Reset Filters listener attached");
    } else {
        console.error("❌ resetFilters button not found!");
    }
    
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
    console.log("📦 Calling initReports()...");
    initReports();
    
    // Load dropdowns for report generator
    loadReportDropdowns();
    
    // Setup Generate Report tab interactivity
    setupGenerateReportTab();
    
    // Auto-refresh for admin/HR every 30 seconds
    if (!window.isEmployeeView) {
        setInterval(() => {
            loadSummary();
            loadCharts();
        }, 30000); // 30 seconds
    }
    
    console.log("✅ Reports page initialization complete");
});

async function initReports() {
    console.log("📊 initReports() started");
    // Check if this is employee view
    const isEmployeeView = window.isEmployeeView || false;
    console.log("👤 Is employee view:", isEmployeeView);
    
    if (isEmployeeView) {
        // Employee view: Auto-load their own data
        console.log("📊 Loading employee self data...");
        await loadEmployeeSelfData();
    } else {
        // Admin/HR view: Load all data
        console.log("📊 Loading admin/HR data...");
        await loadSummary();
        await loadCharts();
        await loadDepartments();
        await loadEmployees();
        await loadEmployeeDropdown();
        await loadTable();
        console.log("✅ All admin/HR data loaded");
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
    let url = "/admin/reports/api/summary?";
    
    // Add date filter based on selection
    if (overviewDateFilter === 'custom') {
        const from = document.getElementById('overviewFromDate')?.value;
        const to = document.getElementById('overviewToDate')?.value;
        if (from && to) {
            url += `period=custom&from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&`;
        } else {
            // If custom selected but no dates, default to last 7 days
            url += `period=last_7_days&`;
        }
    } else {
        // Always send period parameter
        url += `period=${encodeURIComponent(overviewDateFilter)}&`;
    }
    
    console.log('📊 Loading summary with URL:', url);
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") return;

            const presentCount = document.getElementById("presentCount");
            const absentCount = document.getElementById("absentCount");
            const lateCount = document.getElementById("lateCount");
            // Accept either 'attendancePercent' or 'attendancePercentage' id used in templates
            const attendancePercent = document.getElementById("attendancePercent") || document.getElementById("attendancePercentage");

            const setText = (el, val) => { if (!el) return; el.textContent = val; el.setAttribute('data-target', val); };

            setText(presentCount, data.summary.present ?? 0);
            setText(absentCount, data.summary.absent ?? 0);
            setText(lateCount, data.summary.late ?? 0);
            if (attendancePercent) setText(attendancePercent, (data.summary.attendance_percent !== undefined && data.summary.attendance_percent !== null) ? data.summary.attendance_percent + "%" : "-");

            // Re-run countup animation for updated elements
            runCountups();
        })
        .catch(err => console.error("Summary load error:", err));
}

// Helper to animate number/countup elements after dynamic update
function runCountups() {
    document.querySelectorAll('.countup').forEach(function(el) {
        const targetRaw = el.getAttribute('data-target');
        if (!targetRaw || targetRaw === '-') return;
        // Remove any non-numeric characters (like %)
        const numeric = parseFloat(String(targetRaw).replace(/[^0-9.\-]/g, ''));
        if (isNaN(numeric)) return;
        const target = numeric;
        let start = 0;
        const duration = 800;
        let current = start;
        const steps = 40;
        const step = (target - start) / steps;
        let i = 0;
        const timer = setInterval(() => {
            i++;
            current += step;
            if ((target > start && current >= target) || (target < start && current <= target) || i >= steps) {
                el.textContent = (String(targetRaw).includes('%')) ? `${target}%` : Math.round(target);
                clearInterval(timer);
            } else {
                el.textContent = Math.round(current);
            }
        }, duration / steps);
    });
}



// =====================================
// CHART DATA
// =====================================
let lineChartRef = null;
let barChartRef = null;

async function loadCharts() {
    let url = "/admin/reports/api/chart-data?";
    
    // Add date filter based on selection
    if (overviewDateFilter === 'custom') {
        const from = document.getElementById('overviewFromDate')?.value;
        const to = document.getElementById('overviewToDate')?.value;
        if (from && to) {
            url += `period=custom&from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}&`;
        } else {
            // If custom selected but no dates, default to last 7 days
            url += `period=last_7_days&`;
        }
    } else {
        // Always send period parameter
        url += `period=${encodeURIComponent(overviewDateFilter)}&`;
    }
    
    console.log('📊 Loading charts with URL:', url);
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.status !== "ok") return;

            // Use summary data for doughnut chart if available, otherwise fall back to daily calculation
            if (data.chart.summary) {
                renderLineChart(data.chart.summary);
            } else {
                renderLineChart(data.chart.daily);
            }
            renderBarChart(data.chart.departments);
        })
        .catch(err => console.error("Chart load error:", err));
}



// =====================================
// PIE CHART (ATTENDANCE OVERVIEW)
// =====================================
function renderLineChart(chartData) {
    const canvas = document.getElementById("lineChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    let totalPresent, totalAbsent, totalLate;

    // Check if chartData is summary object or daily array
    if (chartData.present !== undefined && chartData.absent !== undefined && chartData.late !== undefined) {
        // New format: summary object with unique employee counts
        totalPresent = chartData.present || 0;
        totalAbsent = chartData.absent || 0;
        totalLate = chartData.late || 0;
    } else {
        // Old format: daily array - sum the values (inflated numbers)
        totalPresent = chartData.reduce((sum, d) => sum + (d.present || 0), 0);
        totalAbsent = chartData.reduce((sum, d) => sum + (d.absent || 0), 0);
        totalLate = chartData.reduce((sum, d) => sum + (d.late || 0), 0);
    }

    if (totalPresent === 0 && totalAbsent === 0 && totalLate === 0) {
        drawNoDataOnCanvas(canvas, 'No attendance data available');
        if (lineChartRef) { lineChartRef.destroy(); lineChartRef = null; }
        return;
    }

    if (lineChartRef) lineChartRef.destroy();

    // Center text plugin for doughnut chart
    const centerTextPlugin = {
        id: 'doughnutCenterText',
        beforeDraw: function(chart) {
            const { width, height, ctx } = chart;
            const { text, subtext, color, fontSize, subFontSize } = chart.options.plugins.doughnutCenterText;
            
            ctx.restore();
            ctx.font = `bold ${fontSize}px Inter, sans-serif`;
            ctx.fillStyle = color;
            ctx.textBaseline = 'middle';
            ctx.textAlign = 'center';
            
            const textX = width / 2;
            const textY = height / 2 - 10;
            
            ctx.fillText(text, textX, textY);
            
            if (subtext) {
                ctx.font = `600 ${subFontSize}px Inter, sans-serif`;
                ctx.fillStyle = '#6b7280';
                ctx.fillText(subtext, textX, textY + 20);
            }
            
            ctx.save();
        }
    };

    // Create modern gradients for each segment
    const presentGradient = ctx.createRadialGradient(150, 150, 50, 150, 150, 150);
    presentGradient.addColorStop(0, '#22C55E'); // Fresh green
    presentGradient.addColorStop(1, '#16A34A'); // Darker green

    const absentGradient = ctx.createRadialGradient(150, 150, 50, 150, 150, 150);
    absentGradient.addColorStop(0, '#EF4444'); // Clean red
    absentGradient.addColorStop(1, '#DC2626'); // Darker red

    const lateGradient = ctx.createRadialGradient(150, 150, 50, 150, 150, 150);
    lateGradient.addColorStop(0, '#F59E0B'); // Amber
    lateGradient.addColorStop(1, '#D97706'); // Darker amber

    lineChartRef = new Chart(ctx, {
        type: "doughnut",
        plugins: [centerTextPlugin],
        data: {
            labels: ["Present", "Absent", "Late"],
            datasets: [{
                data: [totalPresent, totalAbsent, totalLate],
                backgroundColor: [
                    presentGradient,
                    absentGradient,
                    lateGradient
                ],
                borderColor: [
                    '#ffffff', // White borders for contrast
                    '#ffffff',
                    '#ffffff'
                ],
                borderWidth: 4,
                hoverBorderWidth: 6,
                hoverBorderColor: [
                    '#ffffff',
                    '#ffffff',
                    '#ffffff'
                ],
                hoverOffset: 12,
                shadowOffsetX: 0,
                shadowOffsetY: 4,
                shadowBlur: 8,
                shadowColor: 'rgba(0, 0, 0, 0.1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            size: 14,
                            weight: '700',
                            family: 'Inter, sans-serif'
                        },
                        color: '#374151'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    cornerRadius: 12,
                    padding: 16,
                    titleFont: {
                        size: 16,
                        weight: '700'
                    },
                    bodyFont: {
                        size: 14,
                        weight: '500'
                    },
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? Math.round((context.parsed / total) * 100) : 0;
                            return `${context.label} – ${context.parsed} (${percentage}%)`;
                        }
                    },
                    shadowOffsetX: 0,
                    shadowOffsetY: 4,
                    shadowBlur: 8,
                    shadowColor: 'rgba(0, 0, 0, 0.1)'
                },
                // Center text plugin
                doughnutCenterText: {
                    text: `${totalPresent + totalAbsent + totalLate}`,
                    subtext: 'Total Employees',
                    color: '#374151',
                    fontSize: 24,
                    subFontSize: 12
                }
            },
            cutout: '72%',
            animation: {
                animateScale: true,
                animateRotate: true,
                duration: 1800,
                easing: 'easeOutCubic'
            },
            elements: {
                arc: {
                    borderRadius: 8
                }
            }
        }
    });
}



// =====================================
// BAR CHART (DEPARTMENT-WISE) - MODERN CARDS STYLE
// =====================================
function renderBarChart(chartData) {
    const canvas = document.getElementById("barChart");
    if (!canvas) {
        console.error('Bar chart canvas not found');
        return;
    }
    const ctx = canvas.getContext("2d");
    
    // Clear canvas first
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!chartData || chartData.length === 0) {
        drawNoDataOnCanvas(canvas, 'No department data');
        if (barChartRef) { barChartRef.destroy(); barChartRef = null; }
        return;
    }

    if (barChartRef) barChartRef.destroy();

    const labels  = chartData.map(d => d.department);
    const attendancePercentages = chartData.map(d => d.attendance_percentage || 0);

    // Create beautiful gradient for bars (green family to match donut)
    const barGradient = ctx.createLinearGradient(0, 0, 0, 50);
    barGradient.addColorStop(0, '#22C55E'); // Green
    barGradient.addColorStop(0.5, '#16A34A'); // Darker green
    barGradient.addColorStop(1, '#15803D'); // Even darker green

    // Center text plugin for doughnut chart
    const centerTextPlugin = {
        id: 'doughnutCenterText',
        beforeDraw: function(chart) {
            const { width, height, ctx } = chart;
            const { text, subtext, color, fontSize, subFontSize } = chart.options.plugins.doughnutCenterText;
            
            ctx.restore();
            ctx.font = `bold ${fontSize}px Inter, sans-serif`;
            ctx.fillStyle = color;
            ctx.textBaseline = 'middle';
            ctx.textAlign = 'center';
            
            const textX = width / 2;
            const textY = height / 2 - 10;
            
            ctx.fillText(text, textX, textY);
            
            if (subtext) {
                ctx.font = `600 ${subFontSize}px Inter, sans-serif`;
                ctx.fillStyle = '#6b7280';
                ctx.fillText(subtext, textX, textY + 20);
            }
            
            ctx.save();
        }
    };

    try {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded');
            return;
        }
        barChartRef = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Weekly Attendance %",
                    data: attendancePercentages,
                    backgroundColor: '#f59e0b', // Orange single color
                    borderColor: '#ffffff',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    barThickness: 30,
                    maxBarThickness: 45,
                    minBarLength: 5,
                    hoverBackgroundColor: '#d97706',
                    hoverBorderColor: '#ffffff',
                    hoverBorderWidth: 3,
                    shadowOffsetX: 0,
                    shadowOffsetY: 6,
                    shadowBlur: 12,
                    shadowColor: 'rgba(245, 158, 11, 0.4)'
                }
            ]
        },
        options: {
            backgroundColor: 'rgba(219, 234, 254, 0.3)', // Light blue background
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    left: 20,
                    right: 20,
                    top: 10,
                    bottom: 10
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(31, 41, 55, 0.95)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: 'rgba(245, 158, 11, 0.3)',
                    borderWidth: 2,
                    cornerRadius: 16,
                    displayColors: false,
                    padding: 20,
                    titleFont: {
                        size: 16,
                        weight: '700',
                        family: 'Inter, sans-serif'
                    },
                    bodyFont: {
                        size: 14,
                        weight: '500',
                        family: 'Inter, sans-serif'
                    },
                    callbacks: {
                        title: function(context) {
                            return `📊 ${context[0].label}`;
                        },
                        label: function(context) {
                            return `Attendance: ${context.parsed.y}%`;
                        }
                    },
                    shadowOffsetX: 0,
                    shadowOffsetY: 8,
                    shadowBlur: 16,
                    shadowColor: 'rgba(0, 0, 0, 0.2)'
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            size: 12,
                            family: 'Inter, sans-serif',
                            weight: '600'
                        },
                        color: '#374151',
                        padding: 15,
                        maxTicksLimit: 10
                    },
                    border: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    suggestedMax: 100, // Ensure bars show even with low data
                    grid: {
                        color: 'rgba(245, 158, 11, 0.1)', // Light orange grid
                        lineWidth: 1,
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            size: 12,
                            family: 'Inter, sans-serif',
                            weight: '600'
                        },
                        color: '#d97706', // Orange
                        padding: 15,
                        stepSize: 20,
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    border: {
                        display: false
                    }
                }
            },
            elements: {
                bar: {
                    borderRadius: 12
                }
            },
            animation: {
                duration: 1600,
                easing: 'easeOutElastic',
                delay: function(context) {
                    return context.dataIndex * 250;
                },
                onProgress: function(animation) {
                    // Add sparkle effect during animation
                    const progress = animation.currentStep / animation.numSteps;
                    if (progress > 0.7) {
                        ctx.shadowColor = 'rgba(245, 158, 11, 0.6)';
                        ctx.shadowBlur = 20;
                    }
                }
            }
        }
    });
    
    } catch (error) {
        console.error('Error creating bar chart:', error);
    }
}

// Draw a professional 'no data' message on a canvas
function drawNoDataOnCanvas(canvas, message) {
    try {
        const ctx = canvas.getContext('2d');
        // clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        // draw message
        ctx.save();
        ctx.fillStyle = '#6b7280';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const fontSize = Math.max(14, Math.floor(canvas.width / 25));
        ctx.font = `400 ${fontSize}px Inter, sans-serif`;
        ctx.fillText(message, canvas.width / 2, canvas.height / 2);
        ctx.restore();
    } catch (e) {
        // ignore drawing errors
    }
}



// =====================================
// DEPARTMENT DROPDOWN
// =====================================
async function loadDepartments() {
    console.log("📊 Loading departments...");
    fetch("/admin/reports/api/departments")
        .then(res => res.json())
        .then(data => {
            console.log("📊 Departments response:", data);
            if (data.status !== "ok") return;

            const dept = document.getElementById("departmentFilter");
            if (!dept) {
                console.error("❌ Department filter element not found!");
                return;
            }
            dept.innerHTML = `<option value="">All</option>`;

            data.departments.forEach(d => {
                const opt = document.createElement("option");
                opt.value = d.name;
                opt.textContent = d.name;
                dept.appendChild(opt);
            });
            console.log(`✅ Loaded ${data.departments.length} departments`);
        })
        .catch(err => console.error("❌ Failed to load departments:", err));
}



// =====================================
// EMPLOYEE DROPDOWN (for analysis)
// =====================================
async function loadEmployeeDropdown() {
    fetch("/admin/reports/api/employees")
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
    const periodType = document.getElementById("employeePeriodType")?.value || 'month';
    
    const employeeName = empSelector.value;
    
    if (!employeeName) {
        alert("Please select an employee");
        return;
    }
    
    let year, month;
    
    if (periodType === 'month') {
        const monthSelector = document.getElementById("monthSelector");
        const monthValue = monthSelector.value;
        
        if (!monthValue) {
            alert("Please select a month");
            return;
        }
        
        // Parse month
        [year, month] = monthValue.split('-');
    } else {
        // Custom date range - use current month for calendar display
        const fromDate = document.getElementById("empFromDate")?.value;
        const toDate = document.getElementById("empToDate")?.value;
        
        if (!fromDate || !toDate) {
            alert("Please select both From and To dates");
            return;
        }
        
        // Use the from date to determine calendar month
        const fromDateObj = new Date(fromDate);
        year = fromDateObj.getFullYear();
        month = fromDateObj.getMonth() + 1;
    }
    
    // Get employee ID from selected option
    const selectedOption = empSelector.options[empSelector.selectedIndex];
    selectedEmployeeId = employeeName;
    
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
// EMPLOYEE ATTENDANCE SUMMARY (for cards)
// =====================================
async function loadEmployeeAttendanceSummary(employeeName) {
    // Get today's date
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    
    const url = `/admin/reports/api/table?from=${todayStr}&to=${todayStr}&employee=${encodeURIComponent(employeeName)}`;
    
    fetch(url)
        .then(res => res.json())
        .then(data => {
            if (data.status === "ok") {
                // Count today's attendance for this employee
                const todayRecords = data.records.filter(record => record.date === todayStr);
                
                let present = 0;
                let late = 0;
                let absent = 1; // Assume absent unless proven present
                
                if (todayRecords.length > 0) {
                    present = 1; // Employee checked in
                    absent = 0;
                    
                    // Check if any check-in was late (after 9:30 AM)
                    const lateCheckin = todayRecords.find(record => {
                        if (record.entry_time) {
                            const time = record.entry_time.split(' ')[1] || record.entry_time;
                            return time > '09:30:00';
                        }
                        return false;
                    });
                    
                    if (lateCheckin) {
                        late = 1;
                    }
                }
                
                // Update cards with employee data
                const presentCount = document.getElementById("presentCount");
                const absentCount = document.getElementById("absentCount");
                const lateCount = document.getElementById("lateCount");
                const attendancePercent = document.getElementById("attendancePercentage");
                
                const setText = (el, val) => { if (!el) return; el.textContent = val; el.setAttribute('data-target', val); };
                
                setText(presentCount, present);
                setText(absentCount, absent);
                setText(lateCount, late);
                setText(attendancePercent, present ? "100%" : "0%");
                
                // Re-run countup animation
                runCountups();
            }
        })
        .catch(err => console.error("Failed to load employee attendance summary:", err));
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
        
        if (status === "present" || status === "late" || status === "check-in" || status === "check-out" || status === "already") {
            // Treat check-in/check-out/already as present for calendar visualization
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
    console.log("👥 Loading employees...");
    fetch("/admin/reports/api/employees")
        .then(res => res.json())
        .then(data => {
            console.log("👥 Employees response:", data);
            if (data.status !== "ok") return;

            const emp = document.getElementById("employeeFilter");
            if (!emp) {
                console.error("❌ Employee filter element not found!");
                return;
            }
            emp.innerHTML = `<option value="">All</option>`;

            data.employees.forEach(e => {
                const opt = document.createElement("option");
                opt.value = e.full_name;
                opt.textContent = e.full_name;
                emp.appendChild(opt);
            });
            console.log(`✅ Loaded ${data.employees.length} employees`);
        })
        .catch(err => console.error("❌ Failed to load employees:", err));
}



// =====================================
// TABLE API (FILTERS)
// =====================================
async function loadTable() {
    console.log("📋 Loading table with filters...");
    const from = document.getElementById("fromDate").value;
    const to   = document.getElementById("toDate").value;
    const user = document.getElementById("employeeFilter").value;
    const dept = document.getElementById("departmentFilter").value;

    console.log("📋 Filter values:", { from, to, user, dept });

    let url = "/admin/reports/api/table?";

    if (from) url += `from=${encodeURIComponent(from)}&`;
    if (to)   url += `to=${encodeURIComponent(to)}&`;
    if (user) url += `user=${encodeURIComponent(user)}&`;
    if (dept) url += `department=${encodeURIComponent(dept)}&`;

    console.log("📋 Fetching from:", url);

    fetch(url)
        .then(res => res.json())
        .then(data => {
            console.log("📋 Table response:", data);
            if (data.status !== "ok") {
                console.error("❌ Table API returned non-OK status");
                return;
            }
            console.log(`✅ Rendering ${data.records.length} records`);
            renderTable(data.records);
        })
        .catch(err => console.error("❌ Table load error:", err));
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
            <td class="p-2">${formatDate(r.date)}</td>
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
// MODAL CONTROLS
// =====================================
// Load dropdowns for inline report generator
async function loadReportDropdowns() {
    console.log("📋 Loading report dropdowns...");
    // Load employees
    try {
        const empRes = await fetch('/admin/reports/api/employees');
        const empData = await empRes.json();
        const empSelect = document.getElementById('modalEmployeeSelector');
        if (empSelect && empData.employees) {
            empSelect.innerHTML = '<option value="">-- Select Employee --</option>';
            empData.employees.forEach(emp => {
                empSelect.innerHTML += `<option value="${emp.id}">${emp.full_name}</option>`;
            });
            console.log(`✅ Loaded ${empData.employees.length} employees for report`);
        }
    } catch (err) {
        console.error('❌ Failed to load employees:', err);
    }
    
    // Load departments
    try {
        const deptRes = await fetch('/admin/reports/api/departments');
        const deptData = await deptRes.json();
        const deptSelect = document.getElementById('modalDepartmentFilter');
        if (deptSelect && deptData.departments) {
            deptSelect.innerHTML = '<option value="">All Departments</option>';
            deptData.departments.forEach(dept => {
                deptSelect.innerHTML += `<option value="${dept.name}">${dept.name}</option>`;
            });
            console.log(`✅ Loaded ${deptData.departments.length} departments for report`);
        }
    } catch (err) {
        console.error('❌ Failed to load departments:', err);
    }
}

// =====================================
// SETUP GENERATE REPORT TAB
// =====================================
function setupGenerateReportTab() {
    console.log("⚙️ Setting up Generate Report tab...");
    
    // Period buttons
    const periodButtons = document.querySelectorAll('.period-btn');
    const customDateRange = document.getElementById('customDateRange');
    
    periodButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active from all
            periodButtons.forEach(b => b.classList.remove('active'));
            // Add active to clicked
            this.classList.add('active');
            
            // Show/hide custom date range
            if (this.dataset.period === 'custom') {
                customDateRange?.classList.remove('hidden');
                console.log("📅 Custom date range shown");
            } else {
                customDateRange?.classList.add('hidden');
                console.log("📅 Period selected:", this.dataset.period);
            }
        });
    });
    console.log(`✅ Attached listeners to ${periodButtons.length} period buttons`);
    
    // Employee scope radio buttons
    const employeeRadios = document.querySelectorAll('input[name="employee_scope"]');
    const employeeSelector = document.getElementById('modalEmployeeSelector');
    const departmentFilter = document.getElementById('modalDepartmentFilter');
    
    employeeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'specific') {
                employeeSelector?.removeAttribute('disabled');
                employeeSelector?.classList.remove('disabled:bg-gray-100');
                console.log("👤 Employee selector enabled");
            } else {
                employeeSelector?.setAttribute('disabled', 'true');
                employeeSelector?.classList.add('disabled:bg-gray-100');
                if (employeeSelector) employeeSelector.value = '';
                if (departmentFilter) departmentFilter.value = '';
                console.log("👥 All employees selected");
            }
        });
    });
    console.log(`✅ Attached listeners to ${employeeRadios.length} employee radio buttons`);
    
    // Auto-select department when employee is selected
    if (employeeSelector) {
        employeeSelector.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const employeeId = selectedOption.value;
            
            if (employeeId) {
                console.log("👤 Employee selected, fetching department...");
                // Fetch employee details to get department
                fetch(`/admin/reports/api/employees`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.status === 'ok') {
                            const employee = data.employees.find(emp => emp.id == employeeId);
                            if (employee && employee.department) {
                                if (departmentFilter) {
                                    departmentFilter.value = employee.department;
                                    console.log("🏢 Auto-selected department:", employee.department);
                                }
                            }
                        }
                    })
                    .catch(err => console.error("❌ Failed to fetch employee details:", err));
            } else {
                // Clear department when no employee selected
                if (departmentFilter) departmentFilter.value = '';
            }
        });
        console.log("✅ Employee auto-select department listener attached");
    }
    
    console.log("✅ Generate Report tab setup complete");
}

function generateReport() {
    console.log("📄 Generating report...");
    // Get selected period
    const periodBtn = document.querySelector('.period-btn.active');
    const selectedPeriod = periodBtn ? periodBtn.dataset.period : 'this_month';
    console.log("📅 Selected period:", selectedPeriod);
    
    // Get dates
    let fromDate = '';
    let toDate = '';
    if (selectedPeriod === 'custom') {
        fromDate = document.getElementById('modalFromDate').value;
        toDate = document.getElementById('modalToDate').value;
        
        if (!fromDate || !toDate) {
            alert('Please select both from and to dates for custom range');
            console.error("❌ Custom dates not selected");
            return;
        }
        console.log("📅 Custom dates:", fromDate, "to", toDate);
    }
    
    // Get employee scope
    const employeeScope = document.querySelector('input[name="employee_scope"]:checked')?.value || 'all';
    let employeeId = '';
    
    if (employeeScope === 'specific') {
        employeeId = document.getElementById('modalEmployeeSelector')?.value || '';
        if (!employeeId) {
            alert('Please select an employee');
            console.error("❌ No employee selected");
            return;
        }
        console.log("👤 Selected employee ID:", employeeId);
    } else {
        console.log("👥 All employees selected");
    }
    
    // Get department
    const department = document.getElementById('modalDepartmentFilter')?.value || '';
    if (department) {
        console.log("🏢 Selected department:", department);
    }
    
    // Get format
    const formatRadio = document.querySelector('input[name="export_format"]:checked');
    const format = formatRadio ? formatRadio.value : 'pdf';
    console.log("📊 Export format:", format);
    
    // Build URL
    let url = `/admin/reports/api/export/${format}?`;
    
    if (selectedPeriod === 'custom') {
        url += `period=custom&`;
        if (fromDate) url += `from=${encodeURIComponent(fromDate)}&`;
        if (toDate) url += `to=${encodeURIComponent(toDate)}&`;
    } else {
        url += `period=${selectedPeriod}&`;
    }
    
    if (employeeId) url += `employee_id=${encodeURIComponent(employeeId)}&`;
    if (department) url += `department=${encodeURIComponent(department)}&`;
    
    console.log("🔗 Export URL:", url);
    
    // Show loading state
    const btn = document.getElementById('generateReportBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating...';
    btn.disabled = true;
    
    // Download report
    if (format === 'pdf') {
        window.open(url, '_blank');
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
            console.log("✅ PDF generation initiated");
        }, 1000);
    } else {
        window.location.href = url;
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
            console.log(`✅ ${format.toUpperCase()} download initiated`);
        }, 2000);
    }
}

// Reset filters function
function resetAllFilters() {
    console.log("🔄 Resetting all filters...");
    // Clear date filters
    const fromDate = document.getElementById("fromDate");
    const toDate = document.getElementById("toDate");
    if (fromDate) {
        fromDate.value = '';
        console.log("✅ Cleared fromDate");
    }
    if (toDate) {
        toDate.value = '';
        console.log("✅ Cleared toDate");
    }
    
    // Reset dropdown filters
    const employeeFilter = document.getElementById("employeeFilter");
    const departmentFilter = document.getElementById("departmentFilter");
    if (employeeFilter) {
        employeeFilter.value = '';
        console.log("✅ Cleared employeeFilter");
    }
    if (departmentFilter) {
        departmentFilter.value = '';
        console.log("✅ Cleared departmentFilter");
    }
    
    // Reload table with cleared filters
    console.log("🔄 Reloading table with cleared filters...");
    loadTable();
}

// Make functions global
window.resetAllFilters = resetAllFilters;


// =====================================
// LEGACY EXPORT FUNCTIONS (Keep for backward compatibility)
// =====================================
function exportCSV() {
    const from = document.getElementById("fromDate")?.value || '';
    const to   = document.getElementById("toDate")?.value || '';
    const user = document.getElementById("employeeFilter")?.value || '';
    const dept = document.getElementById("departmentFilter")?.value || '';

    let url = "/admin/reports/api/export/csv?period=custom&";

    if (from) url += `from=${encodeURIComponent(from)}&`;
    if (to)   url += `to=${encodeURIComponent(to)}&`;
    if (user) url += `user=${encodeURIComponent(user)}&`;
    if (dept) url += `department=${encodeURIComponent(dept)}&`;

    window.location.href = url;
}

function exportPDF() {
    const from = document.getElementById("fromDate")?.value || '';
    const to   = document.getElementById("toDate")?.value || '';
    const user = document.getElementById("employeeFilter")?.value || '';
    const dept = document.getElementById("departmentFilter")?.value || '';

    let url = "/admin/reports/api/export/pdf?period=custom&";

    if (from) url += `from=${encodeURIComponent(from)}&`;
    if (to)   url += `to=${encodeURIComponent(to)}&`;
    if (user) url += `user=${encodeURIComponent(user)}&`;
    if (dept) url += `department=${encodeURIComponent(dept)}&`;

    window.open(url, "_blank");

}
