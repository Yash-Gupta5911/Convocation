# routes/register.py
from flask import Blueprint, request, jsonify
from database.supabase_client import get_client, upload_photo, upload_ticket, create_rsvp
from pdf.pdf_generator import generate_ticket_pdf_bytes
from routes.mail import send_ticket_email, send_rejection_email

# Use "bp" so app.py can import "bp as register_bp"
bp = Blueprint("register_bp", __name__, url_prefix="/api")


@bp.route("/register", methods=["POST"])
def register():
    try:
        sb = get_client()

        # 1) Extract form data
        uu_roll_no = request.form.get("uu_roll_no")
        name = request.form.get("name")
        name = name.strip()
        email = request.form.get("email")
        course = request.form.get("course")
        dept = "CS"  # Always CS system
        rsvp_status = request.form.get("rsvp_status", "No")
        photo_file = request.files.get("photo")

        if not all([uu_roll_no, name, email, course, photo_file]):
            return jsonify({"error": "Missing required fields"}), 400

        # 2) Upload photo
        photo_bytes = photo_file.read()
        photo_filename = f"{uu_roll_no}.jpg"
        photo_url = upload_photo(photo_bytes, photo_filename)

        # 3. Check Student Exists in Master Table (Strict Roll No + Case-insensitive Name)

        master_query = sb.table("student_master_cs") \
            .select("*") \
            .eq("uu_roll_no", uu_roll_no) \
            .ilike("name", name) \
            .execute()

        student_exists = master_query.data and len(master_query.data) > 0
        approved = bool(student_exists)



        # 4) If approved, generate ticket + upload
        if approved:
            pdf_bytes = generate_ticket_pdf_bytes(
                name=name,
                uu_roll_no=uu_roll_no,
                course=course,
                dept=dept,
                event_name="Convocation 2025",
                event_date="TBD",              # you said date will be updated later
                venue="United University Auditorium",
                # if your generator supports photo/QR, pass args here
            )
            pdf_filename = f"{uu_roll_no}_ticket.pdf"
            ticket_url = upload_ticket(pdf_bytes, pdf_filename)

        # 5) Insert RSVP record
        rsvp_record = create_rsvp({
            "uu_roll_no": uu_roll_no,
            "name": name,
            "email": email,
            "course": course,
            "dept": dept,
            "rsvp_status": rsvp_status,
            "approved": approved,
            "photo_url": photo_url,
            "ticket_url": ticket_url
        })

        # 6) Email
        if approved and pdf_bytes:
            # send with Brevo (already wired in your mail route)
            send_ticket_email(email, name, ticket_url, pdf_bytes)
        else:
            send_rejection_email(email, name)

        # 7) Response
        return jsonify({
            "success": True,
            "approved": approved,
            "photo_url": photo_url,
            "ticket_url": ticket_url,
            "rsvp": rsvp_record
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/rsvp/status/<string:uu_roll_no>", methods=["GET"])
def check_rsvp_status(uu_roll_no):
    sb = get_client()
    res = sb.table("rsvp_table_cs").select("*").eq("uu_roll_no", uu_roll_no).execute()
    if not res.data:
        return jsonify({"success": True, "status": None, "ticket_url": None})
    rsvp = res.data[0]
    return jsonify({"success": True, "status": rsvp, "ticket_url": rsvp.get("ticket_url")})


@bp.route("/ticket/<string:uu_roll_no>", methods=["GET"])
def get_ticket_url(uu_roll_no):
    sb = get_client()
    res = sb.table("rsvp_table_cs").select("ticket_url").eq("uu_roll_no", uu_roll_no).execute()
    if not res.data:
        return jsonify({"success": False, "error": "Ticket not found"})
    url = res.data[0].get("ticket_url")
    if not url:
        return jsonify({"success": False, "error": "Ticket not generated"})
    return jsonify({"success": True, "ticket_url": url})


