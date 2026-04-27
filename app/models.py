from . import db
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ClassGroup(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    class_type = db.Column(db.String(20), nullable=False, default='classmap') # 'classmap' or 'classwrite'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    sessions = db.relationship('Session', backref='class_group', lazy=True, cascade='all, delete-orphan')

class Session(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    class_id = db.Column(db.String(36), db.ForeignKey('class_group.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    flags = db.relationship('Flag', backref='session', lazy=True, cascade='all, delete-orphan')

class Flag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('session.id'), nullable=False)
    client_id = db.Column(db.String(100), nullable=True)
    region_id = db.Column(db.String(50), nullable=False) # Retained for compatibility if needed
    x = db.Column(db.Float, nullable=True) # latitude
    y = db.Column(db.Float, nullable=True) # longitude
    text_content = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=True) # Path to uploaded file
    thumbnail_path = db.Column(db.String(255), nullable=True) # Path to generated thumbnail
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_name = db.Column(db.String(100), nullable=False, default="Participant")
