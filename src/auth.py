# src\auth.py

import logging
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_principal import (
    Principal,
    Permission,
    RoleNeed,
    identity_loaded,
    UserNeed,
    Identity,
    identity_changed,
    AnonymousIdentity,
)
from werkzeug.security import generate_password_hash, check_password_hash
from src.utils.models import get_user_by_username, get_user_by_id, User, users

# Configure Logger
logger = logging.getLogger("authentication")
logger.setLevel(logging.DEBUG)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = "authentication.login"

# Initialize Flask-Principal
principals = Principal()

# Define role-based permissions
admin_permission = Permission(RoleNeed("admin"))
analyst_permission = Permission(RoleNeed("analyst"))
viewer_permission = Permission(RoleNeed("viewer"))


def setup_authentication(app):
    """
    Set up authentication and role management.
    """
    # Initialize extensions
    login_manager.init_app(app)
    principals.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        user = get_user_by_id(int(user_id))
        if user:
            logger.debug("Loaded user: %s", user.username)
        return user

    @identity_loaded.connect_via(app)
    def on_identity_loaded(_sender, identity):
        """
        Handle identity loading for roles and permissions.
        """
        identity.user = current_user
        if hasattr(current_user, "id"):
            identity.provides.add(UserNeed(current_user.id))
        if hasattr(current_user, "role"):
            identity.provides.add(RoleNeed(current_user.role))

    authentication_bp = Blueprint(
        "authentication", __name__, template_folder="templates"
    )

    @authentication_bp.route("/login", methods=["GET", "POST"])
    def login():
        """
        Handle user login.
        """
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            user = get_user_by_username(username)
            if user and check_password_hash(user.password, password):
                login_user(user)
                logger.info("User logged in: %s", user.username)
                identity_changed.send(
                    current_app._get_current_object(), identity=Identity(user.id)
                )
                flash("Logged in successfully.", "success")
                return redirect(url_for("dashboard"))
            else:
                logger.warning("Failed login attempt for username: %s", username)
                flash("Invalid username or password.", "danger")
        return render_template("login.html")

    @authentication_bp.route("/logout")
    @login_required
    def logout():
        """
        Handle user logout.
        """
        logout_user()
        identity_changed.send(
            current_app._get_current_object(), identity=AnonymousIdentity()
        )
        logger.info("User logged out.")
        flash("You have been logged out.", "info")
        return redirect(url_for("authentication.login"))

    @authentication_bp.route("/register", methods=["GET", "POST"])
    def register():
        """
        Handle new user registration.
        """
        if request.method == "POST":
            username = request.form["username"]
            email = request.form["email"]
            password = request.form["password"]
            role = request.form["role"]

            if (
                not username
                or not email
                or not password
                or role not in {"admin", "analyst", "viewer"}
            ):
                flash("Invalid input. Please check your details.", "danger")
                return redirect(url_for("authentication.register"))

            if get_user_by_username(username):
                flash("Username already exists.", "warning")
                return redirect(url_for("authentication.register"))

            hashed_password = generate_password_hash(
                password, method="pbkdf2:sha256", salt_length=16
            )

            new_user = User(
                id=len(users) + 1,
                username=username,
                email=email,
                password=hashed_password,
                role=role,
            )
            users[username] = new_user
            logger.info("New user registered: %s", username)
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("authentication.login"))
        return render_template("register.html")

    app.register_blueprint(authentication_bp)
