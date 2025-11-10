from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

def generate_ticket_pdf_bytes(
        name,
        uu_roll_no,
        course,
        dept,
        event_name,
        event_date,
        venue
    ):
    buffer = BytesIO()

    # Create canvas
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    p.setFont("Helvetica-Bold", 24)
    p.drawString(100, height - 80, event_name)

    # Details
    p.setFont("Helvetica", 14)
    p.drawString(100, height - 130, f"Name: {name}")
    p.drawString(100, height - 150, f"UU Roll No: {uu_roll_no}")
    p.drawString(100, height - 170, f"Course: {course}")
    p.drawString(100, height - 190, f"Dept: {dept}")
    p.drawString(100, height - 210, f"Event Date: {event_date}")
    p.drawString(100, height - 230, f"Venue: {venue}")

    # Finalize
    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()



