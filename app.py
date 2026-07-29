import os
import werkzeug
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from config import Config
from models import UserModel, PatientModel, ReportModel, SummaryModel
from rag_engine import RAGEngine, MedicalSummarizerEngine, extract_text_from_pdf
from pdf_generator import generate_medical_summary_pdf
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app()

# Initialize AI & RAG Engines
rag_engine = RAGEngine()
summarizer = MedicalSummarizerEngine(rag_engine=rag_engine)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'Doctor')
        
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
            
        existing_user = UserModel.get_by_username(username)
        if existing_user:
            flash('Username already exists.', 'danger')
            return render_template('register.html')
            
        user_id = UserModel.create_user(username, email, password, role)
        session['user_id'] = user_id
        session['username'] = username
        session['role'] = role
        flash('Account created successfully! Welcome to Medical Summarizer.', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = UserModel.get_by_username(username)
        if user and UserModel.verify_password(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user.get('role', 'Doctor')
            flash(f'Welcome back, Dr. {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    patients = PatientModel.get_all()
    reports = ReportModel.get_all()
    
    # Calculate stats
    total_patients = len(patients)
    total_reports = len(reports)
    
    # Attach patient details to recent reports
    recent_reports = reports[:5]
    for r in recent_reports:
        p = PatientModel.get_by_id(r['patient_id'])
        r['patient_name'] = p['name'] if p else 'Unknown'
        r['patient_code'] = p['patient_code'] if p else 'N/A'
        
        # Check summary status
        summ = SummaryModel.get_by_report_id(r['id'])
        r['has_summary'] = summ is not None
        if summ:
            r['risk_level'] = summ['summary_json'].get('risk_level', 'Low')

    return render_template(
        'dashboard.html',
        total_patients=total_patients,
        total_reports=total_reports,
        patients=patients,
        recent_reports=recent_reports
    )


@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age = request.form.get('age', 0)
        gender = request.form.get('gender', 'Other')
        blood_group = request.form.get('blood_group', '')
        medical_history = request.form.get('medical_history', '')
        contact = request.form.get('contact', '')
        
        if not name or not age:
            flash('Patient Name and Age are required.', 'danger')
        else:
            PatientModel.create_patient(name, age, gender, blood_group, medical_history, contact)
            flash(f'Patient {name} added successfully.', 'success')
            return redirect(url_for('patients'))
            
    patients_list = PatientModel.get_all()
    return render_template('patients.html', patients=patients_list)


@app.route('/upload_report', methods=['GET', 'POST'])
@login_required
def upload_report():
    patients_list = PatientModel.get_all()
    
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        report_type = request.form.get('report_type', 'General Medical')
        
        if not patient_id:
            flash('Please select a patient.', 'danger')
            return render_template('upload_report.html', patients=patients_list)
            
        file = request.files.get('report_file')
        manual_text = request.form.get('manual_text', '').strip()
        
        filename = "Manual_Report.txt"
        extracted_text = ""
        saved_path = ""

        if file and file.filename != '':
            filename = werkzeug.utils.secure_filename(file.filename)
            saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(saved_path)
            
            if filename.lower().endswith('.pdf'):
                extracted_text = extract_text_from_pdf(saved_path)
            else:
                with open(saved_path, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted_text = f.read()
        elif manual_text:
            filename = f"Clinical_Notes_{patient_id[:6]}.txt"
            saved_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(saved_path, 'w', encoding='utf-8') as f:
                f.write(manual_text)
            extracted_text = manual_text
        else:
            flash('Please upload a PDF report or paste clinical notes.', 'danger')
            return render_template('upload_report.html', patients=patients_list)

        # Create Report DB Entry
        report_entry = ReportModel.create_report(patient_id, filename, saved_path, extracted_text, report_type)
        report_id = report_entry['id']
        
        # Index document in ChromaDB Vectorstore
        rag_engine.index_report(report_id, extracted_text)
        
        # Generate AI Clinical Summary
        summary_dict = summarizer.generate_clinical_summary(report_id, extracted_text)
        
        # Generate Exportable PDF Summary
        patient_info = PatientModel.get_by_id(patient_id)
        pdf_filename = f"Summary_{report_id[:8]}.pdf"
        generate_medical_summary_pdf(patient_info, report_entry, summary_dict, pdf_filename)
        
        # Save Summary in Database
        SummaryModel.save_summary(report_id, patient_id, summary_dict, pdf_filename)
        
        flash('Medical Report processed and AI Summary generated successfully!', 'success')
        return redirect(url_for('report_detail', report_id=report_id))

    return render_template('upload_report.html', patients=patients_list)


@app.route('/report/<report_id>')
@login_required
def report_detail(report_id):
    report = ReportModel.get_by_id(report_id)
    if not report:
        flash('Report not found.', 'danger')
        return redirect(url_for('dashboard'))
        
    patient = PatientModel.get_by_id(report['patient_id'])
    summary = SummaryModel.get_by_report_id(report_id)
    
    summary_json = summary['summary_json'] if summary else {}
    pdf_filename = summary['pdf_path'] if summary else None

    return render_template(
        'report_detail.html',
        report=report,
        patient=patient,
        summary=summary_json,
        pdf_filename=pdf_filename
    )


@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.json or {}
    report_id = data.get('report_id')
    question = data.get('question', '').strip()
    
    if not report_id or not question:
        return jsonify({'error': 'Report ID and question are required'}), 400
        
    report = ReportModel.get_by_id(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
        
    answer = summarizer.answer_patient_question(report_id, report['extracted_text'], question)
    return jsonify({'answer': answer})


@app.route('/download_summary/<filename>')
@login_required
def download_summary(filename):
    return send_from_directory(app.config['GENERATED_PDF_FOLDER'], filename, as_attachment=True)


def seed_demo_data():
    """Seed demo user, patient, and medical report for testing out of the box."""
    if not UserModel.get_by_username('doctor'):
        UserModel.create_user('doctor', 'doctor@hospital.org', 'doctor123', 'Chief Medical Officer')
        
    patients = PatientModel.get_all()
    if not patients:
        p1 = PatientModel.create_patient(
            name="Eleanor Vance",
            age=48,
            gender="Female",
            blood_group="A+",
            medical_history="Hypertension, Mild Asthma",
            contact="+1 (555) 234-5678"
        )
        
        sample_text = """
ST. JUDE MEDICAL CENTER - CARDIOLOGY & METABOLIC DIVISION
PATIENT EVALUATION & CLINICAL REPORT
Patient Name: Eleanor Vance | Age: 48 | Gender: Female

CLINICAL IMPRESSION & CHIEF COMPLAINT:
Patient presented with episodic exertional dyspnea, mild chest tightness, and fatigue over the past 3 weeks. No acute syncope reported.

VITAL SIGNS & LABORATORY RESULTS:
- Blood Pressure: 138/88 mmHg (Elevated Stage 1)
- Heart Rate: 82 bpm, regular sinus rhythm
- Temperature: 98.6 °F
- Fasting Blood Glucose: 112 mg/dL (Borderline Impaired)
- Total Cholesterol: 224 mg/dL (Elevated)
- LDL Cholesterol: 142 mg/dL | HDL: 46 mg/dL
- ECG: Normal sinus rhythm with mild non-specific ST-segment flattening in inferior leads.
- Echocardiogram: Left ventricular ejection fraction (LVEF) 60%. Mild concentric left ventricular hypertrophy.

DIAGNOSIS:
1. Essential Hypertension (Stage 1) - Suboptimally Controlled.
2. Moderate Hyperlipidemia / Dyslipidemia.
3. Impaired Fasting Glucose (Prediabetes risk).

MEDICATIONS & TREATMENT PLAN:
- Lisinopril 10mg orally once daily in the morning.
- Atorvastatin 20mg orally at bedtime.
- Lifestyle Modification: Low-sodium DASH diet, 150 minutes of aerobic exercise weekly.

RISK FACTORS & WARNINGS:
- Moderate cardiovascular risk over 10-year cohort.
- Patient instructed to seek immediate emergency care if chest pain radiates to arm or jaw, or if severe dyspnea occurs.

RECOMMENDATIONS & FOLLOW-UP:
- Repeat lipid panel and HbA1c in 90 days.
- Home blood pressure logging twice daily (Morning and Evening).
- Follow-up cardiology consultation scheduled in 4 weeks.
"""
        sample_filename = "Cardiology_Evaluation_Eleanor_Vance.txt"
        sample_path = os.path.join(app.config['UPLOAD_FOLDER'], sample_filename)
        with open(sample_path, 'w', encoding='utf-8') as f:
            f.write(sample_text)
            
        r1 = ReportModel.create_report(p1['id'], sample_filename, sample_path, sample_text, "Cardiology & Lab Report")
        rag_engine.index_report(r1['id'], sample_text)
        
        summary_dict = summarizer.generate_clinical_summary(r1['id'], sample_text)
        pdf_fn = f"Summary_{r1['id'][:8]}.pdf"
        generate_medical_summary_pdf(p1, r1, summary_dict, pdf_fn)
        SummaryModel.save_summary(r1['id'], p1['id'], summary_dict, pdf_fn)


# Seed initial demo data
with app.app_context():
    seed_demo_data()

if __name__ == '__main__':
    print("Starting AI Medical Report Summarization Flask Server on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
