/* ============================================
   MedCare HMS - Patients JS
   ============================================ */

let patientsPage = 1;

document.addEventListener('DOMContentLoaded', () => {
    // Check URL parameters for search query
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('search')) {
        const searchInput = document.getElementById('patientSearch');
        if (searchInput) searchInput.value = urlParams.get('search');
    }

    loadPatients();
    loadDoctorOptions('patDoctor');

    // Search on Enter
    document.getElementById('patientSearch').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadPatients();
    });
});

function loadPatients() {
    const search = document.getElementById('patientSearch').value;
    const status = document.getElementById('patientStatusFilter').value;
    const sortBy = document.getElementById('patientSort').value;

    const params = new URLSearchParams({
        page: patientsPage, per_page: 10,
        search, status, sort_by: sortBy, sort_order: 'desc'
    });

    fetch(`/api/patients?${params}`)
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('patientsTableBody');

            if (data.patients.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center py-5 text-muted">
                    <i class="fas fa-users fa-3x mb-3 d-block opacity-25"></i>No patients found</td></tr>`;
                return;
            }

            tbody.innerHTML = data.patients.map(p => `
                <tr>
                    <td><span class="fw-semibold text-primary">${p.patient_id}</span></td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <div class="user-avatar-sm"><i class="fas fa-user"></i></div>
                            <div>
                                <div class="fw-medium">${p.full_name}</div>
                                <small class="text-muted">${p.email || ''}</small>
                            </div>
                        </div>
                    </td>
                    <td>${p.age || '--'} / ${p.gender}</td>
                    <td>${p.phone}</td>
                    <td><span class="badge bg-danger-subtle text-danger">${p.blood_group || '--'}</span></td>
                    <td>${getStatusBadge(p.status)}</td>
                    <td><small>${p.assigned_doctor || '--'}</small></td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="viewPatient(${p.id})" title="View">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-outline-secondary" onclick="editPatient(${p.id})" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="deletePatient(${p.id}, '${p.full_name}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');

            document.getElementById('patientsInfo').textContent =
                `Showing ${(patientsPage - 1) * 10 + 1}-${Math.min(patientsPage * 10, data.total)} of ${data.total} patients`;

            renderPagination('patientsPagination', data.pages, patientsPage, (p) => {
                patientsPage = p;
                loadPatients();
            });
        });
}

function showAddPatientModal() {
    document.getElementById('patientForm').reset();
    document.getElementById('editPatientId').value = '';
    document.getElementById('patientModalTitle').textContent = 'Add New Patient';
    new bootstrap.Modal(document.getElementById('patientModal')).show();
}

function editPatient(id) {
    fetch(`/api/patients/${id}`)
        .then(r => r.json())
        .then(p => {
            document.getElementById('editPatientId').value = p.id;
            document.getElementById('patientModalTitle').textContent = 'Edit Patient';
            document.getElementById('patFirstName').value = p.first_name;
            document.getElementById('patLastName').value = p.last_name;
            document.getElementById('patDOB').value = p.date_of_birth;
            document.getElementById('patGender').value = p.gender;
            document.getElementById('patBloodGroup').value = p.blood_group || '';
            document.getElementById('patPhone').value = p.phone;
            document.getElementById('patEmail').value = p.email || '';
            document.getElementById('patAddress').value = p.address || '';
            document.getElementById('patEmergencyName').value = p.emergency_contact_name || '';
            document.getElementById('patEmergencyPhone').value = p.emergency_contact || '';
            document.getElementById('patMedHistory').value = p.medical_history || '';
            document.getElementById('patAllergies').value = p.allergies || '';
            document.getElementById('patMedications').value = p.current_medications || '';
            document.getElementById('patInsurance').value = p.insurance_provider || '';
            document.getElementById('patInsuranceId').value = p.insurance_id || '';
            document.getElementById('patWard').value = p.ward || '';
            document.getElementById('patBed').value = p.bed_number || '';
            document.getElementById('patDoctor').value = p.assigned_doctor_id || '';

            new bootstrap.Modal(document.getElementById('patientModal')).show();
        });
}

