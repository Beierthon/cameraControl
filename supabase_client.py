import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and Key must be set in .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Supabase Table IDs (replace with your actual IDs) ---
# It's good practice to map these for clarity
STATUS_QUEUED = 1
STATUS_PRINTING = 2
STATUS_CANCELED = 3
STATUS_COMPLETED = 4
STATUS_FAILED = 5
STATUS_INSPECTION_PENDING = 6
STATUS_IN_INSPECTION = 7

# Add quality status IDs if you create a separate table for them
QUALITY_STATUS_GOOD = 1 # Example ID if you add a 'quality_statuses' table
QUALITY_STATUS_BAD = 2
QUALITY_STATUS_UNCERTAIN = 3


def get_queued_prints():
    """Fetches print jobs with 'queued' status."""
    try:
        response = supabase.from_('prints').select('*').eq('status', STATUS_QUEUED).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching queued prints: {e}")
        return []

def get_print_by_id(print_id: int):
    """Fetches a single print job by its ID."""
    try:
        response = supabase.from_('prints').select('*').eq('id', print_id).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching print job {print_id}: {e}")
        return None

def update_print_status(print_id: int, new_status_id: int, started_at=None, ended_at=None):
    """Updates the status of a print job."""
    update_data = {'status': new_status_id}
    if new_status_id == STATUS_PRINTING and started_at is None: # Assuming 'printing' means it just started
        update_data['started_at'] = 'now()'
    if ended_at is not None:
        update_data['ended_at'] = 'now()'
        
    try:
        response = supabase.from_('prints').update(update_data).eq('id', print_id).execute()
        if response.data:
            print(f"Successfully updated print {print_id} status to {new_status_id}.")
        return response.data
    except Exception as e:
        print(f"Error updating print {print_id} status to {new_status_id}: {e}")
        return None

def update_print_quality_and_finish(print_id: int, quality_score: float, quality_status_id: int, image_url: str):
    """Updates print job with quality analysis results and sets ended_at."""
    try:
        response = supabase.from_('prints').update({
            'quality_score': quality_score, # Make sure you add this column to your DB!
            'quality_status_id': quality_status_id, # Make sure you add this column to your DB!
            'object_image_url': image_url, # Make sure you add this column to your DB!
            'ended_at': 'now()'
        }).eq('id', print_id).execute()
        if response.data:
            print(f"Successfully updated print {print_id} with quality results.")
        return response.data
    except Exception as e:
        print(f"Error updating print {print_id} with quality results: {e}")
        return None

def upload_image_to_supabase(image_path: str, bucket_name: str = "printed-objects"):
    """Uploads an image file to Supabase Storage and returns its public URL."""
    try:
        # Use your JS logic converted to Python: Date.now()_filename.jpg
        file_name = f"{int(time.time())}_{os.path.basename(image_path)}" # Ensure unique filename
        
        with open(image_path, 'rb') as f:
            res = supabase.storage.from_(bucket_name).upload(file_name, f)
            # You might need to handle the 'res' object to ensure success
            # Supabase-py's upload returns a StorageFile object if successful
        
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        if public_url:
            print(f"Image uploaded to: {public_url}")
            return public_url
        else:
            print("Failed to get public URL after upload.")
            return None
    except Exception as e:
        print(f"Error uploading image to Supabase Storage: {e}")
        return None

# Add a function for real-time listener if you want to use that approach
# However, polling the DB for 'queued' jobs is simpler to start.
# Realtime: https://supabase.com/docs/guides/realtime/client-libraries/python