from flask import Blueprint, request, jsonify, send_file
from database.supabase_client import get_client
import jwt, os, io, csv
from datetime import datetime

bp = Blueprint("admin_attendance_bp", __name__, url_prefix="/api/admin")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")


# ------------------------------
# TOKEN VERIFICATION
# ------------------------------
def verify_token(req):
    auth = req.headers.get("Authorization", "") or req.args.get("token", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
    else:
        token = auth

    if not token:
        return None, "Missing token"

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload, None
    except Exception as e:
        return None, str(e)






# -----------------------------------------------------
# 🟢 FIXED: MANUAL ATTENDANCE LIST (NO RPC USED ANYMORE)
# -----------------------------------------------------
@bp.route("/attendance/list", methods=["GET"])
def attendance_list():
    # ---- 1) Verify admin token ----
    payload, err = verify_token(request)
    if err:
        return jsonify({"success": False, "error": "Unauthorized: " + err}), 401

    sb = get_client()

    try:
        # ---- 2) Fetch all students ----
        students_res = sb.table("student_master_cs") \
            .select("uu_roll_no, name, course, dept") \
            .order("s_no", desc=False) \
            .execute()

        students = students_res.data or []

        # ---- 3) Fetch RSVP statuses ----
        rsvp_res = sb.table("rsvp_table_cs") \
            .select("uu_roll_no, rsvp_status") \
            .execute()

        rsvp_map = {r["uu_roll_no"]: r["rsvp_status"] for r in (rsvp_res.data or [])}

        # ---- 4) Build final list (no attendance yet) ----
        final = []
        for stu in students:
            roll = stu["uu_roll_no"]
            final.append({
                "uu_roll_no": roll,
                "name": stu["name"],
                "course": stu["course"],
                "dept": stu["dept"],
                "rsvp_status": rsvp_map.get(roll, "No"),
                "attendance_status": None  # for now - will be updated when P/A marked
            })

        print(f"Loaded {len(final)} student records successfully.")
        return jsonify({"success": True, "rows": final})

    except Exception as e:
        print("Error while fetching student list:", e)
        return jsonify({"success": False, "error": str(e)}), 500





# -----------------------------------------------------
# MARK ATTENDANCE
# -----------------------------------------------------
@bp.route("/attendance/mark", methods=["POST"])
def mark_attendance():
    # ---- 1) Verify admin token ----
    payload, err = verify_token(request)
    if err:
        return jsonify({"success": False, "error": "Unauthorized: " + err}), 401

    sb = get_client()
    data = request.get_json()
    roll = data.get("uu_roll_no")
    status = data.get("status")

    if not roll or not status:
        return jsonify({"success": False, "error": "Missing roll number or status"}), 400

    try:
        # ---- 2) Fetch student details ----
        stu_res = sb.table("student_master_cs") \
            .select("name, course, dept") \
            .eq("uu_roll_no", roll) \
            .limit(1) \
            .execute()

        if not stu_res.data or len(stu_res.data) == 0:
            return jsonify({"success": False, "error": "Student not found"}), 404

        student = stu_res.data[0]

        # ---- 3) Get RSVP status (default No) ----
        rsvp_res = sb.table("rsvp_table_cs") \
            .select("rsvp_status") \
            .eq("uu_roll_no", roll) \
            .limit(1) \
            .execute()
        rsvp_status = rsvp_res.data[0]["rsvp_status"] if rsvp_res.data else "No"

        # ---- 4) Insert or Update attendance ----
        # Because uu_roll_no is UNIQUE, we can safely UPSERT
        insert_data = {
            "uu_roll_no": roll,
            "name": student["name"],
            "course": student.get("course"),
            "dept": student.get("dept"),
            "rsvp_status": rsvp_status,
            "status": status,
            "method": "Manual",
            "marked_by": "System"
        }

        # ⚡ Upsert to prevent duplicate entries
        sb.table("attendance_table_cs").upsert(insert_data, on_conflict="uu_roll_no").execute()

        return jsonify({"success": True, "message": f"Marked {roll} as {status} successfully."})

    except Exception as e:
        print("Attendance mark error:", e)
        return jsonify({"success": False, "error": str(e)}), 500




# -----------------------------------------------------
# EXPORT CSV
# -----------------------------------------------------
@bp.route("/attendance/export", methods=["GET"])
def attendance_export():
    payload, err = verify_token(request)
    if err:
        return jsonify({"success": False, "error": "Unauthorized: " + err}), 401

    sb = get_client()
    res = sb.table("attendance_table_cs").select("*").order("timestamp", {"ascending": True}).execute()
    rows = res.data or []

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["UU_Roll_No", "Name", "Course", "Dept", "Date", "Status", "Method", "Timestamp"])

    for r in rows:
        writer.writerow([
            r.get("uu_roll_no"), r.get("name"), r.get("course"), r.get("dept"),
            r.get("date"), r.get("status"), r.get("method"), r.get("timestamp")
        ])

    buf.seek(0)
    return send_file(
        io.BytesIO(buf.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="attendance_export.csv"
    )
