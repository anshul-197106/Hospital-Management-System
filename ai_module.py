"""
AI Module for Hospital Management System
Contains: Disease Prediction, Appointment Load Prediction, Medical Chatbot, Patient Risk Analysis
"""
import random
from datetime import datetime, timedelta


# --- Disease Prediction based on Symptoms ---
DISEASE_DATABASE = {
    'Common Cold': {
        'symptoms': ['runny nose', 'sneezing', 'sore throat', 'cough', 'mild fever', 'headache', 'body ache'],
        'severity': 'Low',
        'recommendation': 'Rest, drink fluids, OTC cold medication. Consult doctor if symptoms persist over 7 days.',
        'specialist': 'General Physician'
    },
    'Influenza (Flu)': {
        'symptoms': ['high fever', 'body ache', 'fatigue', 'cough', 'headache', 'chills', 'sore throat'],
        'severity': 'Moderate',
        'recommendation': 'Rest, antiviral medication, fluids. See doctor within 48 hours for antiviral treatment.',
        'specialist': 'General Physician'
    },
    'COVID-19': {
        'symptoms': ['fever', 'dry cough', 'fatigue', 'loss of taste', 'loss of smell', 'breathing difficulty', 'body ache'],
        'severity': 'High',
        'recommendation': 'Isolate immediately, get tested, monitor oxygen levels. Seek emergency care if breathing difficulty worsens.',
        'specialist': 'Pulmonologist'
    },
    'Migraine': {
        'symptoms': ['severe headache', 'nausea', 'vomiting', 'light sensitivity', 'vision changes', 'dizziness'],
        'severity': 'Moderate',
        'recommendation': 'Rest in dark room, prescribed migraine medication. Keep a trigger diary.',
        'specialist': 'Neurologist'
    },
    'Gastroenteritis': {
        'symptoms': ['diarrhea', 'vomiting', 'nausea', 'stomach pain', 'fever', 'dehydration', 'abdominal cramps'],
        'severity': 'Moderate',
        'recommendation': 'Oral rehydration, bland diet, anti-nausea medication. Seek care if dehydration is severe.',
        'specialist': 'Gastroenterologist'
    },
    'Pneumonia': {
        'symptoms': ['high fever', 'cough', 'chest pain', 'breathing difficulty', 'fatigue', 'chills', 'phlegm'],
        'severity': 'High',
        'recommendation': 'Antibiotics required. Hospitalization may be needed for severe cases. Monitor oxygen.',
        'specialist': 'Pulmonologist'
    },
    'Hypertension': {
        'symptoms': ['headache', 'dizziness', 'blurred vision', 'chest pain', 'nosebleed', 'fatigue', 'shortness of breath'],
        'severity': 'High',
        'recommendation': 'Regular BP monitoring, medication adherence, low-sodium diet, regular exercise.',
        'specialist': 'Cardiologist'
    },
    'Diabetes (Type 2)': {
        'symptoms': ['frequent urination', 'excessive thirst', 'fatigue', 'blurred vision', 'slow healing', 'weight loss', 'tingling'],
        'severity': 'High',
        'recommendation': 'Blood sugar monitoring, medication/insulin, dietary changes, regular exercise.',
        'specialist': 'Endocrinologist'
    },
    'Urinary Tract Infection': {
        'symptoms': ['burning urination', 'frequent urination', 'cloudy urine', 'pelvic pain', 'fever', 'back pain'],
        'severity': 'Moderate',
        'recommendation': 'Antibiotics, increased fluid intake. Follow up if symptoms persist after treatment.',
        'specialist': 'Urologist'
    },
    'Allergic Reaction': {
        'symptoms': ['rash', 'itching', 'swelling', 'sneezing', 'watery eyes', 'hives', 'breathing difficulty'],
        'severity': 'Moderate',
        'recommendation': 'Antihistamines, avoid allergens. Seek emergency care if breathing difficulty or anaphylaxis.',
        'specialist': 'Allergist'
    },
    'Asthma': {
        'symptoms': ['wheezing', 'shortness of breath', 'chest tightness', 'cough', 'breathing difficulty'],
        'severity': 'Moderate',
        'recommendation': 'Use prescribed inhalers, avoid triggers, create an asthma action plan with your doctor.',
        'specialist': 'Pulmonologist'
    },
    'Dengue Fever': {
        'symptoms': ['high fever', 'severe headache', 'joint pain', 'muscle pain', 'rash', 'nausea', 'fatigue'],
        'severity': 'High',
        'recommendation': 'Hospitalization may be needed. Monitor platelet count, rest, hydration. Avoid aspirin.',
        'specialist': 'Infectious Disease Specialist'
    }
}


