/* ============================================
   MedCare HMS - Doctors JS
   ============================================ */

let doctorsPage = 1;

document.addEventListener('DOMContentLoaded', () => {
    // Check URL parameters for search query
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('search')) {
        const searchInput = document.getElementById('doctorSearch');
        if (searchInput) searchInput.value = urlParams.get('search');
    }

    loadDoctors();
});

function loadDoctors() {
    const search = document.getElementById('doctorSearch').value;
    const status = document.getElementById('doctorStatusFilter').value;
    const spec = document.getElementById('doctorSpecFilter').value;

    const params = new URLSearchParams({
        page: doctorsPage, per_page: 8,
        search, status, specialization: spec
    });

    fetch(`/api/doctors?${params}`)
        .then(r => r.json())
        .then(data => {
            const grid = document.getElementById('doctorsGrid');

            if (data.doctors.length === 0) {
                grid.innerHTML = `<div class="col-12 text-center py-5 text-muted">
                    <i class="fas fa-user-md fa-3x mb-3 opacity-25"></i><p>No doctors found</p></div>`;
                return;
            }

            grid.innerHTML = data.doctors.map(d => `
                <div class="col-xl-3 col-lg-4 col-md-6">
                    <div class="doctor-card">
                        <div class="doctor-card-header">
                            <div class="doctor-avatar">
                                <i class="fas fa-user-md"></i>
                            </div>
                            <div>
                                <h6>${d.full_name}</h6>
                                <small>${d.specialization}</small>
                            </div>
                        </div>
                        <div class="mb-2">
                            ${getStatusBadge(d.status)}
                            <small class="text-muted ms-2">${d.qualification || ''}</small>
                        </div>
                        <div class="mb-2" style="font-size: 12px; color: var(--text-secondary);">
                            <div><i class="fas fa-clock me-1"></i> ${d.available_time_start || '09:00'} - ${d.available_time_end || '17:00'}</div>
                            <div><i class="fas fa-star me-1 text-warning"></i> ${d.rating || 4.5} Rating</div>
                            <div><i class="fas fa-dollar-sign me-1"></i> $${d.consultation_fee || 0} / visit</div>
                        </div>
                        <div class="doctor-card-stats">
                            <div class="doctor-stat">
                                <div class="doctor-stat-value">${d.experience_years || 0}</div>
                                <div class="doctor-stat-label">Years Exp</div>
                            </div>
                            <div class="doctor-stat">
                                <div class="doctor-stat-value">${d.total_patients || 0}</div>
                                <div class="doctor-stat-label">Patients</div>
                            </div>
                            <div class="doctor-stat">
                                <div class="doctor-stat-value">${d.total_appointments || 0}</div>
                                <div class="doctor-stat-label">Appts</div>
                            </div>
                        </div>
                        <div class="mt-3 d-flex gap-2">
                            <button class="btn btn-sm btn-outline-primary flex-fill" onclick="editDoctor(${d.id})">
                                <i class="fas fa-edit me-1"></i> Edit
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteDoctor(${d.id}, '${d.full_name}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');

            document.getElementById('doctorsInfo').textContent = `Showing ${data.doctors.length} of ${data.total} doctors`;
            renderPagination('doctorsPagination', data.pages, doctorsPage, (p) => {
                doctorsPage = p;
                loadDoctors();
            });
        });
}

function showAddDoctorModal() {
    document.getElementById('doctorForm').reset();
    document.getElementById('editDoctorId').value = '';
    document.getElementById('doctorModalTitle').textContent = 'Add New Doctor';
    new bootstrap.Modal(document.getElementById('doctorModal')).show();
}

function editDoctor(id) {
    fetch(`/api/doctors?per_page=50`)
        .then(r => r.json())
        .then(data => {
            const d = data.doctors.find(doc => doc.id === id);
            if (!d) return;

            document.getElementById('editDoctorId').value = d.id;
            document.getElementById('doctorModalTitle').textContent = 'Edit Doctor';
            document.getElementById('docName').value = d.full_name;
            document.getElementById('docSpec').value = d.specialization;
            document.getElementById('docQual').value = d.qualification || '';
            document.getElementById('docExp').value = d.experience_years || 0;
            document.getElementById('docPhone').value = d.phone;
            document.getElementById('docEmail').value = d.email;
            document.getElementById('docFee').value = d.consultation_fee || 0;
            document.getElementById('docTimeStart').value = d.available_time_start || '09:00';
            document.getElementById('docTimeEnd').value = d.available_time_end || '17:00';
            document.getElementById('docDept').value = d.department || '';
            document.getElementById('docMaxPatients').value = d.max_patients_per_day || 20;

            new bootstrap.Modal(document.getElementById('doctorModal')).show();
        });
}

function saveDoctor() {
    const id = document.getElementById('editDoctorId').value;
    const data = {
        full_name: document.getElementById('docName').value,
        specialization: document.getElementById('docSpec').value,
        qualification: document.getElementById('docQual').value,
        experience_years: parseInt(document.getElementById('docExp').value) || 0,
        phone: document.getElementById('docPhone').value,
        email: document.getElementById('docEmail').value,
        consultation_fee: parseFloat(document.getElementById('docFee').value) || 0,
        available_time_start: document.getElementById('docTimeStart').value,
        available_time_end: document.getElementById('docTimeEnd').value,
        department: document.getElementById('docDept').value,
        max_patients_per_day: parseInt(document.getElementById('docMaxPatients').value) || 20
    };

    const url = id ? `/api/doctors/${id}` : '/api/doctors';
    const method = id ? 'PUT' : 'POST';

    fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(res => {
            if (res.error) { showToast(res.error, 'danger'); return; }
            bootstrap.Modal.getInstance(document.getElementById('doctorModal')).hide();
            showToast(id ? 'Doctor updated!' : 'Doctor added!', 'success');
            loadDoctors();
        })
        .catch(() => showToast('Error saving doctor', 'danger'));
}

function deleteDoctor(id, name) {
    if (!confirm(`Delete doctor "${name}"?`)) return;
    fetch(`/api/doctors/${id}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(() => {
            showToast('Doctor deleted', 'success');
            loadDoctors();
        });
}
