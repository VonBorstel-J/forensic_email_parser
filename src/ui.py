# src/ui.py

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from flask_principal import (
    Identity,
    AnonymousIdentity,
    identity_changed,
    identity_loaded,
    UserNeed,
    RoleNeed,
)
from src.utils.config import Config
from src.auth import (
    setup_authentication,
    admin_permission,
    analyst_permission,
    viewer_permission,
)
import logging
from src.utils.models import User, get_user_by_username, get_user_by_id, db
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
config = Config()

# Secure Configurations
app.config["SECRET_KEY"] = config.FLASK_SECRET_KEY or "default_secret_key"  # Graceful fallback for missing key
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent JavaScript access to session cookies
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Prevent CSRF attacks by limiting cross-site requests
app.config["WTF_CSRF_ENABLED"] = True  # Enable CSRF protection

# Setup database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your-database.db'  # Or your preferred DB URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize CSRF Protection
csrf = CSRFProtect(app)

# Setup Rate Limiting to prevent brute force attacks
limiter = Limiter(
    get_remote_address, app=app, default_limits=["200 per day", "50 per hour"]
)

# Setup Authentication and Role Management
setup_authentication(app)

# Setup Logging for Production
logger = logging.getLogger("ui")
handler = logging.StreamHandler()  # Set up a logging handler
formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

if app.config["DEBUG"]:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)

# Initialize the SQLAlchemy database instance
db.init_app(app)

with app.app_context():
    # Create tables if they do not exist yet
    db.create_all()

# Example Protected Routes

@app.route("/")
@login_required
@limiter.limit("10 per minute")  # Add rate limiting
def dashboard():
    """
    Dashboard view accessible to all authenticated users.
    """
    logger.info(f"Dashboard accessed by user: {current_user.username}")
    return render_template("dashboard.html")

@app.route("/admin")
@login_required
@admin_permission.require(http_exception=403)
@limiter.limit("5 per minute")  # Add rate limiting
def admin_dashboard():
    """
    Admin dashboard accessible only to Admin users.
    """
    logger.info(f"Admin dashboard accessed by user: {current_user.username}")
    return render_template("admin_dashboard.html")

@app.route("/analyst")
@login_required
@analyst_permission.require(http_exception=403)
@limiter.limit("5 per minute")  # Add rate limiting
def analyst_dashboard():
    """
    Analyst dashboard accessible only to Analyst users.
    """
    logger.info(f"Analyst dashboard accessed by user: {current_user.username}")
    return render_template("analyst_dashboard.html")

@app.route("/viewer")
@login_required
@viewer_permission.require(http_exception=403)
@limiter.limit("5 per minute")  # Add rate limiting
def viewer_dashboard():
    """
    Viewer dashboard accessible only to Viewer users.
    """
    logger.info(f"Viewer dashboard accessed by user: {current_user.username}")
    return render_template("viewer_dashboard.html")

@app.route("/review/<email_id>", methods=["GET", "POST"])
@login_required
@limiter.limit("10 per minute")  # Add rate limiting
def review_email(email_id):
    """
    Fetch and display email data for review. Accessible to all authenticated users.
    """
    logger.info(
        f"Email review requested by user: {current_user.username} for email ID: {email_id}"
    )
    # Implement logic to fetch and display email data
    return render_template("review_email.html", email_id=email_id)

# Error Handlers
@app.errorhandler(403)
def forbidden(e):
    logger.warning(
        f"403 Forbidden - User: {current_user.username if current_user.is_authenticated else 'Anonymous'}"
    )
    return render_template("403.html"), 403

@app.errorhandler(404)
def page_not_found(e):
    logger.error(f"404 Not Found - Path: {request.path}")
    return render_template("404.html"), 404

@app.errorhandler(429)
def rate_limit_exceeded(e):
    logger.warning(
        f"429 Rate Limit Exceeded - User: {current_user.username if current_user.is_authenticated else 'Anonymous'}"
    )
    return render_template("429.html"), 429

@app.errorhandler(500)
def internal_server_error(e):
    logger.critical(f"500 Internal Server Error - {str(e)}")
    return render_template("500.html"), 500

# Additional routes for settings, configuration, etc.

if __name__ == "__main__":
    # Ensure app runs with production settings when not in debug mode
    app.run(debug=True)
