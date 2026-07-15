"""
app.py - Application Entry Point for DelishNex
Initializes Flask, SQLAlchemy, Flask-Login, and registers all routes.
"""

from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User

# ── Initialize Flask-Login globally ─────────────────────────────────────
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    """Callback used by Flask-Login to reload the user object from the user ID stored in the session."""
    return db.session.get(User, int(user_id))


def create_app():
    """Application factory: creates and configures the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Initialize extensions ───────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)

    # ── Register blueprints ─────────────────────────────────────────────
    from routes import main
    app.register_blueprint(main)

    # ── Create upload directory if it doesn't exist ─────────────────────
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ── Ensure admin user exists with proper password hash ────────────────
    with app.app_context():
        admin = User.query.filter_by(email='admin@delishnex.com').first()
        if admin:
            # Update the placeholder hash from database.sql with a real one
            if not admin.check_password('admin123'):
                admin.set_password('admin123')
                db.session.commit()
        else:
            # Create admin if not seeded via database.sql
            admin = User(
                full_name='Admin User',
                email='admin@delishnex.com',
                phone='9999999999',
                role='admin',
                reward_points=0
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

    return app


# ── Run the application ────────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
