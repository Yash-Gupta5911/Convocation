from flask import Blueprint, request, jsonify
from database.supabase_client import get_client
import jwt, os

bp = Blueprint("super_admin_bp", __name__, url_prefix="/api/superadmin")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")


# ------------------------------
# VERIFY TOKEN (Super Admin Only)
# ------------------------------
def verify_super_admin(req):
    auth = req.headers.get("Authorization", "") or req.args.get("token", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
    else:
        token = auth

    if not token:
        return None, "Missing token"

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("role") != "super_admin":
            return None, "Access denied: Not a Super Admin"
        return payload, None
    except Exception as e:
        return None, str(e)


# -------------------------------------------------------
# SUPER ADMIN OVERVIEW: Merge student, RSVP, attendance
# -------------------------------------------------------
@bp.route("/overview", methods=["GET"])
def overview():
    # ---- 1) Verify token and role ----
    payload, err = verify_super_admin(request)
    if err:
        return jsonify({"success": False, "error": "Unauthorized: " + err}), 401

    sb = get_client()

    try:
        # ---- 2) Fetch student master ----
        students_res = sb.table("student_master_cs") \
            .select("uu_roll_no, name, course, dept") \
            .order("s_no", desc=False) \
            .execute()
        students = students_res.data or []

        # ---- 3) Fetch RSVP data ----
        rsvp_res = sb.table("rsvp_table_cs") \
            .select("uu_roll_no, rsvp_status, approved, approved_at") \
            .execute()
        rsvp_map = {r["uu_roll_no"]: r for r in (rsvp_res.data or [])}

        # ---- 4) Fetch Attendance data ----
        att_res = sb.table("attendance_table_cs") \
            .select("uu_roll_no, status, method, marked_by, marked_at") \
            .execute()
        att_map = {a["uu_roll_no"]: a for a in (att_res.data or [])}

        # ---- 5) Merge all three tables ----
        merged = []
        for stu in students:
            roll = stu["uu_roll_no"]
            rsvp = rsvp_map.get(roll)
            att = att_map.get(roll)

            merged.append({
                "uu_roll_no": roll,
                "name": stu["name"],
                "course": stu["course"],
                "dept": stu["dept"],
                "rsvp_status": rsvp["rsvp_status"] if rsvp else "No",
                "approved": rsvp["approved"] if rsvp else False,
                "approved_at": rsvp["approved_at"] if rsvp else None,
                "attendance_status": att["status"] if att else "Absent",
                "method": att["method"] if att else None,
                "marked_by": att["marked_by"] if att else None,
                "marked_at": att["marked_at"] if att else None
            })

        print(f"[SuperAdmin] Merged {len(merged)} student records successfully.")
        return jsonify({"success": True, "rows": merged})

    except Exception as e:
        print("Error while fetching super admin overview:", e)
        return jsonify({"success": False, "error": str(e)}), 500
