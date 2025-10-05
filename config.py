
import os
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "uopeople-capstone-mats")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///MATS.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
