import sqlite3
import json
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

try:
    from pymongo import MongoClient
    mongo_client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=2000)
    mongo_client.server_info() # trigger exception if not connected
    db = mongo_client.get_database()
    MONGO_AVAILABLE = True
except Exception:
    MONGO_AVAILABLE = False


def get_sqlite_conn():
    conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_sqlite_db():
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'Doctor',
            created_at TEXT NOT NULL
        )
    ''')
    
    # Patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            patient_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            blood_group TEXT,
            medical_history TEXT,
            contact TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            report_type TEXT DEFAULT 'General Medical',
            extracted_text TEXT,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    # Summaries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS summaries (
            id TEXT PRIMARY KEY,
            report_id TEXT UNIQUE NOT NULL,
            patient_id TEXT NOT NULL,
            summary_json TEXT NOT NULL,
            pdf_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (report_id) REFERENCES reports (id),
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize SQLite tables on module import if MongoDB is unavailable
if not MONGO_AVAILABLE:
    init_sqlite_db()


class UserModel:
    @staticmethod
    def create_user(username, email, password, role='Doctor'):
        password_hash = generate_password_hash(password)
        user_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        if MONGO_AVAILABLE:
            db.users.insert_one({
                '_id': user_id,
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'role': role,
                'created_at': created_at
            })
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (id, username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, username, email, password_hash, role, created_at)
            )
            conn.commit()
            conn.close()
        return user_id

    @staticmethod
    def get_by_username(username):
        if MONGO_AVAILABLE:
            res = db.users.find_one({'username': username})
            if res:
                res['id'] = res['_id']
            return res
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

    @staticmethod
    def get_by_id(user_id):
        if MONGO_AVAILABLE:
            res = db.users.find_one({'_id': user_id})
            if res:
                res['id'] = res['_id']
            return res
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

    @staticmethod
    def verify_password(stored_hash, password):
        return check_password_hash(stored_hash, password)


class PatientModel:
    @staticmethod
    def create_patient(name, age, gender, blood_group='', medical_history='', contact=''):
        patient_id = str(uuid.uuid4())
        patient_code = f"PAT-{str(uuid.uuid4())[:6].upper()}"
        created_at = datetime.utcnow().isoformat()
        
        patient_data = {
            'id': patient_id,
            'patient_code': patient_code,
            'name': name,
            'age': int(age),
            'gender': gender,
            'blood_group': blood_group,
            'medical_history': medical_history,
            'contact': contact,
            'created_at': created_at
        }
        
        if MONGO_AVAILABLE:
            patient_data['_id'] = patient_id
            db.patients.insert_one(patient_data)
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO patients (id, patient_code, name, age, gender, blood_group, medical_history, contact, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (patient_id, patient_code, name, int(age), gender, blood_group, medical_history, contact, created_at)
            )
            conn.commit()
            conn.close()
        return patient_data

    @staticmethod
    def get_all():
        if MONGO_AVAILABLE:
            patients = list(db.patients.find().sort('created_at', -1))
            for p in patients:
                p['id'] = str(p['_id'])
            return patients
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM patients ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(patient_id):
        if MONGO_AVAILABLE:
            res = db.patients.find_one({'_id': patient_id})
            if res:
                res['id'] = str(res['_id'])
            return res
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM patients WHERE id = ?', (patient_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None


class ReportModel:
    @staticmethod
    def create_report(patient_id, filename, file_path, extracted_text, report_type='General Medical'):
        report_id = str(uuid.uuid4())
        uploaded_at = datetime.utcnow().isoformat()
        
        report_data = {
            'id': report_id,
            'patient_id': patient_id,
            'filename': filename,
            'file_path': file_path,
            'report_type': report_type,
            'extracted_text': extracted_text,
            'uploaded_at': uploaded_at
        }
        
        if MONGO_AVAILABLE:
            report_data['_id'] = report_id
            db.reports.insert_one(report_data)
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO reports (id, patient_id, filename, file_path, report_type, extracted_text, uploaded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (report_id, patient_id, filename, file_path, report_type, extracted_text, uploaded_at)
            )
            conn.commit()
            conn.close()
        return report_data

    @staticmethod
    def get_all():
        if MONGO_AVAILABLE:
            reports = list(db.reports.find().sort('uploaded_at', -1))
            for r in reports:
                r['id'] = str(r['_id'])
            return reports
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reports ORDER BY uploaded_at DESC')
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(report_id):
        if MONGO_AVAILABLE:
            res = db.reports.find_one({'_id': report_id})
            if res:
                res['id'] = str(res['_id'])
            return res
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reports WHERE id = ?', (report_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None

    @staticmethod
    def get_by_patient_id(patient_id):
        if MONGO_AVAILABLE:
            reports = list(db.reports.find({'patient_id': patient_id}).sort('uploaded_at', -1))
            for r in reports:
                r['id'] = str(r['_id'])
            return reports
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reports WHERE patient_id = ? ORDER BY uploaded_at DESC', (patient_id,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]


class SummaryModel:
    @staticmethod
    def save_summary(report_id, patient_id, summary_dict, pdf_path=''):
        summary_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        if MONGO_AVAILABLE:
            db.summaries.update_one(
                {'report_id': report_id},
                {'$set': {
                    '_id': summary_id,
                    'patient_id': patient_id,
                    'summary_json': summary_dict,
                    'pdf_path': pdf_path,
                    'created_at': created_at
                }},
                upsert=True
            )
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            summary_str = json.dumps(summary_dict)
            cursor.execute('DELETE FROM summaries WHERE report_id = ?', (report_id,))
            cursor.execute(
                '''INSERT INTO summaries (id, report_id, patient_id, summary_json, pdf_path, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (summary_id, report_id, patient_id, summary_str, pdf_path, created_at)
            )
            conn.commit()
            conn.close()

    @staticmethod
    def get_by_report_id(report_id):
        if MONGO_AVAILABLE:
            res = db.summaries.find_one({'report_id': report_id})
            if res:
                res['id'] = str(res['_id'])
                return res
            return None
        else:
            conn = get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM summaries WHERE report_id = ?', (report_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                res = dict(row)
                if isinstance(res.get('summary_json'), str):
                    try:
                        res['summary_json'] = json.loads(res['summary_json'])
                    except Exception:
                        pass
                return res
            return None
