# from flask import Blueprint, request, jsonify, send_file
# from database.supabase_client import get_client
# import jwt, os, io, csv
# from datetime import datetime

# bp = Blueprint("admin_attendance_bp", __name__, url_prefix="/api/admin")

# SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecret")

# def verify_token(req):
#     auth = req.headers.get("Authorization", "") or req.args.get("token", "")
#     if auth.startswith("Bearer "):
#         token = auth.split(" ", 1)[1]
#     else:
#         token = auth
#     if not token:
#         return None, "Missing token"
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#         return payload, None
#     except Exception as e:
#         return None, str(e)

# @bp.route("/attendance/list", methods=["GET"])
# def attendance_list():
#     payload, err = verify_token(request)
#     if err:
#         return jsonify({"success": False, "error": "Unauthorized: " + err}), 401

#     sb = get_client()

#     # Fetch all RSVP rows
#     rsvp_res = sb.table("rsvp_table_cs") \
#         .select("*") \
#         .order("created_at", {"ascending": False}) \
#         .execute()

#     if rsvp_res.error:
#         return jsonify({"success": False, "error": str(rsvp_res.error)}), 500

#     rows = rsvp_res.data or []
#     output = []

#     # Attach attendance status
#     for r in rows:
#         att = sb.table("attendance_table_cs") \
#             .select("*") \
#             .eq("uu_roll_no", r["uu_roll_no"]) \
#             .order("timestamp", {"ascending": False}) \
#             .limit(1) \
#             .execute()

#         last = att.data[0]["status"] if att.data else None

#         output.append({
#             "uu_roll_no": r["uu_roll_no"],
#             "name": r["name"],
#             "course": r["course"],
#             "dept": r["dept"],
#             "rsvp_status": r.get("rsvp_status"),
#             "attendance_status": last
#         })

#     return jsonify({"success": True, "rows": output})



# @bp.route("/attendance/mark", methods=["POST"])
# def attendance_mark():
#     payload, err = verify_token(request)
#     if err:
#         return jsonify({"success": False, "error": "Unauthorized: " + err}), 401

#     data = request.get_json() or {}
#     uu_roll_no = data.get("uu_roll_no")
#     status = data.get("status")  # "Present" or "Absent"
#     if not uu_roll_no or status not in ("Present", "Absent"):
#         return jsonify({"success": False, "error": "Missing/invalid parameters"}), 400

#     sb = get_client()

#     # Fetch student name/course for logging (best-effort)
#     master = sb.table("student_master_cs").select("name, course, dept").eq("uu_roll_no", uu_roll_no).execute()
#     name = master.data[0]["name"] if master.data else None
#     course = master.data[0]["course"] if master.data else None
#     dept = master.data[0]["dept"] if master.data else "CS"

#     # Upsert attendance record for today+student (we'll simply insert a new row; editing allowed)
#     record = {
#         "uu_roll_no": uu_roll_no,
#         "name": name or "",
#         "course": course or "",
#         "dept": dept or "",
#         "date": datetime.utcnow().date().isoformat(),
#         "status": status,
#         "method": "Manual",
#         "timestamp": datetime.utcnow().isoformat()
#     }
#     insert = sb.table("attendance_table_cs").insert(record).execute()
#     if insert.error:
#         return jsonify({"success": False, "error": str(insert.error)}), 500

#     return jsonify({"success": True, "message": "Attendance recorded"})

# @bp.route("/attendance/export", methods=["GET"])
# def attendance_export():
#     payload, err = verify_token(request)
#     if err:
#         return jsonify({"success": False, "error": "Unauthorized: " + err}), 401

#     sb = get_client()
#     res = sb.table("attendance_table_cs").select("*").order("timestamp", {"ascending": True}).execute()
#     rows = res.data or []

#     # build CSV in memory
#     buf = io.StringIO()
#     writer = csv.writer(buf)
#     writer.writerow(["UU_Roll_No","Name","Course","Dept","Date","Status","Method","Timestamp"])
#     for r in rows:
#         writer.writerow([
#             r.get("uu_roll_no"), r.get("name"), r.get("course"), r.get("dept"),
#             r.get("date"), r.get("status"), r.get("method"), r.get("timestamp")
#         ])
#     buf.seek(0)
#     return send_file(io.BytesIO(buf.getvalue().encode("utf-8")), mimetype="text/csv",
#                      as_attachment=True, download_name="attendance_export.csv")



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
# @bp.route("/attendance/list", methods=["GET"])
# def attendance_list():
#     # ---- 1) Verify admin token ----
#     payload, err = verify_token(request)
#     if err:
#         return jsonify({"success": False, "error": "Unauthorized: " + err}), 401

