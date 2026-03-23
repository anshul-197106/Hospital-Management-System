/* ============================================
   MedCare HMS - Appointments JS
   ============================================ */

let appointmentsPage = 1;

document.addEventListener('DOMContentLoaded', () => {
    // Check URL parameters for search query
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('search')) {
        const searchInput = document.getElementById('apptSearch');
        if (searchInput) searchInput.value = urlParams.get('search');
    }

    loadAppointments();
    loadPatientOptions('apptPatient');
    loadDoctorOptions('apptDoctor');

    // Set default date to today
    const dateInput = document.getElementById('apptDate');
    if (dateInput) dateInput.valueAsDate = new Date();
});

function loadAppointments() {
    const search = document.getElementById('apptSearch').value;
    const status = document.getElementById('apptStatusFilter').value;
    const date = document.getElementById('apptDateFilter').value;

    const params = new URLSearchParams({
        page: appointmentsPage, per_page: 10,
        search, status, date
    });

    fetch(`/api/appointments?${params}`)
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('appointmentsTableBody');

            if (data.appointments.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center py-5 text-muted">
                    <i class="fas fa-calendar fa-3x mb-3 d-block opacity-25"></i>No appointments found</td></tr>`;
                return;
            }

            tbody.innerHTML = data.appointments.map(a => `
                <tr>
                    <td><span class="fw-semibold text-primary">${a.appointment_id}</span></td>
                    <td>
                        <div class="fw-medium">${a.patient_name || 'N/A'}</div>
                    </td>
                    <td>
                        <div>${a.doctor_name || 'N/A'}</div>
                        <small class="text-muted">${a.doctor_specialization || ''}</small>
                    </td>
                    <td>
                        <div>${formatDate(a.appointment_date)}</div>
                        <small class="text-muted">${a.appointment_time}</small>
                    </td>
                    <td><span class="badge bg-info-subtle text-info" style="text-transform:capitalize;">${(a.type || '').replace('_', ' ')}</span></td>
                    <td>${getPriorityBadge(a.priority)}</td>
                    <td>${getStatusBadge(a.status)}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            ${a.status === 'scheduled' ? `
                                <button class="btn btn-outline-success" onclick="updateApptStatus(${a.id}, 'completed')" title="Complete">
                                    <i class="fas fa-check"></i>
                                </button>
                                <button class="btn btn-outline-warning" onclick="updateApptStatus(${a.id}, 'cancelled')" title="Cancel">
                                    <i class="fas fa-times"></i>
                                </button>
                            ` : ''}
                            <button class="btn btn-outline-secondary" onclick="editAppointment(${a.id})" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="deleteAppointment(${a.id})" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');

            document.getElementById('appointmentsInfo').textContent =
                `Showing ${data.appointments.length} of ${data.total} appointments`;

            renderPagination('appointmentsPagination', data.pages, appointmentsPage, (p) => {
                appointmentsPage = p;
                loadAppointments();
            });
        });
}

function showAddAppointmentModal() {
    document.getElementById('appointmentForm').reset();
    document.getElementById('editApptId').value = '';
    document.getElementById('apptModalTitle').textContent = 'Book Appointment';
    document.getElementById('apptDate').valueAsDate = new Date();
    new bootstrap.Modal(document.getElementById('appointmentModal')).show();
}

function editAppointment(id) {
    fetch(`/api/appointments?per_page=100`)
        .then(r => r.json())
        .then(data => {
            const a = data.appointments.find(ap => ap.id === id);
            if (!a) return;

            document.getElementById('editApptId').value = a.id;
            document.getElementById('apptModalTitle').textContent = 'Edit Appointment';
            document.getElementById('apptPatient').value = a.patient_id;
            document.getElementById('apptDoctor').value = a.doctor_id;
            document.getElementById('apptDate').value = a.appointment_date;
            document.getElementById('apptTime').value = a.appointment_time;
            document.getElementById('apptDuration').value = a.duration_minutes;
            document.getElementById('apptType').value = a.type;
            document.getElementById('apptPriority').value = a.priority;
            document.getElementById('apptSymptoms').value = a.symptoms || '';
            document.getElementById('apptNotes').value = a.notes || '';

            new bootstrap.Modal(document.getElementById('appointmentModal')).show();
        });
}

function saveAppointment() {
    const id = document.getElementById('editApptId').value;
    const data = {
        patient_id: document.getElementById('apptPatient').value,
        doctor_id: document.getElementById('apptDoctor').value,
        appointment_date: document.getElementById('apptDate').value,
        appointment_time: document.getElementById('apptTime').value,
        duration_minutes: parseInt(document.getElementById('apptDuration').value),
        type: document.getElementById('apptType').value,
        priority: document.getElementById('apptPriority').value,
        symptoms: document.getElementById('apptSymptoms').value,
        notes: document.getElementById('apptNotes').value
    };

    const url = id ? `/api/appointments/${id}` : '/api/appointments';
    const method = id ? 'PUT' : 'POST';

    fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(res => {
            if (res.error) { showToast(res.error, 'danger'); return; }
            bootstrap.Modal.getInstance(document.getElementById('appointmentModal')).hide();
            showToast(id ? 'Appointment updated!' : 'Appointment booked!', 'success');
            loadAppointments();
        })
        .catch(() => showToast('Error saving appointment', 'danger'));
}

function updateApptStatus(id, status) {
    fetch(`/api/appointments/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
    })
        .then(r => r.json())
        .then(() => {
            showToast(`Appointment ${status}!`, status === 'completed' ? 'success' : 'warning');
            loadAppointments();
        });
}

function deleteAppointment(id) {
    if (!confirm('Delete this appointment?')) return;
    fetch(`/api/appointments/${id}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(() => {
            showToast('Appointment deleted', 'success');
            loadAppointments();
        });
}
