"""
config.py - Application Configuration for DelishNex
Contains database connection settings, secret keys, and app-wide configuration.
"""

import os


class Config:
    """Base configuration class for the DelishNex application."""

    # ── Secret Key ──────────────────────────────────────────────────────
    # Used by Flask for session signing, CSRF protection, and flash messages.
    # In production, replace this with a strong random value stored in an
    # environment variable.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'delishnex-secret-key-change-in-production-2024')

    # ── MySQL Database Configuration ────────────────────────────────────
    # Connection string format: mysql+pymysql://user:password@host:port/dbname
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'niva')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'delishnex')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )

    # Disable modification tracking to save memory
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Upload Configuration ────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

    # ── Pagination ──────────────────────────────────────────────────────
    ITEMS_PER_PAGE = 12
