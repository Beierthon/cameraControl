import time
import threading
from supabase_client import (
    get_queued_prints, update_print_status, update_print_quality_and_finish,
    upload_image_to_supabase, STATUS_QUEUED, STATUS_INSPECTION_PENDING,
    STATUS_PRINTING, STATUS_FAILED, STATUS_COMPLETED, QUALITY_STATUS_GOOD,
    QUALITY_STATUS_BAD, QUALITY_STATUS_UNCERTAIN
)
from camera_controller import take_photo, analyze_image_quality
from socket_server import start_socket_server, send_command_to_pi, get_pi_message, is_pi_connected

# --- Main Orchestration Logic ---
def orchestrate_workflow():
    print("NUC Orchestrator started. Waiting for Pi connection and new jobs.")
    
    while True:
        # 1. Ensure Pi is connected
        if not is_pi_connected():
            print("NUC Orchestrator: Waiting for Raspberry Pi connection...")
            time.sleep(5) # Wait for Pi to connect
            continue
        
        # 2. Check for new print jobs in Supabase
        queued_jobs = get_queued_prints()
        if not queued_jobs:
            # print("NUC Orchestrator: No queued jobs. Waiting...")
            time.sleep(10) # Check less frequently if no jobs
            continue

        for job in queued_jobs:
            print_id = job['id']
            print(f"\n--- Processing new job #{print_id}: '{job['title']}' ---")

            try:
                # Update DB status: Queued -> Printing
                update_print_status(print_id, STATUS_PRINTING)
                
                # Assume 3D printing is happening here. This might be a physical delay
                # or triggered by an external event/OctoPrint API.
                # For this setup, we simulate the printer's completion.
                print(f"Simulating 3D print for job #{print_id}...")
                time.sleep(30) # Simulate printing time (adjust as needed)
                print(f"Simulated print complete for job #{print_id}.")

                # Robot action: Pickup print from printer bed and move to camera position
                command_sent = send_command_to_pi(f"ROBOT_PICKUP_PRINT {print_id}")
                if not command_sent: raise Exception("Failed to send pickup command to Pi.")

                # Wait for Pi's confirmation (e.g., "ROBOT_PICKUP_COMPLETE")
                if not wait_for_pi_response("ROBOT_PICKUP_COMPLETE", timeout=60):
                    raise Exception("Pi did not confirm ROBOT_PICKUP_COMPLETE in time.")
                print(f"Pi confirmed pickup for job #{print_id}.")

                # Take photo
                photo_path = take_photo(output_dir="nuc_images")
                if not photo_path: raise Exception("Failed to take photo.")
                print(f"Photo taken for job #{print_id}.")

                # Upload photo to Supabase Storage
                image_url = upload_image_to_supabase(photo_path, bucket_name="printed-objects")
                if not image_url: raise Exception("Failed to upload image to Supabase.")
                print(f"Image uploaded for job #{print_id}: {image_url}")

                # Analyze image quality
                quality_score, quality_status_id = analyze_image_quality(photo_path)
                print(f"Analysis complete: Score={quality_score}, Status={quality_status_id}")

                # Update DB with quality results and mark as ended
                update_print_quality_and_finish(print_id, quality_score, quality_status_id, image_url)
                print(f"DB updated with quality for job #{print_id}.")

                # Robot action: Place object in good/bad bin based on quality
                placement_command = f"ROBOT_PLACE_GOOD {print_id}" if quality_status_id == QUALITY_STATUS_GOOD else f"ROBOT_PLACE_BAD {print_id}"
                command_sent = send_command_to_pi(placement_command)
                if not command_sent: raise Exception("Failed to send placement command to Pi.")

                # Wait for Pi's confirmation
                expected_response = "ROBOT_PLACE_GOOD_COMPLETE" if quality_status_id == QUALITY_STATUS_GOOD else "ROBOT_PLACE_BAD_COMPLETE"
                if not wait_for_pi_response(expected_response, timeout=30):
                    raise Exception("Pi did not confirm ROBOT_PLACE_COMPLETE in time.")
                print(f"Pi confirmed placement for job #{print_id}.")

                update_print_status(print_id, STATUS_COMPLETED, ended_at='now()') # Final status if everything went well
                print(f"Job #{print_id} completed successfully.")

            except Exception as e:
                print(f"Error processing job #{print_id}: {e}")
                update_print_status(print_id, STATUS_FAILED, ended_at='now()') # Mark as failed
                # Optionally send a 'reset' command to the Pi if it's in a bad state
                # send_command_to_pi("ROBOT_RESET")

            time.sleep(5) # Small delay before checking for next job

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