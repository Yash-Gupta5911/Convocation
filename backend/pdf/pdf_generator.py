
#new imports
import io
from datetime import datetime
from typing import Optional

import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import ImageReader

import qrcode
from qrcode.image.pil import PilImage

# Import your Supabase helpers
from database.supabase_client import get_client, TICKETS_BUCKET

#new
PAGE_W, PAGE_H = A4

def _draw_heading(c: canvas.Canvas, title: str):
    c.setFillColor(colors.HexColor("#0B3D91"))  # deep blue header bar
    c.rect(0, PAGE_H - 40, PAGE_W, 40, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20, PAGE_H - 27, title)

def _draw_label_value(c: canvas.Canvas, x, y, label, value, label_w=110):
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.black)
    c.drawString(x, y, f"{label}:")
    c.setFont("Helvetica", 10)
    c.drawString(x + label_w, y, value if value is not None else "")

def _fetch_image_bytes(url: str) -> Optional[bytes]:
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.content
    except Exception:
        return None

def _pil_to_imagereader(pil_img) -> ImageReader:
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)

def _make_qr(data: dict) -> ImageReader:
    qr = qrcode.QRCode(version=2, box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img: PilImage = qr.make_image(fill_color="black", back_color="white")
    return _pil_to_imagereader(img)

def generate_ticket_pdf_bytes(
    *,
    name: str,
    uu_roll_no: str,
    course: str,
    dept: str,
    year_session: str = "2025 Passout",
    event_name: str = "Convocation 2025",
    event_date: Optional[str] = None,
    venue: str = "United University Auditorium",
    photo_url: Optional[str] = None
) -> bytes:

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    # Header bar
    _draw_heading(c, event_name.upper())

    # Ticket meta
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    issue_ts = datetime.now().strftime("%d %b %Y, %H:%M")
    c.drawString(20, PAGE_H - 55, f"Ticket ID: {uu_roll_no}_TKT")
    c.drawString(200, PAGE_H - 55, f"Issued: {issue_ts}")

    # Unified content box
    BOX_X = 15
    BOX_Y = PAGE_H - 400
    BOX_W = PAGE_W - 30
    BOX_H = 320

    c.setStrokeColor(colors.lightgrey)
    c.rect(BOX_X, BOX_Y, BOX_W, BOX_H, stroke=1, fill=0)

    # Photo (top-right inside box)
    if photo_url:
        img_bytes = _fetch_image_bytes(photo_url)
        if img_bytes:
            try:
                img = ImageReader(io.BytesIO(img_bytes))
                ph_w = 32 * mm
                ph_h = 38 * mm
                c.drawImage(
                    img,
                    BOX_X + BOX_W - ph_w - 15,
                    BOX_Y + BOX_H - ph_h - 15,
                    ph_w, ph_h,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except:
                pass

    # Section Header: Attendee Details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(BOX_X + 15, BOX_Y + BOX_H - 40, "Attendee Details")
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.line(BOX_X + 15, BOX_Y + BOX_H - 45, BOX_X + BOX_W - 15, BOX_Y + BOX_H - 45)

    # Attendee fields
    y = BOX_Y + BOX_H - 65
    gap = 18

    _draw_label_value(c, BOX_X + 15, y, "Full Name", name); y -= gap
    _draw_label_value(c, BOX_X + 15, y, "UU Roll No", uu_roll_no); y -= gap
    _draw_label_value(c, BOX_X + 15, y, "Course", course); y -= gap
    _draw_label_value(c, BOX_X + 15, y, "Department", dept); y -= gap
    _draw_label_value(c, BOX_X + 15, y, "Year / Session", year_session); y -= (gap + 10)

    # Section Header: Event Details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(BOX_X + 15, y, "Event Details")
    c.line(BOX_X + 15, y - 5, BOX_X + BOX_W - 15, y - 5)
    y -= 25

    _draw_label_value(c, BOX_X + 15, y, "Event Name", event_name); y -= gap
    _draw_label_value(c, BOX_X + 15, y, "Event Date", event_date or "TBD"); y -= gap
    _draw_label_value(c, BOX_X + 15, y, "Venue", venue); y -= gap

    # QR Code inside box, bottom-right
    qr_data = {
        "name": name,
        "uu_roll_no": uu_roll_no,
        "course": course,
        "dept": dept,
        "event": event_name,
        "year_session": year_session,
        "venue": venue,
        "event_date": event_date or "TBD"
    }
    qr_img = _make_qr(qr_data)
    qr_size = 40 * mm

    c.drawImage(
        qr_img,
        BOX_X + BOX_W - qr_size - 15,
        BOX_Y + 20,
        qr_size,
        qr_size,
        mask='auto'
    )

    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.darkgrey)
    c.drawString(20, 20, "Please carry a valid photo ID. Entry subject to verification.")

    c.showPage()
    c.save()

    buf.seek(0)
    return buf.read()


# def create_and_upload_ticket(
#     *,
#     name: str,
#     uu_roll_no: str,
#     course: str,
#     dept: str,
#     photo_url: Optional[str] = None,
#     year_session: str = "2025 Passout",
#     event_name: str = "Convocation 2025",
#     event_date: Optional[str] = None,  # update later when decided
#     venue: str = "United University Auditorium",
# ) -> str:
#     """
#     Generates the ticket PDF and uploads it to Supabase Storage.
#     Returns the public URL to the uploaded ticket.
#     """
#     pdf_bytes = generate_ticket_pdf_bytes(
#         name=name,
#         uu_roll_no=uu_roll_no,
#         course=course,
#         dept=dept,
#         year_session=year_session,
#         event_name=event_name,
#         event_date=event_date,
#         venue=venue,
#         photo_url=photo_url
#     )

#     sb = get_client()
#     safe_name = name.replace(" ", "_")
#     object_name = f"{safe_name}_{uu_roll_no}.pdf"

#     # upload with upsert so re-generating replaces it
#     sb.storage.from_(TICKETS_BUCKET).upload(
#         object_name,
#         pdf_bytes,
#         {
#             "contentType": "application/pdf",
#             "upsert": "true"   # MUST be string
#         }
#     )

#     # build public URL
#     # NOTE: if your bucket is private, switch to get_public_url() or signed URLs
#     public_url = sb.storage.from_(TICKETS_BUCKET).get_public_url(object_name)
#     return public_url



def create_and_upload_ticket(
    *,
    name: str,
    uu_roll_no: str,
    course: str,
    dept: str,
    photo_url: Optional[str] = None,
    year_session: str = "2025 Passout",
    event_name: str = "Convocation 2025",
    event_date: Optional[str] = None,
    venue: str = "United University Auditorium",
) -> str:

    # Generate PDF
    pdf_bytes = generate_ticket_pdf_bytes(
        name=name,
        uu_roll_no=uu_roll_no,
        course=course,
        dept=dept,
        year_session=year_session,
        event_name=event_name,
        event_date=event_date,
        venue=venue,
        photo_url=photo_url
    )

    sb = get_client()

    # ✅ Fix file name: Name_RollNo.pdf
    safe_name = name.replace(" ", "_")
    object_name = f"{safe_name}_{uu_roll_no}.pdf"

    # Upload
    sb.storage.from_(TICKETS_BUCKET).upload(
        object_name,
        pdf_bytes,
        {
            "contentType": "application/pdf",
            "upsert": "true"
        }
    )

    public_url = sb.storage.from_(TICKETS_BUCKET).get_public_url(object_name)
    return public_url
