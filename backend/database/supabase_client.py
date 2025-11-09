from typing import Optional, Tuple
from supabase import create_client, Client
import io
#from . import typing as _  # ignore; just to keep relative imports happy
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, STUDENT_PHOTOS_BUCKET, TICKETS_BUCKET

_client: Optional[Client] = None

def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _client

# ---------- DB helpers ----------
def get_student_by_uuid(uu_roll_no: str) -> Optional[dict]:
    sb = get_client()
    res = sb.table("student_master_cs").select("*").eq("uu_roll_no", uu_roll_no).limit(1).execute()
    data = res.data or []
    return data[0] if data else None

def create_rsvp(data):
    sb = get_client()
    res = sb.table("rsvp_table_cs").insert(data).execute()
    return res.data[0] if res.data else None


def update_rsvp_ticket(rsvp_id: int, ticket_url: str) -> None:
    sb = get_client()
    sb.table("rsvp_table_cs").update({"ticket_url": ticket_url}).eq("id", rsvp_id).execute()

# ---------- Storage helpers ----------
def upload_bytes_to_bucket(bucket: str, object_name: str, data: bytes, content_type: str) -> str:
    sb = get_client()

    # Remove existing object if exists
    try:
        sb.storage.from_(bucket).remove([object_name])
    except Exception:
        pass

    # Upload new file
    sb.storage.from_(bucket).upload(
        object_name,
        data,
        file_options={
            "content-type": content_type,
            "upsert": "true"
        }
    )

    # Return public URL
    return sb.storage.from_(bucket).get_public_url(object_name)


def upload_photo(photo_bytes: bytes, filename: str) -> str:
    # store under uu_roll_no/filename for neatness
    object_name = filename
    return upload_bytes_to_bucket(STUDENT_PHOTOS_BUCKET, object_name, photo_bytes, "image/jpeg")

def upload_ticket(pdf_bytes: bytes, filename: str) -> str:
    return upload_bytes_to_bucket(TICKETS_BUCKET, filename, pdf_bytes, "application/pdf")
