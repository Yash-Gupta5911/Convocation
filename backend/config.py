import os
from dotenv import load_dotenv

load_dotenv()

# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
# Use SERVICE ROLE key on server (NOT the anon key) for inserts/storage ops
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Storage buckets (CS system)
STUDENT_PHOTOS_BUCKET = os.getenv("STUDENT_PHOTOS_BUCKET", "cs-student-photos")
TICKETS_BUCKET = os.getenv("TICKETS_BUCKET", "cs-tickets")

# Email settings (we’ll implement in Step 2)
MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@example.com")

# Safety checks
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in your .env")
