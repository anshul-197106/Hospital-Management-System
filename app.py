import os
import csv
import io
import random
import uuid
from datetime import datetime, date, timedelta
from functools import wraps

from flask import (Flask, render_template, request, jsonify, redirect,
                   url_for, flash, session, send_file, make_response)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.utils import secure_filename

from config import Config
from models import (db, User, Patient, Doctor, Appointment, Bill,
                    MedicalReport, Notification, ActivityLog)
from ai_module import (predict_disease, predict_appointment_load,
                       chatbot_respond, analyze_patient_risk, get_ai_insights)

# --- App Initialization ---
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_id(prefix=''):
    return f"{prefix}{random.randint(100000, 999999)}"


def log_activity(action, entity_type=None, entity_id=None, description=None):
    """Log user activity"""
    try:
        log = ActivityLog(
            user_id=current_user.id if current_user.is_authenticated else 0,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


def create_notification(user_id, title, message, notif_type='info', link=None):
    """Create a notification"""
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            link=link
        )
        db.session.add(notif)
        db.session.commit()
    except Exception:
        db.session.rollback()


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# --- Initialize Database ---
def init_db():
    with app.app_context():
        os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()

        # Create default admin if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@medcare.com',
                role='admin',
                full_name='System Administrator',
                phone='+1-800-0000'
            )
            admin.set_password('admin123')
            db.session.add(admin)

            # Seed demo data
            _seed_demo_data()
            db.session.commit()
            print("✅ Database initialized with demo data!")


