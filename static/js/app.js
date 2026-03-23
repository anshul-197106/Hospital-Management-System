/* ============================================
   MedCare HMS - Core Application JS
   ============================================ */

// --- Theme Management ---
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', newTheme);
    html.setAttribute('data-bs-theme', newTheme); // Trigger BS5 built-in dark variations
    localStorage.setItem('theme', newTheme);

    const icon = document.getElementById('themeIcon');
    if (icon) {
        icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Load saved theme
(function () {
    const saved = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', saved);
    document.documentElement.setAttribute('data-bs-theme', saved);
    document.addEventListener('DOMContentLoaded', () => {
        const icon = document.getElementById('themeIcon');
        if (icon) {
            icon.className = saved === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    });
})();

// --- Sidebar Toggle ---
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.toggle('show');
    overlay.classList.toggle('show');
}

// --- Toast Notifications ---
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = {
        success: 'fa-check-circle',
        danger: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };

    const colors = {
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };

    const toastEl = document.createElement('div');
    toastEl.className = 'toast custom-toast show';
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
        <div class="toast-body d-flex align-items-center gap-2" style="background: var(--bg-primary); border-left: 3px solid ${colors[type]}; border-radius: var(--radius-md);">
            <i class="fas ${icons[type]}" style="color: ${colors[type]}; font-size: 18px;"></i>
            <span style="color: var(--text-primary); font-size: 13px; font-weight: 500;">${message}</span>
            <button type="button" class="btn-close ms-auto" style="font-size: 10px;" onclick="this.closest('.toast').remove()"></button>
        </div>
    `;

    container.appendChild(toastEl);

    setTimeout(() => {
        toastEl.style.opacity = '0';
        toastEl.style.transform = 'translateX(20px)';
        toastEl.style.transition = 'all 0.3s ease';
        setTimeout(() => toastEl.remove(), 300);
    }, 4000);
}

// --- Notifications ---
function loadNotifications() {
    fetch('/api/notifications')
        .then(r => r.json())
        .then(data => {
            const badge = document.getElementById('notifBadge');
            const list = document.getElementById('notifList');

            if (data.unread_count > 0) {
                badge.style.display = 'flex';
                badge.textContent = data.unread_count;
            } else {
                badge.style.display = 'none';
            }

            if (data.notifications.length === 0) {
                list.innerHTML = '<div class="notification-empty"><i class="fas fa-bell-slash mb-2 d-block" style="font-size:24px; opacity:0.3;"></i>No notifications</div>';
                return;
            }

            list.innerHTML = data.notifications.map(n => `
                <div class="notification-item ${n.is_read ? '' : 'bg-primary bg-opacity-10'}">
                    <div class="notif-title">${n.title}</div>
                    <div class="notif-message">${n.message}</div>
                    <div class="notif-time">${n.time_ago}</div>
                </div>
            `).join('');
        })
        .catch(() => { });
}

function markAllRead() {
    fetch('/api/notifications/read-all', { method: 'POST' })
        .then(() => loadNotifications());
}

// --- Utility Functions ---
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateTime(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function getStatusBadge(status) {
    const colors = {
        active: 'success', completed: 'success', paid: 'success', reviewed: 'success',
        scheduled: 'primary', pending: 'warning', partial: 'warning',
        discharged: 'secondary', cancelled: 'secondary', inactive: 'secondary',
        critical: 'danger', no_show: 'danger', overdue: 'danger', urgent: 'danger',
        on_leave: 'info'
    };
    const color = colors[status] || 'secondary';
    const label = (status || '').replace('_', ' ');
    return `<span class="badge bg-${color}-subtle text-${color}" style="text-transform: capitalize;">${label}</span>`;
}

function getPriorityBadge(priority) {
    const colors = { low: 'secondary', normal: 'primary', high: 'warning', urgent: 'danger' };
    const color = colors[priority] || 'secondary';
    return `<span class="badge bg-${color}" style="text-transform: capitalize;">${priority}</span>`;
}

// --- Pagination Renderer ---
function renderPagination(containerId, totalPages, currentPage, callback) {
    const container = document.getElementById(containerId);
    if (!container || totalPages <= 1) {
        if (container) container.innerHTML = '';
        return;
    }

    let html = '';

    html += `<li class="page-item ${currentPage <= 1 ? 'disabled' : ''}">
        <a class="page-link" href="#" onclick="event.preventDefault();${currentPage > 1 ? '' : 'return;'}" data-page="${currentPage - 1}">
            <i class="fas fa-chevron-left"></i>
        </a></li>`;

    const maxVisible = 5;
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    if (end - start < maxVisible - 1) start = Math.max(1, end - maxVisible + 1);

    if (start > 1) {
        html += `<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>`;
        if (start > 2) html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
    }

    for (let i = start; i <= end; i++) {
        html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
            <a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
    }

    if (end < totalPages) {
        if (end < totalPages - 1) html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        html += `<li class="page-item"><a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a></li>`;
    }

    html += `<li class="page-item ${currentPage >= totalPages ? 'disabled' : ''}">
        <a class="page-link" href="#" data-page="${currentPage + 1}">
            <i class="fas fa-chevron-right"></i>
        </a></li>`;

    container.innerHTML = html;

    container.querySelectorAll('.page-link[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = parseInt(link.dataset.page);
            if (page >= 1 && page <= totalPages) callback(page);
        });
    });
}

// --- Load Patient Options (for dropdowns) ---
function loadPatientOptions(selectId) {
    fetch('/api/patients?per_page=100')
        .then(r => r.json())
        .then(data => {
            const select = document.getElementById(selectId);
            if (!select) return;
            select.innerHTML = '<option value="">Select Patient</option>';
            data.patients.forEach(p => {
                select.innerHTML += `<option value="${p.id}">${p.patient_id} - ${p.full_name}</option>`;
            });
        });
}

// --- Load Doctor Options (for dropdowns) ---
function loadDoctorOptions(selectId) {
    fetch('/api/doctors?per_page=50')
        .then(r => r.json())
        .then(data => {
            const select = document.getElementById(selectId);
            if (!select) return;
            select.innerHTML = '<option value="">Select Doctor</option>';
            data.doctors.forEach(d => {
                select.innerHTML += `<option value="${d.id}">${d.full_name} - ${d.specialization}</option>`;
            });
        });
}

// --- Initialize ---
document.addEventListener('DOMContentLoaded', () => {
    // Load notifications
    if (document.getElementById('notifBtn')) {
        loadNotifications();
        setInterval(loadNotifications, 30000); // Refresh every 30s
    }

    // Global Search Logic
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const term = this.value.trim().toLowerCase();
                if (term) {
                    if (term.startsWith('doc')) {
                        window.location.href = `/doctors?search=${encodeURIComponent(term)}`;
                    } else if (term.startsWith('apt')) {
                        window.location.href = `/appointments?search=${encodeURIComponent(term)}`;
                    } else if (term.startsWith('bill')) {
                        window.location.href = `/billing?search=${encodeURIComponent(term)}`;
                    } else {
                        window.location.href = `/patients?search=${encodeURIComponent(term)}`;
                    }
                }
            }
        });
    }
});