#     sb = get_client()

#     # ---- 2) Try RPC call safely ----
#     try:
#         rows = sb.rpc("get_admin_attendance_rows_cs").execute()
#         # RPC success → rows.data available
#         data_rows = rows.data or []

#         out = []
#         for r in data_rows:
#             out.append({
#                 "uu_roll_no": r.get("uu_roll_no"),
#                 "name": r.get("name"),
#                 "course": r.get("course"),
#                 "dept": r.get("dept"),
#                 "rsvp_status": r.get("rsvp_status"),
#                 "attendance_status": r.get("status")
#             })

#         return jsonify({"success": True, "rows": out})

#     except Exception as e:
#         print("RPC failed, falling back:", e)

#     # ---- 3) Fallback: direct table select ----
#     try:
#         res = sb.table("rsvp_table_cs").select("*").order("created_at", desc=True).execute()
#         rrows = res.data or []

#         out = []

#         for r in rrows:
#             # fetch last attendance (if any)
#             att = sb.table("attendance_table_cs") \
#                 .select("status") \
#                 .eq("uu_roll_no", r["uu_roll_no"]) \
#                 .order("timestamp", desc=True) \
#                 .limit(1) \
#                 .execute()

#             last_status = None
#             if att.data and len(att.data) > 0:
#                 last_status = att.data[0].get("status")

#             out.append({
#                 "uu_roll_no": r["uu_roll_no"],
#                 "name": r["name"],
#                 "course": r["course"],
#                 "dept": r["dept"],
#                 "rsvp_status": r.get("rsvp_status"),
#                 "attendance_status": last_status
#             })

#         return jsonify({"success": True, "rows": out})

#     except Exception as e:
#         return jsonify({"success": False, "error": str(e)}), 500

@bp.route("/attendance/list", methods=["GET"])
def attendance_list():
    payload, err = verify_token(request)
    if err:
        return jsonify({"success": False, "error": "Unauthorized: " + err}), 401

    sb = get_client()

    # 1️⃣ Fetch ALL students (main list)
    master = (
    sb.table("student_master_cs")
      .select("*")
      .order("s_no", desc=False)   # ascending = True
      .execute()
    )

    students = master.data or []

    # 2️⃣ Fetch RSVP statuses
    rsvp = (
    sb.table("rsvp_table_cs")
      .select("*")
      .order("created_at", desc=True)
      .execute()
    )

    rsvp_map = {r["uu_roll_no"]: r["rsvp_status"] for r in (rsvp.data or [])}

    # 3️⃣ Fetch latest attendance per student
    attendance = sb.table("attendance_table_cs") \
                   .select("uu_roll_no, status, timestamp") \
                   .order("timestamp", desc=True).execute()

    attendance_map = {}
    for row in (attendance.data or []):
        if row["uu_roll_no"] not in attendance_map:
            attendance_map[row["uu_roll_no"]] = row["status"]

    # 4️⃣ Build combined unified list
    final = []
    for stu in students:
        roll = stu["uu_roll_no"]
        final.append({
            "uu_roll_no": roll,
            "name": stu["name"],
            "course": stu["course"],
            "dept": stu["dept"],
            "rsvp_status": rsvp_map.get(roll, "No"),
            "attendance_status": attendance_map.get(roll, None)
        })

    return jsonify({"success": True, "rows": final})


# -----------------------------------------------------
# MARK ATTENDANCE
# -----------------------------------------------------
@bp.route("/attendance/mark", methods=["POST"])
def attendance_mark():
    payload, err = verify_token(request)
    if err:
        return jsonify({"success": False, "error": "Unauthorized: " + err}), 401

    data = request.get_json() or {}
    uu_roll_no = data.get("uu_roll_no")
    status = data.get("status")

    if not uu_roll_no or status not in ("Present", "Absent"):
        return jsonify({"success": False, "error": "Missing or invalid parameters"}), 400

    sb = get_client()

    # Fetch master table record
    master = sb.table("student_master_cs").select("*").eq("uu_roll_no", uu_roll_no).execute()
    student = master.data[0] if master.data else {}

    record = {
        "uu_roll_no": uu_roll_no,
        "name": student.get("name", ""),
        "course": student.get("course", ""),
        "dept": student.get("dept", "CS"),
        "date": datetime.utcnow().date().isoformat(),
        "status": status,
        "method": "Manual",
        "timestamp": datetime.utcnow().isoformat()
    }

    insert = sb.table("attendance_table_cs").insert(record).execute()
    if insert.error:
        return jsonify({"success": False, "error": str(insert.error)}), 500

    return jsonify({"success": True, "message": "Attendance recorded"})


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