def _seed_demo_data():
    """Seed database with demo data for showcase"""
    # Create doctors
    specializations = [
        ('Dr. Sarah Johnson', 'Cardiology', 'MD, FACC', 15),
        ('Dr. Michael Chen', 'Neurology', 'MD, PhD', 12),
        ('Dr. Emily Williams', 'Pediatrics', 'MD, FAAP', 8),
        ('Dr. James Wilson', 'Orthopedics', 'MD, FAAOS', 20),
        ('Dr. Maria Garcia', 'Dermatology', 'MD, FAAD', 10),
        ('Dr. Robert Taylor', 'General Medicine', 'MD, MBBS', 18),
        ('Dr. Lisa Anderson', 'Gynecology', 'MD, FACOG', 14),
        ('Dr. David Brown', 'Pulmonology', 'MD, FCCP', 11),
    ]

    doctors = []
    for i, (name, spec, qual, exp) in enumerate(specializations, 1):
        doc_user = User(
            username=name.lower().replace(' ', '.').replace('dr.', 'dr'),
            email=f"doctor{i}@medcare.com",
            role='doctor',
            full_name=name,
            phone=f'+1-800-{1000+i}'
        )
        doc_user.set_password('doctor123')
        db.session.add(doc_user)
        db.session.flush()

        doctor = Doctor(
            doctor_id=f'DOC{1000+i}',
            user_id=doc_user.id,
            full_name=name,
            specialization=spec,
            qualification=qual,
            experience_years=exp,
            phone=f'+1-800-{1000+i}',
            email=f"doctor{i}@medcare.com",
            consultation_fee=random.choice([300, 500, 800, 1000, 1200]),
            available_days='Mon,Tue,Wed,Thu,Fri',
            available_time_start='09:00',
            available_time_end='17:00',
            department=spec,
            status='active',
            max_patients_per_day=random.randint(15, 25),
            rating=round(random.uniform(4.0, 5.0), 1)
        )
        db.session.add(doctor)
        doctors.append(doctor)

    db.session.flush()

    # Create staff user
    staff = User(
        username='staff',
        email='staff@medcare.com',
        role='staff',
        full_name='John Staff',
        phone='+1-800-2000'
    )
    staff.set_password('staff123')
    db.session.add(staff)

    # Create patients
    patient_names = [
        ('Alice', 'Martin', 'F'), ('Bob', 'Thompson', 'M'), ('Carol', 'Davis', 'F'),
        ('Daniel', 'Miller', 'M'), ('Eva', 'Rodriguez', 'F'), ('Frank', 'Lee', 'M'),
        ('Grace', 'Walker', 'F'), ('Henry', 'Hall', 'M'), ('Iris', 'Allen', 'F'),
        ('Jack', 'Young', 'M'), ('Karen', 'King', 'F'), ('Leo', 'Wright', 'M'),
        ('Mary', 'Scott', 'F'), ('Nathan', 'Green', 'M'), ('Olivia', 'Baker', 'F'),
        ('Peter', 'Nelson', 'M'), ('Quinn', 'Carter', 'F'), ('Ryan', 'Mitchell', 'M'),
        ('Sofia', 'Perez', 'F'), ('Thomas', 'Roberts', 'M'),
    ]

    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    statuses = ['active', 'active', 'active', 'discharged', 'active']
    wards = ['General Ward A', 'General Ward B', 'ICU', 'Pediatrics', 'Cardiology', 'Emergency']

    patients = []
    for i, (fn, ln, gender) in enumerate(patient_names, 1):
        dob = date(random.randint(1955, 2010), random.randint(1, 12), random.randint(1, 28))
        admitted = datetime.now() - timedelta(days=random.randint(0, 60))
        p = Patient(
            patient_id=f'PAT{10000+i}',
            first_name=fn,
            last_name=ln,
            date_of_birth=dob,
            gender=gender,
            blood_group=random.choice(blood_groups),
            phone=f'+1-555-{1000+i}',
            email=f'{fn.lower()}.{ln.lower()}@email.com',
            address=f'{random.randint(100, 9999)} Medical Ave, Suite {random.randint(1,100)}',
            emergency_contact=f'+1-555-{5000+i}',
            emergency_contact_name=f'{random.choice(["Spouse", "Parent", "Sibling"])} of {fn}',
            medical_history=random.choice(['None', 'Diabetes', 'Hypertension', 'Asthma', 'Heart Disease', '']),
            allergies=random.choice(['None', 'Penicillin', 'Sulfa', 'Latex', 'Peanuts', '']),
            status=random.choice(statuses),
            admitted_date=admitted,
            ward=random.choice(wards),
            bed_number=f'{random.choice(["A","B","C"])}{random.randint(1,20)}',
            assigned_doctor_id=random.choice(doctors).id if doctors else None
        )
        db.session.add(p)
        patients.append(p)

    db.session.flush()

    # Create appointments
    appt_types = ['consultation', 'follow_up', 'emergency', 'surgery']
    appt_statuses = ['scheduled', 'completed', 'completed', 'completed', 'cancelled']
    for i in range(30):
        appt_date = date.today() + timedelta(days=random.randint(-15, 15))
        a = Appointment(
            appointment_id=f'APT{20000+i}',
            patient_id=random.choice(patients).id,
            doctor_id=random.choice(doctors).id,
            appointment_date=appt_date,
            appointment_time=f'{random.randint(9,16)}:{random.choice(["00","15","30","45"])}',
            duration_minutes=random.choice([15, 30, 45, 60]),
            type=random.choice(appt_types),
            status=random.choice(appt_statuses),
            symptoms=random.choice(['Headache', 'Fever', 'Chest pain', 'Back pain', 'Cough', 'Fatigue', '']),
            priority=random.choice(['low', 'normal', 'normal', 'high', 'urgent'])
        )
        db.session.add(a)

    # Create bills
    pay_statuses = ['paid', 'paid', 'paid', 'pending', 'partial']
    for i in range(15):
        subtotal_parts = {
            'consultation': random.choice([300, 500, 800, 1000]),
            'medicine': random.randint(200, 2000),
            'lab': random.randint(500, 3000),
            'room': random.randint(0, 5000),
            'surgery': random.choice([0, 0, 0, 15000, 25000, 50000]),
            'other': random.randint(0, 500)
        }
        subtotal = sum(subtotal_parts.values())
        discount = random.choice([0, 5, 10])
        discount_amt = subtotal * discount / 100
        tax = (subtotal - discount_amt) * 0.1
        total = subtotal - discount_amt + tax
        paid = total if random.random() > 0.3 else total * random.uniform(0.3, 0.9)

        b = Bill(
            bill_id=f'BILL{30000+i}',
            patient_id=random.choice(patients).id,
            consultation_fee=subtotal_parts['consultation'],
            medicine_charges=subtotal_parts['medicine'],
            lab_charges=subtotal_parts['lab'],
            room_charges=subtotal_parts['room'],
            surgery_charges=subtotal_parts['surgery'],
            other_charges=subtotal_parts['other'],
            discount=discount,
            tax_percentage=10,
            total_amount=round(total, 2),
            paid_amount=round(paid, 2),
            payment_status=random.choice(pay_statuses),
            payment_method=random.choice(['cash', 'card', 'insurance', 'upi']),
            bill_date=datetime.now() - timedelta(days=random.randint(0, 30))
        )
        db.session.add(b)

    # Create dummy medical reports
    report_titles = [
        ('Blood Test Report', 'blood_test', 'Complete blood count and metabolic panel results.'),
        ('Chest X-Ray', 'x_ray', 'Routine chest imaging for physical examination.'),
        ('Brain MRI', 'mri', 'Detailed scan of brain structure and vessels.'),
        ('Discharge Summary', 'discharge_summary', 'Final summary of treatment and follow-up instructions.'),
        ('Billing Statement', 'billing_report', 'Itemized billing statement for recent stay.'),
        ('Cardiology Report', 'ecg', 'Electrocardiogram analysis for heart rhythms.'),
    ]
    
    for i in range(12):
        p = random.choice(patients)
        title, rtype, desc = random.choice(report_titles)
        report = MedicalReport(
            report_id=f'REP{40000+i}',
            patient_id=p.id,
            report_type=rtype,
            title=f"{p.last_name} - {title}",
            description=desc,
            status=random.choice(['completed', 'completed', 'reviewed']),
            results="Normal results across all tested parameters.",
            created_at=datetime.now() - timedelta(days=random.randint(1, 45))
        )
        db.session.add(report)


