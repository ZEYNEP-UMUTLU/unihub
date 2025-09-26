import os

# Base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# SQLite database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret key for session management
SECRET_KEY = 'your-secret-key-here-change-in-production'