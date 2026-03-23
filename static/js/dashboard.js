/* ============================================
   MedCare HMS - Dashboard JS
   ============================================ */

let trendsChart = null;
let revenueChart = null;
let workloadChart = null;

document.addEventListener('DOMContentLoaded', loadDashboard);

function loadDashboard() {
    fetch('/api/dashboard/stats')
        .then(r => r.json())
        .then(data => {
            // Update Stats Cards
            animateNumber('totalPatients', data.total_patients);
            animateNumber('totalDoctors', data.total_doctors);
            animateNumber('totalAppointments', data.total_appointments);
            document.getElementById('totalRevenue').textContent = formatCurrency(data.total_revenue);
            document.getElementById('activePatients').textContent = data.active_patients;
            document.getElementById('todayAppointments').textContent = data.today_appointments;
            document.getElementById('pendingAppointments').textContent = data.pending_appointments;

            // Render Charts
            renderTrendsChart(data.chart_labels, data.patient_data, data.appointment_data);
            if (document.getElementById('revenueChart')) {
                renderRevenueChart(data.revenue_labels, data.revenue_data);
            }

            // Recent Appointments
            renderRecentAppointments(data.recent_appointments);

            // AI Insights
            renderAIInsights(data.ai_insights);
        })
        .catch(err => console.error('Dashboard error:', err));
}

function animateNumber(elementId, target) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    // Smooth, fast animation using requestAnimationFrame
    const duration = 800; // ms
    const start = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smoother stop
        const easeOutQuad = progress * (2 - progress);
        const current = Math.floor(target * easeOutQuad);
        
        el.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.textContent = target.toLocaleString();
        }
    }
    
    requestAnimationFrame(update);
}

function renderTrendsChart(labels, patientData, appointmentData) {
    const ctx = document.getElementById('trendsChart');
    if (!ctx) return;

    if (trendsChart) trendsChart.destroy();

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'New Patients',
                    data: patientData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointBackgroundColor: '#3b82f6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                },
                {
                    label: 'Appointments',
                    data: appointmentData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointBackgroundColor: '#8b5cf6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: textColor, usePointStyle: true, padding: 20, font: { size: 12 } }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: gridColor, drawBorder: false },
                    ticks: { color: textColor, font: { size: 11 } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: textColor, font: { size: 11 } }
                }
            },
            interaction: { intersect: false, mode: 'index' }
        }
    });
}

function renderRevenueChart(labels, data) {
    const ctx = document.getElementById('revenueChart');
    if (!ctx) return;

    if (revenueChart) revenueChart.destroy();

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    revenueChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Revenue ($)',
                data: data,
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(139, 92, 246, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(6, 182, 212, 0.8)',
                    'rgba(236, 72, 153, 0.8)'
                ],
                borderRadius: 8,
                borderSkipped: false,
                barThickness: 28
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)', drawBorder: false },
                    ticks: {
                        color: textColor,
                        font: { size: 11 },
                        callback: v => '$' + (v / 1000).toFixed(0) + 'k'
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: textColor, font: { size: 11 } }
                }
            }
        }
    });
}


function renderRecentAppointments(appointments) {
    const tbody = document.getElementById('recentAppointmentsBody');
    if (!tbody) return;

    if (appointments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-muted">No recent appointments</td></tr>';
        return;
    }

    tbody.innerHTML = appointments.map(a => `
        <tr>
            <td>
                <div class="d-flex align-items-center gap-2">
                    <div class="user-avatar-sm"><i class="fas fa-user"></i></div>
                    <span class="fw-medium">${a.patient_name || 'N/A'}</span>
                </div>
            </td>
            <td><small class="text-muted">${a.doctor_name || 'N/A'}</small></td>
            <td><small>${formatDate(a.appointment_date)}</small></td>
            <td>${getStatusBadge(a.status)}</td>
        </tr>
    `).join('');
}

function renderAIInsights(insights) {
    const container = document.getElementById('aiInsightsContainer');
    if (!container || !insights) return;

    container.innerHTML = insights.map(insight => `
        <div class="col-md-6 col-lg-3">
            <div class="ai-insight-card insight-${insight.type}">
                <div class="d-flex align-items-center gap-2 mb-2">
                    <i class="fas ${insight.icon}" style="color: var(--${insight.type === 'success' ? 'success' : insight.type === 'warning' ? 'warning' : 'primary'})"></i>
                    <strong style="font-size: 13px;">${insight.title}</strong>
                </div>
                <p class="text-muted mb-2" style="font-size: 12px;">${insight.message}</p>
                <span class="badge bg-${insight.type === 'success' ? 'success' : insight.type === 'warning' ? 'warning' : 'primary'}-subtle text-${insight.type === 'success' ? 'success' : insight.type === 'warning' ? 'warning' : 'primary'} fs-6">${insight.metric}</span>
            </div>
        </div>
    `).join('');
}
function formatCurrency(v) {
    return '$' + parseFloat(v).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getStatusBadge(status) {
    const s = (status || 'pending').toLowerCase();
    const badges = {
        'scheduled': 'bg-primary-subtle text-primary',
        'completed': 'bg-success-subtle text-success',
        'cancelled': 'bg-danger-subtle text-danger',
        'pending': 'bg-warning-subtle text-warning'
    };
    const cls = badges[s] || 'bg-secondary-subtle text-secondary';
    return `<span class="badge ${cls}">${s.toUpperCase()}</span>`;
}
