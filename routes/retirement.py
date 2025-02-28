import logging
from flask import Blueprint, render_template, jsonify, request, session
from extensions import db
from models.user import User
import time
from sqlalchemy.exc import IntegrityError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

retirement_bp = Blueprint("retirement", __name__, url_prefix="/apps/401k")

# Initialize Flask-Limiter for rate limiting
limiter = Limiter(get_remote_address, default_limits=["5 per minute"])
csrf = CSRFProtect()

# Configure logging
logging.basicConfig(
    filename="security.log",
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def log_suspicious_activity(user, message, level=logging.WARNING):
    """Logs suspicious activity for monitoring"""
    logging.log(level, f"User: {user} - {message}")

# Secure session settings
SESSION_SETTINGS = {
    "SESSION_COOKIE_SECURE": True,
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SAMESITE": "Strict",
}

@retirement_bp.route("/")
def retirement_dashboard():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
    return render_template("401k.html", username=session["user"])

@retirement_bp.route("/balance")
def get_balance():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401
        
    username = session["user"]
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "funds": user.funds,
        "401k_balance": user.k_balance
    })

@retirement_bp.route("/contribute", methods=["POST"])
@limiter.limit("5 per minute")
@csrf.exempt
def contribute():
    """Secure 401(k) contribution handling with suspicious activity logging"""
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    amount = data.get("amount", 0)
    username = session["user"]
    
    # Validate input
    if not isinstance(amount, (int, float)) or amount <= 0:
        log_suspicious_activity(username, f"Invalid contribution attempt: ${amount}")
        return jsonify({"message": "Invalid contribution amount!"}), 400

    user = User.query.filter_by(username=username).with_for_update().first()

    if not user:
        return jsonify({"message": "User not found!"}), 404

    if amount > user.funds:
        log_suspicious_activity(username, f"Attempted over-contribution: Requested ${amount}, Available ${user.funds}")
        return jsonify({"message": "Insufficient funds!"}), 400

    # Flag unusually high contributions
    if amount > 5000:
        log_suspicious_activity(username, f"Large transaction alert: Contributed ${amount}", level=logging.INFO)

    try:
        company_match = amount * 0.5
        total_contribution = amount + company_match

        user.funds -= amount
        user.k_balance += total_contribution
        db.session.commit()

        return jsonify({
            "message": f"Contributed ${amount}. Employer matched ${company_match}!",
            "funds": user.funds,
            "401k_balance": user.k_balance
        })
    except IntegrityError:
        db.session.rollback()
        log_suspicious_activity(username, "Database error during contribution")
        return jsonify({"message": "Transaction failed, try again!"}), 500

@retirement_bp.route("/reset", methods=["POST"])
@limiter.limit("2 per minute")
@csrf.exempt
def reset_account():
    """Secure account reset with logging"""
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    username = session["user"]
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"message": "Account not found!"}), 404

    # Log suspicious frequent resets
    log_suspicious_activity(username, "Account reset request", level=logging.INFO)

    user.funds = 10000
    user.k_balance = 0
    db.session.commit()

    return jsonify({
        "message": "Account reset successfully!",
        "funds": user.funds,
        "401k_balance": user.k_balance
    })
