"""
app.py - Application Entry Point for DelishNex
Initializes Flask, SQLAlchemy, Flask-Login, and registers all routes.
"""

from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User
import os

# ---------------- Flask-Login ----------------
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    """Reload user object from session."""
    return db.session.get(User, int(user_id))


# ---------------- Application Factory ----------------
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprint
    from routes import main
    app.register_blueprint(main)

    # Create upload folder if missing
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Create/Update admin account
    with app.app_context():
        admin = User.query.filter_by(email="admin@delishnex.com").first()

        if admin:
            if not admin.check_password("admin123"):
                admin.set_password("admin123")
                db.session.commit()
        else:
            admin = User(
                full_name="Admin User",
                email="admin@delishnex.com",
                phone="9999999999",
                role="admin",
                reward_points=0,
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

    return app


# ======================================================
# IMPORTANT FOR VERCEL
# This creates the Flask app at the top level.
# ======================================================
app = create_app()


# ======================================================
# Run locally
# ======================================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )