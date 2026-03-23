/* ============================================
   MedCare HMS - AI Features JS
   ============================================ */

// --- Symptom Checker ---
let symptoms = [];
let hourlyChart = null;
let weekChart = null;

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('symptomInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addSymptom();
    });

    document.getElementById('chatInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChat();
    });

    // Set today's date for load prediction
    const loadDate = document.getElementById('loadDate');
    if (loadDate) loadDate.valueAsDate = new Date();
});

function addSymptom() {
    const input = document.getElementById('symptomInput');
    const symptom = input.value.trim().toLowerCase();
    if (symptom && !symptoms.includes(symptom)) {
        symptoms.push(symptom);
        renderSymptomTags();
    }
    input.value = '';
    input.focus();
}

function quickAddSymptom(symptom) {
    symptom = symptom.toLowerCase();
    if (!symptoms.includes(symptom)) {
        symptoms.push(symptom);
        renderSymptomTags();
    }
}

function removeSymptom(index) {
    symptoms.splice(index, 1);
    renderSymptomTags();
}

function renderSymptomTags() {
    const container = document.getElementById('selectedSymptoms');
    if (symptoms.length === 0) {
        container.innerHTML = '<span class="text-muted" style="font-size:12px;">No symptoms selected</span>';
        return;
    }
    container.innerHTML = symptoms.map((s, i) => `
        <span class="symptom-tag">
            ${s}
            <span class="remove-symptom" onclick="removeSymptom(${i})"><i class="fas fa-times"></i></span>
        </span>
    `).join('');
}

function predictDisease() {
    if (symptoms.length === 0) {
        showToast('Please add at least one symptom', 'warning');
        return;
    }

    const btn = document.getElementById('predictBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Analyzing...';

    fetch('/api/ai/predict-disease', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptoms })
    })
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('predictionResults');

            if (data.predictions.length === 0) {
                container.innerHTML = `
                    <div class="text-center py-4 text-muted">
                        <i class="fas fa-question-circle fa-3x mb-3 opacity-25"></i>
                        <p>No matching diseases found for the given symptoms.</p>
                        <p class="small">Try adding more specific symptoms.</p>
                    </div>`;
                return;
            }

            container.innerHTML = `
                <div class="mb-3">
                    <small class="text-muted"><i class="fas fa-info-circle me-1"></i>
                    Analyzed ${data.symptoms_analyzed} symptoms. Top predictions shown below.
                    <strong>This is not a medical diagnosis.</strong></small>
                </div>
                ${data.predictions.map((p, i) => {
                    const severityColors = { Low: '#22c55e', Moderate: '#f59e0b', High: '#ef4444' };
                    const confColor = p.confidence > 60 ? '#ef4444' : p.confidence > 30 ? '#f59e0b' : '#3b82f6';
                    return `
                    <div class="prediction-card" style="animation: fadeIn 0.3s ease ${i * 0.1}s both;">
                        <div class="prediction-header">
                            <div>
                                <h6 class="mb-0">${p.disease}</h6>
                                <small class="text-muted">Specialist: ${p.specialist}</small>
                            </div>
                            <div class="text-end">
                                <span class="badge" style="background: ${severityColors[p.severity]}; color: white;">${p.severity} Risk</span>
                            </div>
                        </div>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: ${p.confidence}%; background: ${confColor};"></div>
                        </div>
                        <div class="d-flex justify-content-between mb-2">
                            <small class="text-muted">Confidence: <strong>${p.confidence}%</strong></small>
                            <small class="text-muted">Matched: ${p.matched_symptoms.length}/${p.total_symptoms} symptoms</small>
                        </div>
                        <div class="p-2 rounded" style="background: var(--bg-secondary); font-size: 12px;">
                            <i class="fas fa-comment-medical me-1 text-primary"></i> ${p.recommendation}
                        </div>
                    </div>`;
                }).join('')}
                <div class="alert alert-warning mt-3 mb-0" style="font-size: 12px;">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    <strong>Disclaimer:</strong> This AI prediction is for informational purposes only and should not replace professional medical advice. Please consult a qualified healthcare provider.
                </div>
            `;
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-brain me-1"></i> Analyze Symptoms';
        });
}

// --- Risk Analysis ---
function analyzeRisk() {
    const data = {
        age: parseInt(document.getElementById('riskAge').value) || 0,
        bmi: parseFloat(document.getElementById('riskBMI').value) || 22,
        bp_systolic: parseInt(document.getElementById('riskBPSys').value) || 120,
        bp_diastolic: parseInt(document.getElementById('riskBPDia').value) || 80,
        blood_sugar: parseInt(document.getElementById('riskSugar').value) || 100,
        heart_rate: parseInt(document.getElementById('riskHR').value) || 72,
        spo2: parseInt(document.getElementById('riskSpO2').value) || 98,
        smoker: document.getElementById('riskSmoker').checked
    };

    const container = document.getElementById('riskResults');
    container.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div><p class="mt-2 text-muted">Analyzing risk profile...</p></div>';

    fetch('/api/ai/risk-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(result => {
            container.innerHTML = `
                <div class="risk-meter">
                    <div class="risk-score-display" style="color: ${result.risk_color};">${result.risk_score}</div>
                    <div class="fs-6 fw-bold" style="color: ${result.risk_color};">${result.risk_level} Risk</div>
                    <p class="text-muted mt-2" style="font-size: 13px;">${result.summary}</p>
                </div>

                <h6 class="mb-3"><i class="fas fa-exclamation-circle me-1 text-warning"></i> Risk Factors</h6>
                ${result.risk_factors.length > 0 ? result.risk_factors.map(f => `
                    <div class="risk-factor-item">
                        <div>
                            <strong style="font-size: 13px;">${f.factor}</strong>
                            <small class="text-muted d-block">${f.details}</small>
                        </div>
                        <span class="badge bg-${f.impact === 'Critical' ? 'danger' : f.impact === 'High' ? 'warning' : 'info'}">${f.impact}</span>
                    </div>
                `).join('') : '<p class="text-muted">No significant risk factors identified.</p>'}

                <h6 class="mt-4 mb-3"><i class="fas fa-lightbulb me-1 text-success"></i> Recommendations</h6>
                <ul class="list-unstyled">
                    ${result.recommendations.map(r => `
                        <li class="mb-2" style="font-size: 13px;">
                            <i class="fas fa-check-circle text-success me-2"></i>${r}
                        </li>
                    `).join('')}
                </ul>
            `;
        })
        .catch(() => {
            container.innerHTML = '<div class="alert alert-danger">Error performing risk analysis.</div>';
        });
}
