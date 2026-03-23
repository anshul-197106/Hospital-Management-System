from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # admin, doctor, staff
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(256), default='default.png')
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'phone': self.phone,
            'is_active': self.is_active_user,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    blood_group = db.Column(db.String(5))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(20))
    emergency_contact_name = db.Column(db.String(100))
    medical_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    insurance_provider = db.Column(db.String(100))
    insurance_id = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')  # active, discharged, critical
    admitted_date = db.Column(db.DateTime, default=datetime.utcnow)
    discharged_date = db.Column(db.DateTime)
    ward = db.Column(db.String(50))
    bed_number = db.Column(db.String(10))
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    bills = db.relationship('Bill', backref='patient', lazy=True)
    reports = db.relationship('MedicalReport', backref='patient', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'blood_group': self.blood_group,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'emergency_contact': self.emergency_contact,
            'emergency_contact_name': self.emergency_contact_name,
            'medical_history': self.medical_history,
            'allergies': self.allergies,
            'current_medications': self.current_medications,
            'insurance_provider': self.insurance_provider,
            'insurance_id': self.insurance_id,
            'status': self.status,
            'admitted_date': self.admitted_date.isoformat() if self.admitted_date else None,
            'discharged_date': self.discharged_date.isoformat() if self.discharged_date else None,
            'ward': self.ward,
            'bed_number': self.bed_number,
            'assigned_doctor_id': self.assigned_doctor_id,
            'assigned_doctor': self.assigned_doctor.full_name if self.assigned_doctor else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'age': self._calculate_age()
        }

    def _calculate_age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    full_name = db.Column(db.String(150), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer, default=0)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    consultation_fee = db.Column(db.Float, default=0.0)
    available_days = db.Column(db.String(200))  # JSON string
    available_time_start = db.Column(db.String(10))
    available_time_end = db.Column(db.String(10))
    department = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')  # active, on_leave, inactive
    max_patients_per_day = db.Column(db.Integer, default=20)
    rating = db.Column(db.Float, default=4.5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patients = db.relationship('Patient', backref='assigned_doctor', lazy=True)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'specialization': self.specialization,
            'qualification': self.qualification,
            'experience_years': self.experience_years,
            'phone': self.phone,
            'email': self.email,
            'consultation_fee': self.consultation_fee,
            'available_days': self.available_days,
            'available_time_start': self.available_time_start,
            'available_time_end': self.available_time_end,
            'department': self.department,
            'status': self.status,
            'max_patients_per_day': self.max_patients_per_day,
            'rating': self.rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_patients': len(self.patients),
            'total_appointments': len(self.appointments)
        }


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(10), nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    type = db.Column(db.String(50), default='consultation')  # consultation, follow_up, emergency, surgery
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, no_show
    symptoms = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    priority = db.Column(db.String(10), default='normal')  # low, normal, high, urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.first_name + ' ' + self.patient.last_name if self.patient else None,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.full_name if self.doctor else None,
            'doctor_specialization': self.doctor.specialization if self.doctor else None,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'appointment_time': self.appointment_time,
            'duration_minutes': self.duration_minutes,
            'type': self.type,
            'status': self.status,
            'symptoms': self.symptoms,
            'diagnosis': self.diagnosis,
            'prescription': self.prescription,
            'notes': self.notes,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Bill(db.Model):
    __tablename__ = 'bills'
    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    bill_date = db.Column(db.DateTime, default=datetime.utcnow)
    consultation_fee = db.Column(db.Float, default=0.0)
    medicine_charges = db.Column(db.Float, default=0.0)
    lab_charges = db.Column(db.Float, default=0.0)
    room_charges = db.Column(db.Float, default=0.0)
    surgery_charges = db.Column(db.Float, default=0.0)
    other_charges = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    tax_percentage = db.Column(db.Float, default=10.0)
    total_amount = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default='pending')  # pending, partial, paid, overdue
    payment_method = db.Column(db.String(30))  # cash, card, insurance, upi
    insurance_claim = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        subtotal = (self.consultation_fee + self.medicine_charges + self.lab_charges +
                    self.room_charges + self.surgery_charges + self.other_charges)
        discount_amount = subtotal * (self.discount / 100) if self.discount else 0
        tax_amount = (subtotal - discount_amount) * (self.tax_percentage / 100)
        return {
            'id': self.id,
            'bill_id': self.bill_id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.first_name + ' ' + self.patient.last_name if self.patient else None,
            'bill_date': self.bill_date.isoformat() if self.bill_date else None,
            'consultation_fee': self.consultation_fee,
            'medicine_charges': self.medicine_charges,
            'lab_charges': self.lab_charges,
            'room_charges': self.room_charges,
            'surgery_charges': self.surgery_charges,
            'other_charges': self.other_charges,
            'subtotal': subtotal,
            'discount': self.discount,
            'discount_amount': discount_amount,
            'tax_percentage': self.tax_percentage,
            'tax_amount': tax_amount,
            'total_amount': self.total_amount,
            'paid_amount': self.paid_amount,
            'balance': self.total_amount - self.paid_amount,
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'insurance_claim': self.insurance_claim,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MedicalReport(db.Model):
    __tablename__ = 'medical_reports'
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # blood_test, x_ray, mri, ct_scan, etc
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(256))
    file_name = db.Column(db.String(200))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    status = db.Column(db.String(20), default='pending')  # pending, completed, reviewed
    results = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'report_id': self.report_id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.first_name + ' ' + self.patient.last_name if self.patient else None,
            'report_type': self.report_type,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'status': self.status,
            'results': self.results,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(30), default='info')  # info, warning, success, danger
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'link': self.link,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'time_ago': self._time_ago()
        }

    def _time_ago(self):
        diff = datetime.utcnow() - self.created_at
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = diff.seconds // 60
        if minutes > 0:
            return f"{minutes}m ago"
        return "Just now"


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50))  # patient, doctor, appointment, bill
    entity_id = db.Column(db.Integer)
    description = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='activity_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_role': self.user.role if self.user else None,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'description': self.description,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