# ========================= PAGE ROUTES =========================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_activity('login', 'user', user.id, f'{user.full_name} logged in')
            flash('Welcome back!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            role='staff'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        log_activity('register', 'user', user.id, f'New user registered: {full_name}')
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    log_activity('logout', 'user', current_user.id, f'{current_user.full_name} logged out')
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/patients')
@login_required
def patients():
    return render_template('patients.html')


@app.route('/doctors')
@login_required
def doctors():
    return render_template('doctors.html')


@app.route('/appointments')
@login_required
def appointments():
    return render_template('appointments.html')


@app.route('/billing')
@login_required
def billing():
    return render_template('billing.html')


@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')


@app.route('/ai-features')
@login_required
def ai_features():
    return render_template('ai_features.html')


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/activity-logs')
@login_required
@role_required('admin')
def activity_logs():
    return render_template('activity_logs.html')


# ========================= API ROUTES =========================

# --- Dashboard Stats ---
@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.filter_by(status='active').count()
    total_appointments = Appointment.query.count()
    today_appointments = Appointment.query.filter(
        Appointment.appointment_date == date.today()
    ).count()
    pending_appointments = Appointment.query.filter_by(status='scheduled').count()
    total_revenue = db.session.query(db.func.sum(Bill.paid_amount)).scalar() or 0
    active_patients = Patient.query.filter_by(status='active').count()
    critical_patients = Patient.query.filter_by(status='critical').count()

    # Chart data - last 7 days
    chart_labels = []
    patient_data = []
    appointment_data = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        chart_labels.append(d.strftime('%b %d'))
        patient_data.append(Patient.query.filter(
            db.func.date(Patient.admitted_date) == d
        ).count())
        appointment_data.append(Appointment.query.filter(
            Appointment.appointment_date == d
        ).count())

    # Revenue chart - last 6 months
    revenue_labels = []
    revenue_data = []
    for i in range(5, -1, -1):
        d = date.today() - timedelta(days=30*i)
        month_label = d.strftime('%b')
        revenue_labels.append(month_label)
        month_start = d.replace(day=1)
        if i > 0:
            month_end = (d + timedelta(days=30)).replace(day=1)
        else:
            month_end = date.today()
        rev = db.session.query(db.func.sum(Bill.paid_amount)).filter(
            db.func.date(Bill.bill_date) >= month_start,
            db.func.date(Bill.bill_date) < month_end
        ).scalar() or 0
        revenue_data.append(float(rev))

    # Doctor workload (Optimized single query to fix N+1 performance issue)
    doctor_workload = []
    workload_query = db.session.query(
        Doctor.id, Doctor.full_name, Doctor.specialization, db.func.count(Appointment.id)
    ).outerjoin(Appointment, db.and_(Appointment.doctor_id == Doctor.id, Appointment.status != 'cancelled'))\
     .filter(Doctor.status == 'active')\
     .group_by(Doctor.id).all()
    
    for doc_id, doc_name, doc_spec, appt_count in workload_query:
        doctor_workload.append({
            'name': doc_name.replace('Dr. ', ''),
            'appointments': appt_count,
            'specialization': doc_spec
        })
    doctor_workload.sort(key=lambda x: x['appointments'], reverse=True)

    # Recent appointments
    recent_appointments = Appointment.query.order_by(
        Appointment.created_at.desc()
    ).limit(5).all()

    stats = {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'total_revenue': float(total_revenue),
        'active_patients': active_patients,
        'critical_patients': critical_patients,
        'chart_labels': chart_labels,
        'patient_data': patient_data,
        'appointment_data': appointment_data,
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'doctor_workload': doctor_workload[:8],
        'recent_appointments': [a.to_dict() for a in recent_appointments],
        'ai_insights': get_ai_insights({
            'total_patients': total_patients,
            'total_doctors': total_doctors,
            'total_appointments': total_appointments,
            'total_revenue': float(total_revenue),
            'pending_appointments': pending_appointments
        })
    }
    return jsonify(stats)


# --- Patient CRUD ---
@app.route('/api/patients', methods=['GET'])
@login_required
def api_get_patients():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')

    query = Patient.query

    if search:
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Patient.patient_id.ilike(f'%{search}%'),
                Patient.phone.ilike(f'%{search}%'),
                Patient.email.ilike(f'%{search}%')
            )
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    # Sorting
    sort_column = getattr(Patient, sort_by, Patient.created_at)
    if sort_order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'patients': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@app.route('/api/patients', methods=['POST'])