def predict_disease(symptoms_list):
    """Predict possible diseases based on input symptoms"""
    if not symptoms_list:
        return []

    symptoms_lower = [s.strip().lower() for s in symptoms_list]
    results = []

    for disease, info in DISEASE_DATABASE.items():
        disease_symptoms = [s.lower() for s in info['symptoms']]
        matched = [s for s in symptoms_lower if any(ds in s or s in ds for ds in disease_symptoms)]
        match_count = len(matched)

        if match_count > 0:
            confidence = min(95, round((match_count / len(disease_symptoms)) * 100))
            results.append({
                'disease': disease,
                'confidence': confidence,
                'matched_symptoms': matched,
                'total_symptoms': len(disease_symptoms),
                'severity': info['severity'],
                'recommendation': info['recommendation'],
                'specialist': info['specialist']
            })

    results.sort(key=lambda x: x['confidence'], reverse=True)
    return results[:5]


# --- Appointment Load Prediction ---
def predict_appointment_load(date_str=None):
    """Predict appointment load for a given date"""
    if date_str:
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        target_date = datetime.now()

    day_of_week = target_date.weekday()
    day_name = target_date.strftime('%A')
    month = target_date.month

    # Base load by day of week
    day_loads = {
        0: 85,   # Monday - high
        1: 78,   # Tuesday
        2: 72,   # Wednesday
        3: 75,   # Thursday
        4: 80,   # Friday
        5: 45,   # Saturday - lower
        6: 30    # Sunday - lowest
    }

    base_load = day_loads.get(day_of_week, 70)

    # Seasonal adjustment
    seasonal = {1: 1.15, 2: 1.1, 3: 1.05, 4: 1.0, 5: 0.95, 6: 0.9,
                7: 0.95, 8: 1.0, 9: 1.05, 10: 1.1, 11: 1.15, 12: 1.2}
    season_factor = seasonal.get(month, 1.0)

    predicted_load = int(base_load * season_factor)
    variation = random.randint(-5, 5)
    predicted_load = max(10, min(100, predicted_load + variation))

    # Hourly distribution
    hourly_dist = [
        {'hour': '08:00', 'label': '8 AM', 'load': int(predicted_load * 0.6)},
        {'hour': '09:00', 'label': '9 AM', 'load': int(predicted_load * 0.85)},
        {'hour': '10:00', 'label': '10 AM', 'load': predicted_load},
        {'hour': '11:00', 'label': '11 AM', 'load': int(predicted_load * 0.95)},
        {'hour': '12:00', 'label': '12 PM', 'load': int(predicted_load * 0.5)},
        {'hour': '13:00', 'label': '1 PM', 'load': int(predicted_load * 0.4)},
        {'hour': '14:00', 'label': '2 PM', 'load': int(predicted_load * 0.75)},
        {'hour': '15:00', 'label': '3 PM', 'load': int(predicted_load * 0.85)},
        {'hour': '16:00', 'label': '4 PM', 'load': int(predicted_load * 0.9)},
        {'hour': '17:00', 'label': '5 PM', 'load': int(predicted_load * 0.65)},
    ]

    peak_hour = max(hourly_dist, key=lambda x: x['load'])
    low_hour = min(hourly_dist, key=lambda x: x['load'])

    status = 'Normal'
    if predicted_load > 80:
        status = 'High'
    elif predicted_load > 60:
        status = 'Moderate'
    elif predicted_load < 30:
        status = 'Low'

    return {
        'date': target_date.strftime('%Y-%m-%d'),
        'day': day_name,
        'predicted_total': int(predicted_load * 2.5),
        'load_percentage': predicted_load,
        'status': status,
        'peak_hour': peak_hour['label'],
        'low_hour': low_hour['label'],
        'hourly_distribution': hourly_dist,
        'recommendation': _get_load_recommendation(status),
        'week_forecast': _get_week_forecast(target_date)
    }


def _get_load_recommendation(status):
    recs = {
        'High': 'Consider scheduling additional staff. Reduce non-urgent appointments. Prepare for longer wait times.',
        'Moderate': 'Normal staffing should be sufficient. Monitor for unexpected surges.',
        'Normal': 'Standard operations. Good time for routine check-ups and follow-ups.',
        'Low': 'Consider reduced staffing. Schedule maintenance or training activities.'
    }
    return recs.get(status, 'Standard operations.')


