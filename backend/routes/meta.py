from flask import Blueprint, jsonify
from database.supabase_client import get_client

bp = Blueprint("meta", __name__)

@bp.get("/meta/options")
def options():
    sb = get_client()
    # Distinct depts and courses from master table (CS system)
    depts = sb.table("student_master_cs").select("dept").neq("dept", None).execute()
    courses = sb.table("student_master_cs").select("course").neq("course", None).execute()

    uniq_depts = sorted({row["dept"] for row in depts.data})
    uniq_courses = sorted({row["course"] for row in courses.data})

    return jsonify({
        "depts": uniq_depts,           # e.g., ["CS"]
        "courses": uniq_courses,       # e.g., ["BCA", "BTECH", "MCA", "DIPLOMA"]
    })