function savePatient() {
    const id = document.getElementById('editPatientId').value;
    const data = {
        first_name: document.getElementById('patFirstName').value,
        last_name: document.getElementById('patLastName').value,
        date_of_birth: document.getElementById('patDOB').value,
        gender: document.getElementById('patGender').value,
        blood_group: document.getElementById('patBloodGroup').value,
        phone: document.getElementById('patPhone').value,
        email: document.getElementById('patEmail').value,
        address: document.getElementById('patAddress').value,
        emergency_contact_name: document.getElementById('patEmergencyName').value,
        emergency_contact: document.getElementById('patEmergencyPhone').value,
        medical_history: document.getElementById('patMedHistory').value,
        allergies: document.getElementById('patAllergies').value,
        current_medications: document.getElementById('patMedications').value,
        insurance_provider: document.getElementById('patInsurance').value,
        insurance_id: document.getElementById('patInsuranceId').value,
        ward: document.getElementById('patWard').value,
        bed_number: document.getElementById('patBed').value,
        assigned_doctor_id: document.getElementById('patDoctor').value || null
    };

    const url = id ? `/api/patients/${id}` : '/api/patients';
    const method = id ? 'PUT' : 'POST';

    fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(res => {
            if (res.error) {
                showToast(res.error, 'danger');
                return;
            }
            bootstrap.Modal.getInstance(document.getElementById('patientModal')).hide();
            showToast(id ? 'Patient updated successfully!' : 'Patient registered successfully!', 'success');
            loadPatients();
        })
        .catch(() => showToast('Error saving patient', 'danger'));
}

function viewPatient(id) {
    fetch(`/api/patients/${id}`)
        .then(r => r.json())
        .then(p => {
            document.getElementById('viewPatientBody').innerHTML = `
                <div class="row g-4">
                    <div class="col-md-4 text-center">
                        <div class="profile-avatar-large mx-auto mb-3">
                            <i class="fas fa-user"></i>
                        </div>
                        <h5>${p.full_name}</h5>
                        <span class="badge bg-primary mb-2">${p.patient_id}</span>
                        <div>${getStatusBadge(p.status)}</div>
                    </div>
                    <div class="col-md-8">
                        <div class="row g-3">
                            <div class="col-6">
                                <small class="text-muted d-block">Age / Gender</small>
                                <strong>${p.age || '--'} / ${p.gender}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted d-block">Blood Group</small>
                                <strong>${p.blood_group || '--'}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted d-block">Phone</small>
                                <strong>${p.phone}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted d-block">Email</small>
                                <strong>${p.email || '--'}</strong>
                            </div>
                            <div class="col-12">
                                <small class="text-muted d-block">Address</small>
                                <strong>${p.address || '--'}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted d-block">Ward / Bed</small>
                                <strong>${p.ward || '--'} / ${p.bed_number || '--'}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted d-block">Doctor</small>
                                <strong>${p.assigned_doctor || '--'}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted d-block">Medical History</small>
                                <strong>${p.medical_history || 'None'}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted d-block">Allergies</small>
                                <strong>${p.allergies || 'None'}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted d-block">Insurance</small>
                                <strong>${p.insurance_provider || 'None'}</strong>
                            </div>
                            <div class="col-6">
                                <small class="text-muted d-block">Emergency Contact</small>
                                <strong>${p.emergency_contact_name || '--'} (${p.emergency_contact || '--'})</strong>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            new bootstrap.Modal(document.getElementById('viewPatientModal')).show();
        });
}

function deletePatient(id, name) {
    if (!confirm(`Are you sure you want to delete patient "${name}"? This will also delete their appointments, bills, and reports.`)) return;

    fetch(`/api/patients/${id}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(() => {
            showToast('Patient deleted successfully', 'success');
            loadPatients();
        });
}