@login_required
def api_create_patient():
    data = request.get_json()

    try:
        dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
    except (ValueError, KeyError):
        return jsonify({'error': 'Invalid date of birth'}), 400

    patient = Patient(
        patient_id=generate_id('PAT'),
        first_name=data['first_name'],
        last_name=data['last_name'],
        date_of_birth=dob,
        gender=data['gender'],
        blood_group=data.get('blood_group'),
        phone=data['phone'],
        email=data.get('email'),
        address=data.get('address'),
        emergency_contact=data.get('emergency_contact'),
        emergency_contact_name=data.get('emergency_contact_name'),
        medical_history=data.get('medical_history'),
        allergies=data.get('allergies'),
        current_medications=data.get('current_medications'),
        insurance_provider=data.get('insurance_provider'),
        insurance_id=data.get('insurance_id'),
        ward=data.get('ward'),
        bed_number=data.get('bed_number'),
        assigned_doctor_id=data.get('assigned_doctor_id'),
        status=data.get('status', 'active')
    )

    db.session.add(patient)
    db.session.commit()

    log_activity('create', 'patient', patient.id, f'Patient {patient.first_name} {patient.last_name} registered')
    create_notification(current_user.id, 'New Patient Registered',
                        f'{patient.first_name} {patient.last_name} has been registered.',
                        'success', '/patients')

    return jsonify({'message': 'Patient created successfully', 'patient': patient.to_dict()}), 201


@app.route('/api/patients/<int:patient_id>', methods=['GET'])
@login_required
def api_get_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return jsonify(patient.to_dict())


