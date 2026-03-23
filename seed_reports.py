from app import app, db, MedicalReport, Patient
from datetime import datetime, timedelta
import random

with app.app_context():
    patients = Patient.query.all()
    if not patients:
        print("No patients found. Run initialize database first.")
        exit()
        
    report_titles = [
        ('Blood Test Report', 'blood_test', 'Complete blood count and metabolic panel results.'),
        ('Chest X-Ray', 'x_ray', 'Routine chest imaging for physical examination.'),
        ('Brain MRI', 'mri', 'Detailed scan of brain structure and vessels.'),
        ('Discharge Summary', 'discharge_summary', 'Final summary of treatment and follow-up instructions.'),
        ('Cardiology Report', 'ecg', 'Electrocardiogram analysis for heart rhythms.'),
    ]
    
    for i in range(20):
        p = random.choice(patients)
        title, rtype, desc = random.choice(report_titles)
        report = MedicalReport(
            report_id=f'REP{40000+i}',
            patient_id=p.id,
            report_type=rtype,
            title=f"{p.last_name} - {title}",
            description=desc,
            status=random.choice(['completed', 'completed', 'reviewed']),
            results="Normal results across all tested parameters. No immediate action required.",
            created_at=datetime.now() - timedelta(days=random.randint(1, 45))
        )
        db.session.add(report)
    
    db.session.commit()
    print(f"✅ Successfully seeded {MedicalReport.query.count()} medical reports!")
