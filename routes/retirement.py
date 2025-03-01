import logging
import time
from flask import Blueprint, jsonify, request, session
from datetime import datetime, timedelta

# Configure Logging
logging.basicConfig(filename="401k_activity.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define Blueprint
retirement_bp = Blueprint("retirement", __name__, url_prefix="/apps/401k")

# Placeholder function to fetch user account data
def get_user_account(user):
    # This function should interact with a secure database to fetch user data
    # For demonstration, returning a sample user data structure
    return {"funds": 10000, "401k_balance": 5000, "locked": False, "reset": False}

# Rate Limit Tracker { "user": {"endpoint": [timestamps]} }
request_tracker = {}

# Logging Function
def log_activity(event, desc):
    user = session.get("user", "Unknown User")
    logging.info(f"{event} - User: {user} - {desc}")

# Rate Limiting Function
def rate_limited(user, endpoint, limit, period):
    now = datetime.now()
    request_tracker.setdefault(user, {}).setdefault(endpoint, [])
    request_tracker[user][endpoint] = [t for t in request_tracker[user][endpoint] if now - t < timedelta(seconds=period)]

    if len(request_tracker[user][endpoint]) >= limit:
        log_activity("RATE LIMIT", f"User {user} exceeded {endpoint} limit")
        return True  # Rate limit exceeded

    request_tracker[user][endpoint].append(now)
    return False  # Allowed

# Balance Route (Limit: 10 per min)
@retirement_bp.route("/balance")
def get_balance():
    user = session.get("user")
    if not user: return jsonify({"error": "Not logged in"}), 401
    
    user_data = get_user_account(user)
    if not user_data: return jsonify({"error": "User not found"}), 404
    if rate_limited(user, "balance", 10, 60): return jsonify({"error": "Rate limit exceeded"}), 429

    log_activity("BALANCE CHECK", f"Checked balance: ${user_data['401k_balance']}")
    return jsonify(user_data)

# Personal Funds and 401(k) Balance Route (Limit: 10 per min)
@retirement_bp.route("/funds")
def get_funds():
    user = session.get("user")
    if not user: return jsonify({"error": "Not logged in"}), 401
    
    user_data = get_user_account(user)
    if not user_data: return jsonify({"error": "User not found"}), 404
    if rate_limited(user, "funds", 10, 60): return jsonify({"error": "Rate limit exceeded"}), 429

    log_activity("FUNDS CHECK", f"Checked funds: ${user_data['funds']}, 401(k) balance: ${user_data['401k_balance']}")
    return jsonify({"funds": user_data["funds"], "401k_balance": user_data["401k_balance"]})

# Contribution Route (Limit: 3 per min)
@retirement_bp.route("/contribute", methods=["POST"])
def contribute():
    user = session.get("user")
    if not user: return jsonify({"error": "Not logged in"}), 401
    
    user_data = get_user_account(user)
    if not user_data: return jsonify({"error": "User not found"}), 404
    if rate_limited(user, "contribute", 3, 60): return jsonify({"error": "Rate limit exceeded"}), 429

    try:
        amount = float(request.json.get("amount", 0))
        if amount <= 0: raise ValueError
    except ValueError:
        log_activity("INVALID CONTRIBUTION", "Invalid amount")
        return jsonify({"error": "Invalid contribution amount!"}), 400

    # **Prevent simultaneous transactions (Lock funds during processing)**
    if user_data["locked"]:
        log_activity("CONTRIBUTION LOCKED", f"User {user} attempted multiple contributions simultaneously")
        return jsonify({"error": "Transaction in progress. Please wait."}), 429

    user_data["locked"] = True  # Lock funds

    # **Final balance check before deducting funds**
    if amount > user_data["funds"]:
        log_activity("INSUFFICIENT FUNDS", f"User {user} attempted to contribute ${amount} but only has ${user_data['funds']}")
        user_data["locked"] = False  # Unlock funds
        return jsonify({
            "error": "Insufficient funds! Contribution exceeds available balance.",
            "funds": user_data["funds"],
            "401k_balance": user_data["401k_balance"]
        }), 400

    time.sleep(1)  # Simulating Processing
    match = amount * 0.5
    user_data["funds"] -= amount
    user_data["401k_balance"] += amount + match
    log_activity("CONTRIBUTION", f"Contributed ${amount}, employer matched ${match}")

    user_data["locked"] = False  # Unlock funds after transaction
    return jsonify({"message": f"Contributed ${amount}. Employer matched ${match}!", "funds": user_data["funds"], "401k_balance": user_data["401k_balance"]})

# Withdrawal Route (Limit: 3 per min)
@retirement_bp.route("/withdraw", methods=["POST"])
def withdraw():
    user = session.get("user")
    if not user: return jsonify({"error": "Not logged in"}), 401
    
    user_data = get_user_account(user)
    if not user_data: return jsonify({"error": "User not found"}), 404
    if rate_limited(user, "withdraw", 3, 60): return jsonify({"error": "Rate limit exceeded"}), 429

    try:
        amount = float(request.json.get("amount", 0))
        if amount <= 0: raise ValueError
    except ValueError:
        log_activity("INVALID WITHDRAWAL", "Invalid amount")
        return jsonify({"error": "Invalid withdrawal amount!"}), 400

    # Prevent simultaneous transactions (Lock funds during processing)
    if user_data["locked"]:
        log_activity("WITHDRAWAL LOCKED", f"User {user} attempted multiple withdrawals simultaneously")
        return jsonify({"error": "Transaction in progress. Please wait."}), 429

    user_data["locked"] = True  # Lock funds

    # Final balance check before withdrawing funds
    if amount > user_data["401k_balance"]:
        log_activity("INSUFFICIENT FUNDS", f"User {user} attempted to withdraw ${amount} but only has ${user_data['401k_balance']}")
        user_data["locked"] = False  # Unlock funds
        return jsonify({
            "error": "Insufficient funds! Withdrawal exceeds 401(k) balance.",
            "funds": user_data["funds"],
            "401k_balance": user_data["401k_balance"]
        }), 400

    time.sleep(1)  # Simulating Processing
    user_data["401k_balance"] -= amount
    user_data["funds"] += amount
    log_activity("WITHDRAWAL", f"Withdrew ${amount} from 401(k)")

    user_data["locked"] = False  # Unlock funds after transaction
    return jsonify({"message": f"Withdrew ${amount} from 401(k)!", "funds": user_data["funds"], "401k_balance": user_data["401k_balance"]})

# Reset Route (Limit: 1 per min)
@retirement_bp.route("/reset", methods=["POST"])
def reset_account():
    user = session.get("user")
    if not user: return jsonify({"error": "Not logged in"}), 401
    
    user_data = get_user_account(user)
    if not user_data: return jsonify({"error": "User not found"}), 404
    if rate_limited(user, "reset", 1, 60): return jsonify({"error": "Rate limit exceeded"}), 429

    # Prevent resetting account after the first attempt
    if user_data.get("reset"):
        log_activity("ACCOUNT RESET ATTEMPT", "User attempted to reset account again")
        return jsonify({"error": "Account has already been reset once"}), 403

    # Ensure the user account is properly reset
    user_data = {"funds": 10000, "401k_balance": 0, "locked": False, "reset": True}
    if user_data is None:
        log_activity("ACCOUNT RESET ERROR", "Failed to reset account")
        return jsonify({"error": "Failed to reset account"}), 500

    log_activity("ACCOUNT RESET", "401(k) account reset")
    return jsonify({"message": "Account reset successfully!", "funds": 10000, "401k_balance": 0})