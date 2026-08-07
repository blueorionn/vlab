"""Authentication routes — signup, login, logout."""

from flask import (
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from vlab.database import get_db

from . import blueprint
from .models import User


@blueprint.route("/signup", methods=["GET", "POST"])
def signup():
    """Register a new user account."""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""

        errors = []

        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not email or "@" not in email:
            errors.append("Please provide a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        # Check for existing username / email.
        if not errors:
            if User.find_by_username(username):
                errors.append("Username is already taken.")
            if User.find_by_email(email):
                errors.append("Email is already registered.")

        if errors:
            for error in errors:
                flash(error, "error")
            return (
                render_template("auth/signup.html"),
                400,
            )

        # Create the user.
        db = next(get_db())
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.add(user)
            db.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as exc:
            db.rollback()
            flash(f"Could not create account: {exc}", "error")
            return render_template("auth/signup.html"), 500
        finally:
            db.close()

    return render_template("auth/signup.html")


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate an existing user."""
    if request.method == "POST":
        login_id = (request.form.get("login") or "").strip()
        password = request.form.get("password") or ""

        if not login_id or not password:
            flash(
                "Please provide both login (email or username) and password.", "error"
            )
            return render_template("auth/login.html"), 400

        # Accept email *or* username.
        user = User.find_by_email(login_id.lower())
        if user is None:
            user = User.find_by_username(login_id)

        if user is None or not user.check_password(password):
            flash("Invalid login credentials.", "error")
            return render_template("auth/login.html"), 401

        # Store user identity in the session.
        session.clear()
        session["user_id"] = user.id
        session["username"] = user.username
        flash(f"Welcome back, {user.username}!", "success")
        return redirect(url_for("core.index"))

    return render_template("auth/login.html")


@blueprint.route("/logout")
def logout():
    """Clear the session and redirect home."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("core.index"))


# ---------------------------------------------------------------------------
# Helpers accessible from other blueprints
# ---------------------------------------------------------------------------


def current_user() -> User | None:
    """Return the currently logged-in ``User``, or ``None``."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    db = next(get_db())
    try:
        return db.query(User).get(user_id)
    finally:
        db.close()


@blueprint.app_context_processor
def inject_current_user():
    """Make ``current_user`` available in all templates."""
    return {"current_user": current_user()}