def _get_week_forecast(start_date):
    forecast = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        day_load = {0: 85, 1: 78, 2: 72, 3: 75, 4: 80, 5: 45, 6: 30}
        load = day_load.get(d.weekday(), 70) + random.randint(-8, 8)
        load = max(10, min(100, load))
        forecast.append({
            'date': d.strftime('%Y-%m-%d'),
            'day': d.strftime('%a'),
            'load': load
        })
    return forecast


# --- Medical Chatbot ---
CHATBOT_RESPONSES = {
    'hours': {
        'keywords': ['hours', 'open', 'timing', 'time', 'schedule', 'when'],
        'response': '🏥 **Hospital Hours:**\n- **Emergency:** 24/7 (Open round the clock)\n- **OPD:** Monday-Saturday, 8:00 AM - 5:00 PM\n- **Pharmacy:** 24/7\n- **Lab Services:** Monday-Saturday, 7:00 AM - 6:00 PM\n- **Visiting Hours:** 10:00 AM - 12:00 PM & 4:00 PM - 6:00 PM'
    },
    'departments': {
        'keywords': ['department', 'departments', 'speciality', 'specialties', 'services'],
        'response': '🏥 **Our Departments:**\n- Cardiology\n- Neurology\n- Orthopedics\n- Pediatrics\n- Gynecology\n- Dermatology\n- Ophthalmology\n- ENT\n- General Medicine\n- General Surgery\n- Emergency Medicine\n- Radiology & Imaging\n- Pathology & Lab\n- Psychiatry'
    },
    'appointment': {
        'keywords': ['appointment', 'book', 'booking', 'schedule', 'visit', 'consult'],
        'response': '📅 **Booking an Appointment:**\n1. Use the Appointments section in the dashboard\n2. Select your preferred doctor and specialization\n3. Choose date and time slot\n4. Provide symptoms or reason for visit\n\nYou can also call our front desk at **+1-800-HOSPITAL** for assistance.'
    },
    'emergency': {
        'keywords': ['emergency', 'urgent', 'critical', 'ambulance', '911'],
        'response': '🚨 **Emergency Services:**\n- Our Emergency Department is open **24/7**\n- Ambulance Helpline: **108** or **+1-800-EMERGENCY**\n- Trauma Center available\n- ICU beds available\n\n⚠️ If experiencing chest pain, difficulty breathing, or severe bleeding, call emergency services immediately!'
    },
    'insurance': {
        'keywords': ['insurance', 'coverage', 'claim', 'cashless', 'policy'],
        'response': '💳 **Insurance Information:**\n- We accept all major insurance providers\n- Cashless treatment available for network partners\n- Insurance desk available at the front lobby\n- Documents needed: Insurance card, ID proof, policy number\n- Claim processing within 7-10 business days'
    },
    'billing': {
        'keywords': ['bill', 'billing', 'payment', 'cost', 'charges', 'fees', 'price'],
        'response': '💰 **Billing Information:**\n- Payment modes: Cash, Credit/Debit Card, UPI, Insurance\n- Billing counter at Ground Floor\n- Online payment available through patient portal\n- EMI options available for surgeries above ₹50,000\n- Consultation fee varies by department (₹300-₹1500)'
    },
    'admission': {
        'keywords': ['admission', 'admit', 'bed', 'room', 'ward', 'icu'],
        'response': '🛏️ **Admission Information:**\n- **General Ward:** ₹1,500/day\n- **Semi-Private Room:** ₹3,000/day\n- **Private Room:** ₹5,000/day\n- **Deluxe Suite:** ₹10,000/day\n- **ICU:** ₹8,000/day\n\nDocuments needed: ID proof, insurance details, doctor referral. Contact admissions at ext. 101.'
    },
    'reports': {
        'keywords': ['report', 'reports', 'test', 'results', 'lab'],
        'response': '📋 **Reports & Test Results:**\n- Lab reports available within 24-48 hours\n- Reports can be accessed through the patient portal\n- Physical copies available at the lab counter\n- For urgent reports, contact the lab at ext. 501'
    },
    'greeting': {
        'keywords': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'help'],
        'response': '👋 **Hello! Welcome to MedCare Hospital Assistant!**\n\nI can help you with:\n- 🕐 Hospital hours & schedules\n- 📅 Appointment booking\n- 🏥 Department information\n- 🚨 Emergency services\n- 💳 Insurance & billing\n- 🛏️ Admission details\n- 📋 Report inquiries\n\nJust type your question and I\'ll assist you!'
    }
}


