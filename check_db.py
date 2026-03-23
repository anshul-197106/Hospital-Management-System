from app import app, db, MedicalReport, Patient
with app.app_context():
    count = MedicalReport.query.count()
    print(f"Total Medical Reports: {count}")
    reports = MedicalReport.query.all()
    for r in reports:
        print(f"ID: {r.id}, Title: {r.title}, Patient ID: {r.patient_id}")
    
    p_count = Patient.query.count()
    print(f"Total Patients: {p_count}")
