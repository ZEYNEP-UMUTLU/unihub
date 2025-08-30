import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'forum.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = 'forum_site_secret_key_2025_change_in_production'