import cv2
import datetime
import time # For time.sleep
import os

def take_photo(output_dir: str = "images"):
    """Captures an image from the default webcam and saves it."""
    os.makedirs(output_dir, exist_ok=True) # Ensure output directory exists

    cap = cv2.VideoCapture(0) # 0 is typically the default webcam
    if not cap.isOpened():
        print("Error: Could not open camera. Make sure it's connected and drivers are installed.")
        return None
    
    # Try to set higher resolution (optional)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Give camera time to warm up (optional but good practice)
    time.sleep(2) 

    ret, frame = cap.read() # Read a frame
    cap.release() # Release the camera immediately
    cv2.destroyAllWindows() # Close any OpenCV windows

    if ret:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"object_photo_{timestamp}.jpg")
        cv2.imwrite(filename, frame)
        print(f"Image saved to {filename}")
        return filename
    else:
        print("Failed to grab frame from camera.")
        return None

def analyze_image_quality(image_path: str):
    """
    Analyzes the quality of a 3D printed object from an image.
    This is a placeholder for your actual computer vision logic.
    """
    print(f"Analyzing image: {image_path}")
    # Load the image
    img = cv2.imread(image_path)
    from supabase_client import QUALITY_STATUS_GOOD, QUALITY_STATUS_BAD, QUALITY_STATUS_UNCERTAIN
    if img is None:
        print(f"Error: Could not load image from {image_path} for analysis.")
        return 0.0, QUALITY_STATUS_UNCERTAIN # Always return a valid int

    # --- Your Computer Vision Logic Goes Here ---
    # Examples:
    # - Grayscale conversion: gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # - Edge detection: edges = cv2.Canny(gray, 100, 200)
    # - Template matching: result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    # - AI model inference: Load your TensorFlow/PyTorch model and predict quality
    
    # For now, a placeholder:
    import random
    quality_score = random.uniform(50.0, 100.0) # Random float score

    # Determine quality status ID based on score thresholds (align with your DB's print_statuses)
    quality_status_id = QUALITY_STATUS_UNCERTAIN # Default
    if quality_score >= 90.0:
        quality_status_id = QUALITY_STATUS_GOOD
    elif quality_score < 70.0:
        quality_status_id = QUALITY_STATUS_BAD
    
    print(f"Analysis result: Score={quality_score:.2f}, Status ID={quality_status_id}")
    return quality_score, quality_status_id