import time
import threading
import os
import requests
from supabase_client import (
    get_queued_prints, update_print_status, update_print_quality_and_finish,
    STATUS_QUEUED, STATUS_INSPECTION_PENDING,
    STATUS_PRINTING, STATUS_FAILED, STATUS_COMPLETED, QUALITY_STATUS_GOOD,
    QUALITY_STATUS_BAD, QUALITY_STATUS_UNCERTAIN
)
from camera_controller import take_photo_with_zivid, analyze_image_quality
from socket_server import start_socket_server, send_command_to_pi, get_pi_message, is_pi_connected

def download_stl_from_supabase(stl_url: str, print_id: int) -> str:
    """Downloads the STL file from the given URL and saves it to data/raw/. Returns the local path."""
    local_stl_path = os.path.join("data/raw", f"print_{print_id}.stl")
    response = requests.get(stl_url)
    response.raise_for_status()
    with open(local_stl_path, "wb") as f:
        f.write(response.content)
    print(f"Downloaded STL to {local_stl_path}")
    return local_stl_path

# --- Main Orchestration Logic ---
def orchestrate_workflow():
    print("NUC Orchestrator started. Waiting for Pi connection and new jobs.")
    
    while True:
        # 1. Ensure Pi is connected
        if not is_pi_connected():
            print("NUC Orchestrator: Waiting for Raspberry Pi connection...")
            time.sleep(5)
            continue
        
        # 2. Check for new print jobs in Supabase
        queued_jobs = get_queued_prints()
        if not queued_jobs:
            time.sleep(10)
            continue

        for job in queued_jobs:
            print_id = job['id']
            print(f"\n--- Processing new job #{print_id}: '{job['title']}' ---")
            try:
                update_print_status(print_id, STATUS_PRINTING)
                print(f"Simulating 3D print for job #{print_id}...")
                time.sleep(5)
                print(f"Simulated print complete for job #{print_id}.")

                # --- Robotic arm grabs the print and moves it in place ---
                command_sent = send_command_to_pi(f"ROBOT_PICKUP_PRINT {print_id}")
                if not command_sent: raise Exception("Failed to send pickup command to Pi.")
                if not wait_for_pi_response("ROBOT_PICKUP_COMPLETE", timeout=60):
                    raise Exception("Pi did not confirm ROBOT_PICKUP_COMPLETE in time.")
                print(f"Pi confirmed pickup for job #{print_id}.")

                # --- Take a photo with Zivid ---
                image_file, zdf_file, ply_file = take_photo_with_zivid(output_dir="data/raw")
                if not image_file:
                    raise Exception("Failed to take photo with Zivid.")
                print(f"Photo taken for job #{print_id}: {image_file}")
                photo_path = image_file  # for downstream analysis

                # --- Analyze the photo ---
                quality_score, quality_status_id = analyze_image_quality(photo_path)
                if quality_status_id is None:
                    quality_status_id = QUALITY_STATUS_UNCERTAIN
                print(f"Analysis complete: Score={quality_score}, Status={quality_status_id}")

                # --- Update Supabase with quality results ---
                update_print_quality_and_finish(print_id, quality_status_id)
                print(f"DB updated with quality for job #{print_id}.")

                # --- Command the robot to place the item accordingly ---
                placement_command = f"ROBOT_PLACE_GOOD {print_id}" if quality_status_id == QUALITY_STATUS_GOOD else f"ROBOT_PLACE_BAD {print_id}"
                command_sent = send_command_to_pi(placement_command)
                if not command_sent: raise Exception("Failed to send placement command to Pi.")
                expected_response = "ROBOT_PLACE_GOOD_COMPLETE" if quality_status_id == QUALITY_STATUS_GOOD else "ROBOT_PLACE_BAD_COMPLETE"
                if not wait_for_pi_response(expected_response, timeout=30):
                    raise Exception("Pi did not confirm ROBOT_PLACE_COMPLETE in time.")
                print(f"Pi confirmed placement for job #{print_id}.")

                update_print_status(print_id, STATUS_COMPLETED, ended_at='now()')
                print(f"Job #{print_id} completed successfully.")

            except Exception as e:
                print(f"Error processing job #{print_id}: {e}")
                update_print_status(print_id, STATUS_FAILED, ended_at='now()')
            time.sleep(5)

def wait_for_pi_response(expected_response: str, timeout: int = 30):
    """Waits for a specific message from the Pi within a timeout period."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        msg = get_pi_message()
        if msg:
            if msg == expected_response:
                return True
            else:
                print(f"NUC Orchestrator: Received unexpected message from Pi: '{msg}'")
        time.sleep(0.1) # Check frequently
    return False # Timeout

if __name__ == "__main__":
    # Start the socket server in a separate thread
    socket_server_thread = threading.Thread(target=start_socket_server, daemon=True)
    socket_server_thread.start()
    
    # Start the main orchestration loop
    orchestrate_workflow()