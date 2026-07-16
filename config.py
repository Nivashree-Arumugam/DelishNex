"""
config.py - Application Configuration for DelishNex
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "delishnex-secret-key"
    )

    # SQLite database
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "delishnex.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images")

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    ITEMS_PER_PAGE = 12