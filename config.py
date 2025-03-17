import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hospital.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_EMAIL = 'frazakram19@gmail.com'
    HOSPITAL_NAME = 'Care Hospital'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