def chatbot_respond(message):
    """Generate chatbot response based on user message"""
    if not message:
        return {'response': 'Please type a message for me to help you!', 'category': 'error'}

    message_lower = message.lower().strip()

    best_match = None
    best_score = 0

    for category, data in CHATBOT_RESPONSES.items():
        score = sum(1 for kw in data['keywords'] if kw in message_lower)
        if score > best_score:
            best_score = score
            best_match = category

    if best_match and best_score > 0:
        return {
            'response': CHATBOT_RESPONSES[best_match]['response'],
            'category': best_match,
            'confidence': min(95, best_score * 30)
        }

    return {
        'response': "I'm not sure I understand your question. Here are some topics I can help with:\n\n"
                    "- **Hospital hours** - Ask about our timings\n"
                    "- **Departments** - Learn about our specialties\n"
                    "- **Appointments** - How to book a visit\n"
                    "- **Emergency** - Emergency services info\n"
                    "- **Insurance** - Coverage and claims\n"
                    "- **Billing** - Payment and costs\n"
                    "- **Admission** - Room types and rates\n"
                    "- **Reports** - Lab results and reports\n\n"
                    "Try asking about any of these topics!",
        'category': 'unknown',
        'confidence': 0
    }


# --- Patient Risk Analysis ---
def analyze_patient_risk(patient_data):
    """Analyze patient risk based on health parameters"""
    risk_score = 0
    risk_factors = []
    recommendations = []

    # Age risk
    age = patient_data.get('age', 0)
    if age > 70:
        risk_score += 25
        risk_factors.append({'factor': 'Advanced Age', 'impact': 'High', 'details': f'Patient is {age} years old'})
    elif age > 55:
        risk_score += 15
        risk_factors.append({'factor': 'Senior Age', 'impact': 'Moderate', 'details': f'Patient is {age} years old'})
    elif age < 5:
        risk_score += 15
        risk_factors.append({'factor': 'Pediatric Age', 'impact': 'Moderate', 'details': f'Patient is {age} years old'})

    # Blood pressure
    bp_systolic = patient_data.get('bp_systolic', 120)
    bp_diastolic = patient_data.get('bp_diastolic', 80)
    if bp_systolic >= 180 or bp_diastolic >= 120:
        risk_score += 30
        risk_factors.append({'factor': 'Hypertensive Crisis', 'impact': 'Critical', 'details': f'BP: {bp_systolic}/{bp_diastolic}'})
        recommendations.append('Immediate medical attention for blood pressure management')
    elif bp_systolic >= 140 or bp_diastolic >= 90:
        risk_score += 20
        risk_factors.append({'factor': 'High Blood Pressure', 'impact': 'High', 'details': f'BP: {bp_systolic}/{bp_diastolic}'})
        recommendations.append('Regular BP monitoring and medication review')

    # Blood sugar
    blood_sugar = patient_data.get('blood_sugar', 100)
    if blood_sugar > 250:
        risk_score += 25
        risk_factors.append({'factor': 'Severe Hyperglycemia', 'impact': 'Critical', 'details': f'Blood Sugar: {blood_sugar} mg/dL'})
        recommendations.append('Urgent diabetes management and insulin adjustment')
    elif blood_sugar > 180:
        risk_score += 15
        risk_factors.append({'factor': 'High Blood Sugar', 'impact': 'High', 'details': f'Blood Sugar: {blood_sugar} mg/dL'})
        recommendations.append('Dietary modifications and medication review')

    # Heart rate
    heart_rate = patient_data.get('heart_rate', 72)
    if heart_rate > 120 or heart_rate < 50:
        risk_score += 20
        risk_factors.append({'factor': 'Abnormal Heart Rate', 'impact': 'High', 'details': f'HR: {heart_rate} bpm'})
        recommendations.append('Cardiac evaluation recommended')

    # Oxygen saturation
    spo2 = patient_data.get('spo2', 98)
    if spo2 < 90:
        risk_score += 30
        risk_factors.append({'factor': 'Low Oxygen Saturation', 'impact': 'Critical', 'details': f'SpO2: {spo2}%'})
        recommendations.append('Immediate oxygen therapy and respiratory assessment')
    elif spo2 < 94:
        risk_score += 15
        risk_factors.append({'factor': 'Reduced Oxygen', 'impact': 'Moderate', 'details': f'SpO2: {spo2}%'})

    # BMI
    bmi = patient_data.get('bmi', 22)
    if bmi > 35:
        risk_score += 15
        risk_factors.append({'factor': 'Severe Obesity', 'impact': 'High', 'details': f'BMI: {bmi}'})
        recommendations.append('Weight management program and nutritional counseling')
    elif bmi > 30:
        risk_score += 10
        risk_factors.append({'factor': 'Obesity', 'impact': 'Moderate', 'details': f'BMI: {bmi}'})
    elif bmi < 18.5:
        risk_score += 10
        risk_factors.append({'factor': 'Underweight', 'impact': 'Moderate', 'details': f'BMI: {bmi}'})

    # Smoking
    if patient_data.get('smoker', False):
        risk_score += 15
        risk_factors.append({'factor': 'Tobacco Use', 'impact': 'High', 'details': 'Active smoker'})
        recommendations.append('Smoking cessation program recommended')

    # Pre-existing conditions
    conditions = patient_data.get('conditions', [])
    high_risk_conditions = ['diabetes', 'heart disease', 'cancer', 'kidney disease', 'liver disease', 'copd']
    for condition in conditions:
        if condition.lower() in high_risk_conditions:
            risk_score += 10
            risk_factors.append({'factor': f'Pre-existing: {condition}', 'impact': 'Moderate', 'details': f'Has {condition}'})

    # Cap risk score
    risk_score = min(100, risk_score)

    # Determine risk level
    if risk_score >= 75:
        risk_level = 'Critical'
        risk_color = '#ef4444'
    elif risk_score >= 50:
        risk_level = 'High'
        risk_color = '#f97316'
    elif risk_score >= 25:
        risk_level = 'Moderate'
        risk_color = '#eab308'
    else:
        risk_level = 'Low'
        risk_color = '#22c55e'

    if not recommendations:
        recommendations.append('Continue regular health check-ups')
        recommendations.append('Maintain a healthy lifestyle with balanced diet and exercise')

    return {
        'risk_score': risk_score,
        'risk_level': risk_level,
        'risk_color': risk_color,
        'risk_factors': risk_factors,
        'recommendations': recommendations,
        'summary': f"Patient has a {risk_level} risk level with a score of {risk_score}/100. "
                   f"{'Immediate medical attention is recommended.' if risk_score >= 75 else ''}"
                   f"{'Close monitoring advised.' if 50 <= risk_score < 75 else ''}"
                   f"{'Regular check-ups recommended.' if risk_score < 50 else ''}"
    }