@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
@login_required
def api_update_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    data = request.get_json()

    for field in ['first_name', 'last_name', 'gender', 'blood_group', 'phone', 'email',
                  'address', 'emergency_contact', 'emergency_contact_name', 'medical_history',
                  'allergies', 'current_medications', 'insurance_provider', 'insurance_id',
                  'ward', 'bed_number', 'status', 'assigned_doctor_id']:
        if field in data:
            setattr(patient, field, data[field])

    if 'date_of_birth' in data:
        try:
            patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

    db.session.commit()
    log_activity('update', 'patient', patient.id, f'Patient {patient.first_name} {patient.last_name} updated')

    return jsonify({'message': 'Patient updated successfully', 'patient': patient.to_dict()})


@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
@login_required
def api_delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    name = f"{patient.first_name} {patient.last_name}"

    # Delete related records
    Appointment.query.filter_by(patient_id=patient_id).delete()
    Bill.query.filter_by(patient_id=patient_id).delete()
    MedicalReport.query.filter_by(patient_id=patient_id).delete()

    db.session.delete(patient)
    db.session.commit()

    log_activity('delete', 'patient', patient_id, f'Patient {name} deleted')
    return jsonify({'message': f'Patient {name} deleted successfully'})


# --- Doctor CRUD ---
@app.route('/api/doctors', methods=['GET'])
@login_required
def api_get_doctors():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    specialization = request.args.get('specialization', '').strip()

    query = Doctor.query

    if search:
        query = query.filter(
            db.or_(
                Doctor.full_name.ilike(f'%{search}%'),
                Doctor.doctor_id.ilike(f'%{search}%'),
                Doctor.specialization.ilike(f'%{search}%')
            )
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    if specialization:
        query = query.filter_by(specialization=specialization)

    pagination = query.order_by(Doctor.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'doctors': [d.to_dict() for d in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@app.route('/api/doctors', methods=['POST'])
@login_required
@role_required('admin')
def api_create_doctor():
    data = request.get_json()

    doctor = Doctor(
        doctor_id=generate_id('DOC'),
        full_name=data['full_name'],
        specialization=data['specialization'],
        qualification=data.get('qualification'),
        experience_years=data.get('experience_years', 0),
        phone=data['phone'],
        email=data['email'],
        consultation_fee=data.get('consultation_fee', 0),
        available_days=data.get('available_days', 'Mon,Tue,Wed,Thu,Fri'),
        available_time_start=data.get('available_time_start', '09:00'),
        available_time_end=data.get('available_time_end', '17:00'),
        department=data.get('department', data['specialization']),
        max_patients_per_day=data.get('max_patients_per_day', 20)
    )

    db.session.add(doctor)
    db.session.commit()

    log_activity('create', 'doctor', doctor.id, f'Doctor {doctor.full_name} added')
    return jsonify({'message': 'Doctor added successfully', 'doctor': doctor.to_dict()}), 201


@app.route('/api/doctors/<int:doctor_id>', methods=['PUT'])
@login_required
def api_update_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    # Check permissions: Admin can edit all, Doctor can edit self
    if current_user.role != 'admin':
        if current_user.role == 'doctor':
            # Check if this doctor record belongs to the current user
            if doctor.user_id != current_user.id:
                return jsonify({'error': 'You can only edit your own profile.'}), 403
        else:
            return jsonify({'error': 'Permission denied.'}), 403

    data = request.get_json()
    
    # Non-admins cannot change their own status or fee (simplified rule)
    if current_user.role != 'admin':
        for restricted in ['status', 'consultation_fee', 'doctor_id', 'user_id']:
            if restricted in data:
                del data[restricted]

    for field in ['full_name', 'specialization', 'qualification', 'experience_years',
                  'phone', 'email', 'consultation_fee', 'available_days',
                  'available_time_start', 'available_time_end', 'department',
                  'status', 'max_patients_per_day']:
        if field in data:
            setattr(doctor, field, data[field])

    db.session.commit()
    log_activity('update', 'doctor', doctor.id, f'Doctor {doctor.full_name} updated')
    return jsonify({'message': 'Doctor updated successfully', 'doctor': doctor.to_dict()})


@app.route('/api/doctors/<int:doctor_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def api_delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    name = doctor.full_name
    db.session.delete(doctor)
    db.session.commit()
    log_activity('delete', 'doctor', doctor_id, f'Doctor {name} deleted')
    return jsonify({'message': f'Doctor {name} deleted successfully'})


# --- Appointment CRUD ---
@app.route('/api/appointments', methods=['GET'])
@login_required
def api_get_appointments():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    date_filter = request.args.get('date', '').strip()

    query = Appointment.query

    if search:
        query = query.join(Patient).join(Doctor).filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Doctor.full_name.ilike(f'%{search}%'),
                Appointment.appointment_id.ilike(f'%{search}%')
            )
        )

    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(Appointment.appointment_date == filter_date)
        except ValueError:
            pass

    pagination = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'appointments': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@app.route('/api/appointments', methods=['POST'])
@login_required
def api_create_appointment():
    data = request.get_json()

    try:
        appt_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
    except (ValueError, KeyError):
        return jsonify({'error': 'Invalid date'}), 400

    appointment = Appointment(
        appointment_id=generate_id('APT'),
        patient_id=data['patient_id'],
        doctor_id=data['doctor_id'],
        appointment_date=appt_date,
        appointment_time=data['appointment_time'],
        duration_minutes=data.get('duration_minutes', 30),
        type=data.get('type', 'consultation'),
        symptoms=data.get('symptoms'),
        notes=data.get('notes'),
        priority=data.get('priority', 'normal')
    )

    db.session.add(appointment)
    db.session.commit()

    log_activity('create', 'appointment', appointment.id, f'Appointment {appointment.appointment_id} booked')

    # Notify
    patient = Patient.query.get(data['patient_id'])
    doctor = Doctor.query.get(data['doctor_id'])
    if patient and doctor:
        create_notification(current_user.id, 'Appointment Booked',
                            f'Appointment for {patient.first_name} {patient.last_name} with {doctor.full_name} on {appt_date}',
                            'success', '/appointments')

    return jsonify({'message': 'Appointment booked successfully', 'appointment': appointment.to_dict()}), 201


@app.route('/api/appointments/<int:appt_id>', methods=['PUT'])
@login_required
def api_update_appointment(appt_id):
    appointment = Appointment.query.get_or_404(appt_id)
    data = request.get_json()

    for field in ['appointment_time', 'duration_minutes', 'type', 'status',
                  'symptoms', 'diagnosis', 'prescription', 'notes', 'priority']:
        if field in data:
            setattr(appointment, field, data[field])

    if 'appointment_date' in data:
        try:
            appointment.appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date'}), 400

    db.session.commit()
    log_activity('update', 'appointment', appointment.id, f'Appointment {appointment.appointment_id} updated')
    return jsonify({'message': 'Appointment updated', 'appointment': appointment.to_dict()})


@app.route('/api/appointments/<int:appt_id>', methods=['DELETE'])
@login_required
def api_delete_appointment(appt_id):
    appointment = Appointment.query.get_or_404(appt_id)
    db.session.delete(appointment)
    db.session.commit()
    log_activity('delete', 'appointment', appt_id, 'Appointment deleted')
    return jsonify({'message': 'Appointment deleted successfully'})


# --- Billing CRUD ---
@app.route('/api/bills', methods=['GET'])
@login_required
def api_get_bills():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Bill.query

    if search:
        query = query.join(Patient).filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Bill.bill_id.ilike(f'%{search}%')
            )
        )

    if status_filter:
        query = query.filter(Bill.payment_status == status_filter)

    pagination = query.order_by(Bill.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'bills': [b.to_dict() for b in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@app.route('/api/bills', methods=['POST'])
@login_required
def api_create_bill():
    data = request.get_json()

    consultation = float(data.get('consultation_fee', 0))
    medicine = float(data.get('medicine_charges', 0))
    lab = float(data.get('lab_charges', 0))
    room = float(data.get('room_charges', 0))
    surgery = float(data.get('surgery_charges', 0))
    other = float(data.get('other_charges', 0))
    discount = float(data.get('discount', 0))
    tax_pct = float(data.get('tax_percentage', 10))

    subtotal = consultation + medicine + lab + room + surgery + other
    discount_amt = subtotal * (discount / 100)
    tax_amt = (subtotal - discount_amt) * (tax_pct / 100)
    total = subtotal - discount_amt + tax_amt

    bill = Bill(
        bill_id=generate_id('BILL'),
        patient_id=data['patient_id'],
        consultation_fee=consultation,
        medicine_charges=medicine,
        lab_charges=lab,
        room_charges=room,
        surgery_charges=surgery,
        other_charges=other,
        discount=discount,
        tax_percentage=tax_pct,
        total_amount=round(total, 2),
        paid_amount=float(data.get('paid_amount', 0)),
        payment_status=data.get('payment_status', 'pending'),
        payment_method=data.get('payment_method'),
        insurance_claim=data.get('insurance_claim', False),
        notes=data.get('notes')
    )

    db.session.add(bill)
    db.session.commit()

    log_activity('create', 'bill', bill.id, f'Bill {bill.bill_id} generated - Total: ${total:.2f}')
    return jsonify({'message': 'Bill generated successfully', 'bill': bill.to_dict()}), 201


@app.route('/api/bills/<int:bill_id>', methods=['PUT'])
@login_required
def api_update_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    data = request.get_json()

    for field in ['consultation_fee', 'medicine_charges', 'lab_charges', 'room_charges',
                  'surgery_charges', 'other_charges', 'discount', 'tax_percentage',
                  'paid_amount', 'payment_status', 'payment_method', 'insurance_claim', 'notes']:
        if field in data:
            setattr(bill, field, data[field])

    # Recalculate total
    subtotal = (bill.consultation_fee + bill.medicine_charges + bill.lab_charges +
                bill.room_charges + bill.surgery_charges + bill.other_charges)
    discount_amt = subtotal * (bill.discount / 100)
    tax_amt = (subtotal - discount_amt) * (bill.tax_percentage / 100)
    bill.total_amount = round(subtotal - discount_amt + tax_amt, 2)

    db.session.commit()
    log_activity('update', 'bill', bill.id, f'Bill {bill.bill_id} updated')
    return jsonify({'message': 'Bill updated', 'bill': bill.to_dict()})


@app.route('/api/bills/<int:bill_id>', methods=['DELETE'])
@login_required
def api_delete_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    db.session.delete(bill)
    db.session.commit()
    log_activity('delete', 'bill', bill_id, 'Bill deleted')
    return jsonify({'message': 'Bill deleted successfully'})


# --- Medical Reports ---
@app.route('/api/reports', methods=['GET'])
@login_required
def api_get_reports():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '').strip()

    query = MedicalReport.query

    if search:
        query = query.join(Patient).filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                MedicalReport.report_id.ilike(f'%{search}%'),
                MedicalReport.title.ilike(f'%{search}%')
            )
        )

    pagination = query.order_by(MedicalReport.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'reports': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@app.route('/api/reports', methods=['POST'])
@login_required
def api_create_report():
    patient_id = request.form.get('patient_id')
    report_type = request.form.get('report_type')
    title = request.form.get('title')
    description = request.form.get('description')
    results = request.form.get('results')

    file_path = None
    file_name = None
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            file_name = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4().hex}_{file_name}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(file_path)
            file_path = f"uploads/{unique_name}"

    report = MedicalReport(
        report_id=generate_id('RPT'),
        patient_id=patient_id,
        report_type=report_type,
        title=title,
        description=description,
        file_path=file_path,
        file_name=file_name,
        uploaded_by=current_user.id,
        results=results
    )

    db.session.add(report)
    db.session.commit()

    log_activity('create', 'report', report.id, f'Report {report.report_id} uploaded')
    return jsonify({'message': 'Report uploaded successfully', 'report': report.to_dict()}), 201


