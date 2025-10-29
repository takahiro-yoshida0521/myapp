class Config:
    SECRET_KEY = 'your-secret-key'  # セッションに必須！
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgre@localhost/myappdb'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 最大2MB
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
