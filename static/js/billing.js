/* ============================================
   MedCare HMS - Billing JS
   ============================================ */

let billsPage = 1;

document.addEventListener('DOMContentLoaded', () => {
    // Check URL parameters for search query
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('search')) {
        const searchInput = document.getElementById('billSearch');
        if (searchInput) searchInput.value = urlParams.get('search');
    }

    loadBills();
    loadPatientOptions('billPatient');
});

function loadBills() {
    const search = document.getElementById('billSearch').value;
    const status = document.getElementById('billStatusFilter').value;

    const params = new URLSearchParams({
        page: billsPage, per_page: 10, search, status
    });

    fetch(`/api/bills?${params}`)
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('billsTableBody');

            // Update summary
            let totalRev = 0, paidCount = 0, pendingCount = 0;
            data.bills.forEach(b => {
                totalRev += b.paid_amount || 0;
                if (b.payment_status === 'paid') paidCount++;
                if (b.payment_status === 'pending') pendingCount++;
            });

            document.getElementById('billTotalRevenue').textContent = formatCurrency(totalRev);
            document.getElementById('billPaidCount').textContent = paidCount;
            document.getElementById('billPendingCount').textContent = pendingCount;
            document.getElementById('billTotalCount').textContent = data.total;

            if (data.bills.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" class="text-center py-5 text-muted">
                    <i class="fas fa-file-invoice fa-3x mb-3 d-block opacity-25"></i>No bills found</td></tr>`;
                return;
            }

            tbody.innerHTML = data.bills.map(b => `
                <tr>
                    <td><span class="fw-semibold text-primary">${b.bill_id}</span></td>
                    <td>${b.patient_name || 'N/A'}</td>
                    <td><strong>${formatCurrency(b.total_amount)}</strong></td>
                    <td class="text-success">${formatCurrency(b.paid_amount)}</td>
                    <td class="${b.balance > 0 ? 'text-danger' : 'text-success'}">${formatCurrency(b.balance)}</td>
                    <td><span class="badge bg-secondary-subtle text-secondary" style="text-transform:capitalize;">${b.payment_method || '--'}</span></td>
                    <td>${getStatusBadge(b.payment_status)}</td>
                    <td><small>${formatDate(b.created_at)}</small></td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-secondary" onclick="editBill(${b.id})" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="deleteBill(${b.id})" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');

            document.getElementById('billsInfo').textContent =
                `Showing ${data.bills.length} of ${data.total} bills`;

            renderPagination('billsPagination', data.pages, billsPage, (p) => {
                billsPage = p;
                loadBills();
            });
        });
}

function showAddBillModal() {
    document.getElementById('billForm').reset();
    document.getElementById('editBillId').value = '';
    document.getElementById('billModalTitle').textContent = 'Generate Bill';
    calculateBillTotal();
    new bootstrap.Modal(document.getElementById('billModal')).show();
}

function calculateBillTotal() {
    const consultation = parseFloat(document.getElementById('billConsultation').value) || 0;
    const medicine = parseFloat(document.getElementById('billMedicine').value) || 0;
    const lab = parseFloat(document.getElementById('billLab').value) || 0;
    const room = parseFloat(document.getElementById('billRoom').value) || 0;
    const surgery = parseFloat(document.getElementById('billSurgery').value) || 0;
    const other = parseFloat(document.getElementById('billOther').value) || 0;
    const discount = parseFloat(document.getElementById('billDiscount').value) || 0;
    const tax = parseFloat(document.getElementById('billTax').value) || 0;

    const subtotal = consultation + medicine + lab + room + surgery + other;
    const discountAmt = subtotal * (discount / 100);
    const taxAmt = (subtotal - discountAmt) * (tax / 100);
    const total = subtotal - discountAmt + taxAmt;

    document.getElementById('billSubtotal').textContent = formatCurrency(subtotal);
    document.getElementById('billDiscountAmt').textContent = `-${formatCurrency(discountAmt)}`;
    document.getElementById('billTaxAmt').textContent = `+${formatCurrency(taxAmt)}`;
    document.getElementById('billTotal').textContent = formatCurrency(total);
}

function editBill(id) {
    fetch(`/api/bills?per_page=100`)
        .then(r => r.json())
        .then(data => {
            const b = data.bills.find(bill => bill.id === id);
            if (!b) return;

            document.getElementById('editBillId').value = b.id;
            document.getElementById('billModalTitle').textContent = 'Edit Bill';
            document.getElementById('billPatient').value = b.patient_id;
            document.getElementById('billConsultation').value = b.consultation_fee;
            document.getElementById('billMedicine').value = b.medicine_charges;
            document.getElementById('billLab').value = b.lab_charges;
            document.getElementById('billRoom').value = b.room_charges;
            document.getElementById('billSurgery').value = b.surgery_charges;
            document.getElementById('billOther').value = b.other_charges;
            document.getElementById('billDiscount').value = b.discount;
            document.getElementById('billTax').value = b.tax_percentage;
            document.getElementById('billPaid').value = b.paid_amount;
            document.getElementById('billMethod').value = b.payment_method || 'cash';
            document.getElementById('billStatus').value = b.payment_status;
            calculateBillTotal();

            new bootstrap.Modal(document.getElementById('billModal')).show();
        });
}

function saveBill() {
    const id = document.getElementById('editBillId').value;
    const data = {
        patient_id: document.getElementById('billPatient').value,
        consultation_fee: parseFloat(document.getElementById('billConsultation').value) || 0,
        medicine_charges: parseFloat(document.getElementById('billMedicine').value) || 0,
        lab_charges: parseFloat(document.getElementById('billLab').value) || 0,
        room_charges: parseFloat(document.getElementById('billRoom').value) || 0,
        surgery_charges: parseFloat(document.getElementById('billSurgery').value) || 0,
        other_charges: parseFloat(document.getElementById('billOther').value) || 0,
        discount: parseFloat(document.getElementById('billDiscount').value) || 0,
        tax_percentage: parseFloat(document.getElementById('billTax').value) || 0,
        paid_amount: parseFloat(document.getElementById('billPaid').value) || 0,
        payment_method: document.getElementById('billMethod').value,
        payment_status: document.getElementById('billStatus').value
    };

    const url = id ? `/api/bills/${id}` : '/api/bills';
    const method = id ? 'PUT' : 'POST';

    fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(res => {
            if (res.error) { showToast(res.error, 'danger'); return; }
            bootstrap.Modal.getInstance(document.getElementById('billModal')).hide();
            showToast(id ? 'Bill updated!' : 'Bill generated!', 'success');
            loadBills();
        })
        .catch(() => showToast('Error saving bill', 'danger'));
}

function deleteBill(id) {
    if (!confirm('Delete this bill?')) return;
    fetch(`/api/bills/${id}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(() => {
            showToast('Bill deleted', 'success');
            loadBills();
        });
}