# --- AI Dashboard Insights ---
def get_ai_insights(stats):
    """Generate AI-powered insights for the dashboard"""
    insights = []

    total_patients = stats.get('total_patients', 0)
    total_doctors = stats.get('total_doctors', 0)
    total_appointments = stats.get('total_appointments', 0)
    total_revenue = stats.get('total_revenue', 0)
    pending_appointments = stats.get('pending_appointments', 0)

    # Patient-doctor ratio
    if total_doctors > 0:
        ratio = total_patients / total_doctors
        if ratio > 50:
            insights.append({
                'type': 'warning',
                'icon': 'fa-exclamation-triangle',
                'title': 'High Patient-Doctor Ratio',
                'message': f'Current ratio is {ratio:.0f}:1. Consider hiring additional medical staff.',
                'metric': f'{ratio:.0f}:1'
            })
        else:
            insights.append({
                'type': 'success',
                'icon': 'fa-check-circle',
                'title': 'Optimal Staffing',
                'message': f'Patient-doctor ratio of {ratio:.0f}:1 is within healthy range.',
                'metric': f'{ratio:.0f}:1'
            })

    # Appointment completion
    if total_appointments > 0:
        completion_rate = ((total_appointments - pending_appointments) / total_appointments) * 100
        insights.append({
            'type': 'info' if completion_rate > 70 else 'warning',
            'icon': 'fa-chart-line',
            'title': 'Appointment Completion Rate',
            'message': f'{completion_rate:.0f}% of appointments completed. {"Keep up the great work!" if completion_rate > 80 else "Consider follow-up with no-show patients."}',
            'metric': f'{completion_rate:.0f}%'
        })

    # Revenue insight
    if total_revenue > 0:
        avg_revenue_per_patient = total_revenue / max(total_patients, 1)
        insights.append({
            'type': 'info',
            'icon': 'fa-dollar-sign',
            'title': 'Revenue per Patient',
            'message': f'Average revenue per patient is ${avg_revenue_per_patient:,.0f}.',
            'metric': f'${avg_revenue_per_patient:,.0f}'
        })

    # General insights
    insights.append({
        'type': 'info',
        'icon': 'fa-lightbulb',
        'title': 'AI Recommendation',
        'message': 'Based on current trends, peak hours are between 10 AM - 12 PM. Consider distributing appointments more evenly.',
        'metric': '10-12 AM'
    })

    return insights
