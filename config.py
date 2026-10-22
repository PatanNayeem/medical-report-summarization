import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'med-summary-secret-key-2026-secure')
    
    # Base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Upload & Storage Config
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    PERSIST_DIRECTORY = os.path.join(BASE_DIR, 'chroma_db')
    GENERATED_PDF_FOLDER = os.path.join(BASE_DIR, 'generated_summaries')
    
    # Database Configuration (MongoDB with SQLite fallback)
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/medical_summarizer_db')
    SQLITE_DB_PATH = os.path.join(BASE_DIR, 'medical_db.sqlite')
    
    # HuggingFace & LangChain Config
    HUGGINGFACE_API_TOKEN = os.environ.get('HUGGINGFACE_API_TOKEN', '')
    MODEL_ID = os.environ.get('MODEL_ID', 'mistralai/Mistral-7B-Instruct-v0.2')
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # Allowed Extensions
    ALLOWED_EXTENSIONS = {'pdf', 'txt'}

    @classmethod
    def init_app(cls):
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.PERSIST_DIRECTORY, exist_ok=True)
        os.makedirs(cls.GENERATED_PDF_FOLDER, exist_ok=True)
