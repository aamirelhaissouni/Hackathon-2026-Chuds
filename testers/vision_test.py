import cv2
import numpy as np
from picamera2 import Picamera2
from deepface import DeepFace
import time
import threading  # We import the threading module

# --- Threading & Shared Data ---
# These variables will be shared between the main (video) thread
# and the (AI) worker thread.
data_lock = threading.Lock()
latest_frame = None
player_1_emotion = "unknown"
player_2_emotion = "unknown"
player_1_race = "unknown"
player_2_race = "unknown"
player_1_box = None
player_2_box = None
app_running = True  # A flag to tell the thread to stop

# --- SETTINGS ---
# We can now afford a more accurate, slower analysis
ANALYSIS_INTERVAL = 0.5  # Run analysis every 0.5 seconds
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CENTER_LINE = CAMERA_WIDTH / 2

# --- FONT & BOX for drawing ---
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7
FONT_COLOR = (255, 255, 255)  # White
BOX_COLOR = (0, 255, 0)      # Green
LINE_TYPE = 2

# ===================================================================
# This function runs in the background thread
# ===================================================================
def analysis_worker():
    global latest_frame, data_lock, app_running
    global player_1_emotion, player_2_emotion, player_1_race, player_2_race, player_1_box, player_2_box

    print("Analysis thread started.")
    
    while app_running:
        frame_to_analyze = None
        
        # 1. Safely get a copy of the latest frame
        with data_lock:
            if latest_frame is not None:
                frame_to_analyze = latest_frame.copy()

        if frame_to_analyze is None:
            time.sleep(ANALYSIS_INTERVAL)
            continue
            
        # 2. Run the HEAVY analysis (this is the slow part)
        try:
            # OPTIMIZATION: DeepFace prefers RGB, so we give it the RGB frame
            results = DeepFace.analyze(
                img_path=frame_to_analyze,
                actions=['emotion', 'race'],
                enforce_detection=False,
                silent=True,
                # --- TRY THESE FOR ACCURACY vs SPEED ---
                # detector_backend = 'ssd'  # Faster, less accurate
                detector_backend = 'mtcnn' # Slower, MUCH more accurate
                # detector_backend = 'opencv' # Default
            )
            
            # --- Reset values ---
            p1_emotion, p1_race, p1_box = "unknown", "unknown", None
            p2_emotion, p2_race, p2_box = "unknown", "unknown", None

            if isinstance(results, list) and len(results) > 0:
                for face in results:
                    face_x = face['region']['x']
                    emotion = face['dominant_emotion']
                    race = face['dominant_race']
                    
                    # Re-map 'fear' to 'angry'
                    if emotion == "fear":
                        emotion = "angry"  # Use ONE '='

                    if face_x < CENTER_LINE:
                        p1_emotion, p1_race, p1_box = emotion, race, face['region']
                    else:
                        p2_emotion, p2_race, p2_box = emotion, race, face['region']
            
            # 3. Safely update the global variables
            with data_lock:
                player_1_emotion, player_1_race, player_1_box = p1_emotion, p1_race, p1_box
                player_2_emotion, player_2_race, player_2_box = p2_emotion, p2_race, p2_box

        except Exception as e:
            # print(f"Analysis error: {e}")
            with data_lock:
                # Clear boxes if analysis fails
                player_1_box, player_2_box = None, None

        # 4. Wait for the next interval
        time.sleep(ANALYSIS_INTERVAL)
    
    print("Analysis thread stopped.")

# ===================================================================
# This is the Main Thread
# ===================================================================
if __name__ == "__main__":
    try:
        # -- Initialize piccam2 --
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (CAMERA_WIDTH, CAMERA_HEIGHT)}))
        picam2.start()
        print("Camera warming up...")
        time.sleep(1.0)
    except Exception as e:
        print(f"Error initializing camera: {e}")
        exit()

    # --- Start the Analysis Thread ---
    analysis_thread = threading.Thread(target=analysis_worker, daemon=True)
    analysis_thread.start()

    print("Starting camera feed. Press 'q' to quit.")

    try:
        while True:
            # 1. Read a frame (FAST)
            frame_rgb = picam2.capture_array()
            
            # 2. Update the shared frame for the worker thread (FAST)
            with data_lock:
                latest_frame = frame_rgb.copy()
            
            # 3. Convert to BGR for OpenCV drawing (FAST)
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            
            # 4. Read shared variables (FAST)
            with data_lock:
                # Make local copies so we don't hold the lock
                p1_emo_copy, p1_race_copy, p1_box_copy = player_1_emotion, player_1_race, player_1_box
                p2_emo_copy, p2_race_copy, p2_box_copy = player_2_emotion, player_2_race, player_2_box

            # 5. Draw player info on the BGR frame (FAST)
            
            # --- Draw Player 1 (Left) Info ---
            cv2.putText(frame_bgr, f"Player 1: {p1_emo_copy} ({p1_race_copy})",
                        (10, 30), FONT, FONT_SCALE, FONT_COLOR, LINE_TYPE)
            if p1_box_copy:
                x, y, w, h = p1_box_copy['x'], p1_box_copy['y'], p1_box_copy['w'], p1_box_copy['h']
                cv2.rectangle(frame_bgr, (x, y), (x+w, y+h), BOX_COLOR, LINE_TYPE)

            # --- Draw Player 2 (Right) Info ---
            cv2.putText(frame_bgr, f"Player 2: {p2_emo_copy} ({p2_race_copy})",
                        (int(CENTER_LINE) + 10, 30), FONT, FONT_SCALE, FONT_COLOR, LINE_TYPE)
            if p2_box_copy:
                x, y, w, h = p2_box_copy['x'], p2_box_copy['y'], p2_box_copy['w'], p2_box_copy['h']
                cv2.rectangle(frame_bgr, (x, y), (x+w, y+h), BOX_COLOR, LINE_TYPE)

            # 6. Display the frame (FAST)
            cv2.imshow("Live Test Feed - Press 'q' to quit", frame_bgr)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Clean up
        print("Stopping threads and camera...")
        app_running = False  # Signal the thread to stop
        analysis_thread.join() # Wait for thread to finish
        picam2.stop()
        cv2.destroyAllWindows()
        print("Test script finished.")