@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
@login_required
def api_delete_report(report_id):
    report = MedicalReport.query.get_or_404(report_id)
    if report.file_path:
        full_path = os.path.join(app.root_path, 'static', report.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    db.session.delete(report)
    db.session.commit()
    return jsonify({'message': 'Report deleted successfully'})


@app.route('/api/reports/<int:report_id>/view', methods=['GET'])
@login_required
def api_view_report(report_id):
    report = MedicalReport.query.get_or_404(report_id)
    return render_template('report_view.html', report=report)


# --- Notifications ---
@app.route('/api/notifications', methods=['GET'])
@login_required
def api_get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).limit(20).all()

    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread
    })


@app.route('/api/notifications/read-all', methods=['POST'])
@login_required
def api_read_all_notifications():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All notifications marked as read'})


# --- Activity Logs ---
@app.route('/api/activity-logs', methods=['GET'])
@login_required
@role_required('admin')
def api_get_activity_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    pagination = ActivityLog.query.order_by(
        ActivityLog.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'logs': [l.to_dict() for l in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


# --- Profile ---
@app.route('/api/profile', methods=['GET'])
@login_required
def api_get_profile():
    return jsonify(current_user.to_dict())


@app.route('/api/profile', methods=['PUT'])
@login_required
def api_update_profile():
    data = request.get_json()

    if 'full_name' in data:
        current_user.full_name = data['full_name']
    if 'phone' in data:
        current_user.phone = data['phone']
    if 'email' in data:
        existing = User.query.filter(User.email == data['email'], User.id != current_user.id).first()
        if existing:
            return jsonify({'error': 'Email already in use'}), 400
        current_user.email = data['email']

    if 'current_password' in data and 'new_password' in data:
        if not current_user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        current_user.set_password(data['new_password'])

    db.session.commit()
    log_activity('update', 'profile', current_user.id, 'Profile updated')
    return jsonify({'message': 'Profile updated successfully', 'user': current_user.to_dict()})


# --- AI Endpoints ---
@app.route('/api/ai/predict-disease', methods=['POST'])
@login_required
def api_predict_disease():
    data = request.get_json()
    symptoms = data.get('symptoms', [])
    results = predict_disease(symptoms)
    return jsonify({'predictions': results, 'symptoms_analyzed': len(symptoms)})


@app.route('/api/ai/predict-load', methods=['GET'])
@login_required
def api_predict_load():
    date_str = request.args.get('date')
    result = predict_appointment_load(date_str)
    return jsonify(result)


@app.route('/api/ai/chatbot', methods=['POST'])
@login_required
def api_chatbot():
    data = request.get_json()
    message = data.get('message', '')
    response = chatbot_respond(message)
    return jsonify(response)


@app.route('/api/ai/risk-analysis', methods=['POST'])
@login_required
def api_risk_analysis():
    data = request.get_json()
    result = analyze_patient_risk(data)
    return jsonify(result)


# --- Export ---
@app.route('/api/export/patients')
@login_required
def export_patients_csv():
    patients = Patient.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Patient ID', 'First Name', 'Last Name', 'DOB', 'Gender',
                     'Blood Group', 'Phone', 'Email', 'Status', 'Ward', 'Admitted Date'])

    for p in patients:
        writer.writerow([p.patient_id, p.first_name, p.last_name,
                         p.date_of_birth, p.gender, p.blood_group,
                         p.phone, p.email, p.status, p.ward, p.admitted_date])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=patients_export.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@app.route('/api/export/bills')
@login_required
def export_bills_csv():
    bills = Bill.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Bill ID', 'Patient', 'Total Amount', 'Paid Amount', 'Status',
                     'Payment Method', 'Date'])

    for b in bills:
        patient_name = f"{b.patient.first_name} {b.patient.last_name}" if b.patient else 'N/A'
        writer.writerow([b.bill_id, patient_name, b.total_amount,
                         b.paid_amount, b.payment_status, b.payment_method, b.bill_date])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=bills_export.csv"
    response.headers["Content-type"] = "text/csv"
    return response


# ========================= MAIN =========================
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
