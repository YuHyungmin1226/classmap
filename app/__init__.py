import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from .config import Config

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")

def get_base_prefix():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def create_app():
    base_dir = get_base_prefix()
    
    # In PyInstaller, templates and static will be extracted to _MEIPASS/app/...
    template_dir = os.path.join(base_dir, 'app', 'templates')
    static_dir = os.path.join(base_dir, 'app', 'static')
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app)

    with app.app_context():
        from . import models
        db.create_all()
        
        # Initialize default admin if not exists
        admin = models.Admin.query.first()
        if not admin:
            default_admin = models.Admin()
            default_admin.set_password('admin123')
            db.session.add(default_admin)
            db.session.commit()

        from .routes import main
        app.register_blueprint(main)
        from . import events

    return app
