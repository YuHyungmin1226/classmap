import os
import sys

# Determine base directory depending on if we are running as a PyInstaller bundle
if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    basedir = sys._MEIPASS
    # For data, we use the folder where the executable is located
    exe_dir = os.path.dirname(sys.executable)
    data_dir = os.path.join(exe_dir, 'ClassMapData')
else:
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    data_dir = os.path.join(basedir, 'app', 'static')

# Ensure data directories exist
os.makedirs(os.path.join(data_dir, 'instance'), exist_ok=True)
os.makedirs(os.path.join(data_dir, 'uploads'), exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key-for-classroom'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(data_dir, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(data_dir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
