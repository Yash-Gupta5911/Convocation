from flask import Blueprint, request, jsonify
from database.supabase_client import get_client
import bcrypt
import jwt
import os
from datetime import datetime, timedelta

bp = Blueprint("super_admin_auth_bp", __name__, url_prefix="/api/superadmin")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")


@bp.route("/login", methods=["POST"])
def super_admin_login():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"success": False, "error": "Email and password required"}), 400

        sb = get_client()
        res = sb.table("admin_users").select("*").eq("email", email).execute()

        if not res.data or len(res.data) == 0:
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

        admin = res.data[0]

        # Verify role
        if admin.get("role") != "super_admin":
            return jsonify({"success": False, "error": "Access denied: Not a Super Admin"}), 403

        stored_hash = admin["password_hash"].encode("utf-8")
        if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

        # Generate JWT
        token = jwt.encode(
            {
                "email": email,
                "role": "super_admin",
                "exp": datetime.utcnow() + timedelta(hours=12)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        return jsonify({
            "success": True,
            "message": "Super Admin Login successful",
            "token": token,
            "admin": {"name": admin["name"], "email": email, "role": "super_admin"}
        })

    except Exception as e:
        print("Super Admin Login error:", e)
        return jsonify({"success": False, "error": str(e)}), 500
