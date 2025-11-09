import cv2
import numpy as np
import time
import threading

# project modules
try:
    from picamera2 import Picamera2
    from deepface import DeepFace      
    from audio import Speaker      
except ImportError as e:
    print(f"FATAL ERROR: Failed to import a module. {e}")
    print("Please ensure audio.py, picamera2, and deepface are available.")
    exit()

# threading
data_lock = threading.Lock()
latest_frame = None
player_1_emotion = "unknown"
player_2_emotion = "unknown"
player_1_box = None
player_2_box = None
app_running = True  # flag for thread 

# camera/capture settings
ANALYSIS_INTERVAL = 0.5  # run analysis every 0.5 seconds
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CENTER_LINE = CAMERA_WIDTH / 2

# cooldowns
AUDIO_COOLDOWN = 5.0  # 5 seconds before a new alert
player_1_last_alert = 0.0
player_2_last_alert = 0.0

# font and box
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7
FONT_COLOR = (255, 255, 255)  # White
BOX_COLOR = (0, 255, 0)      # Green
LINE_TYPE = 2

# This function runs in the background thread
def analysis_worker():
    """
    This worker thread handles the slow DeepFace analysis in the background
    so the main video feed never lags.
    """
    global latest_frame, data_lock, app_running
    global player_1_emotion, player_2_emotion, player_1_box, player_2_box

    print("[Analysis Thread] Started.")

    while app_running:
        frame_to_analyze = None

        # 1. Safely get a copy of the latest frame
        with data_lock:
            if latest_frame is not None:
                # We work on a copy so the main thread can keep updating
                frame_to_analyze = latest_frame.copy()

        if frame_to_analyze is None:
            time.sleep(ANALYSIS_INTERVAL)  # Wait for first frame
            continue

        # 2. Run the HEAVY analysis (this is the slow part)
        try:
            results = DeepFace.analyze(
                img_path=frame_to_analyze,
                actions=['emotion'],
                enforce_detection=False,  # Don't crash if no face
                silent=True,
                detector_backend='mtcnn'
            )

            # analyis variables
            p1_emotion, p1_box = "unknown", None
            p2_emotion, p2_box = "unknown", None

            if isinstance(results, list) and len(results) > 0:
                for face in results:
                    face_x = face['region']['x']
                    emotion = face['dominant_emotion']

                    if emotion == "fear":
                        emotion = "angry"

                    if face_x < CENTER_LINE:
                        p1_emotion, p1_box = emotion, face['region']
                    else:
                        p2_emotion, p2_box = emotion, face['region']

            # 3. Safely update the global variables
            with data_lock:
                player_1_emotion = p1_emotion
                player_2_emotion = p2_emotion
                player_1_box = p1_box
                player_2_box = p2_box

        except Exception as e:
            # print(f"[Analysis Thread] Error: {e}")
            with data_lock:
                # Clear boxes if analysis fails
                player_1_emotion = "unknown"
                player_2_emotion = "unknown"
                player_1_box = None
                player_2_box = None

        # 4. Wait for the next interval
        time.sleep(ANALYSIS_INTERVAL)

    print("[Analysis Thread] Stopped.")

# main thread
def main_app():
    global latest_frame, data_lock, app_running
    global player_1_last_alert, player_2_last_alert

    # initialize modules
    print("[Main Thread] Initializing modules...")
    try:
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration(main={"format": 'RGB888', "size": (CAMERA_WIDTH, CAMERA_HEIGHT)}))
        picam2.start()
        print("[Main Thread] Camera initialized.")
        time.sleep(1.0)
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize camera: {e}")
        return

    # Initialize our hardware 
    speaker = Speaker()
    print("[Main Thread] Audio module initialized.")

    # --- 2. Start the Analysis Thread ---
    analysis_thread = threading.Thread(target=analysis_worker, daemon=True)
    analysis_thread.start()

    print("[Main Thread] Starting video feed. Press 'q' to quit.")

    try:
        while True:
            current_time = time.time()

            # --- 1. Read Frame (FAST) ---
            frame_bgr = picam2.capture_array()

            # --- 2. Update Shared Frame (FAST) ---
            with data_lock:
                latest_frame = frame_bgr.copy()

            # --- 4. Read Shared AI Data (FAST) ---
            with data_lock:
                # Make local copies so we don't hold the lock
                p1_emo_copy, p1_box_copy = player_1_emotion, player_1_box
                p2_emo_copy, p2_box_copy = player_2_emotion, player_2_box

            # --- 5. Check Hardware Triggers (FAST) ---
            # All hardware/mic logic removed

            # --- 6. ALERT LOGIC (Replaces Roasting) ---

            # --- Player 1 (Left) Alert ---
            if p1_emo_copy == 'angry' and (current_time - player_1_last_alert > AUDIO_COOLDOWN):
                print("[Main Thread] ALERT: Player 1 (Left) is angry")

                # Use a simple string, not the roaster
                alert_text = "Player one seems angry."
                speaker.speak(alert_text)

                player_1_last_alert = current_time

            # --- Player 2 (Right) Alert ---
            elif p2_emo_copy == 'angry' and (current_time - player_2_last_alert > AUDIO_COOLDOWN):
                print("[Main Thread] ALERT: Player 2 (Right) is angry")

                # Use a simple string, not the roaster
                alert_text = "Player two is looking mad."
                speaker.speak(alert_text)

                player_2_last_alert = current_time

            # --- 7. Draw Overlay on Video Feed (FAST) ---
            
            # --- Draw Player 1 (Left) Info ---
            cv2.putText(frame_bgr, f"P1: {p1_emo_copy}", (10, 30), FONT, FONT_SCALE, FONT_COLOR, LINE_TYPE)
            if p1_box_copy:
                x, y, w, h = p1_box_copy['x'], p1_box_copy['y'], p1_box_copy['w'], p1_box_copy['h']
                cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), BOX_COLOR, 2)

            # --- Draw Player 2 (Right) Info ---
            cv2.putText(frame_bgr, f"P2: {p2_emo_copy}", (int(CENTER_LINE) + 10, 30), FONT, FONT_SCALE, FONT_COLOR, LINE_TYPE)
            if p2_box_copy:
                x, y, w, h = p2_box_copy['x'], p2_box_copy['y'], p2_box_copy['w'], p2_box_copy['h']
                cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), BOX_COLOR, 2)

            # 8. Display the frame (FAST)
            cv2.imshow("Rage-O-Meter - Press 'q' to quit", frame_bgr)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # 9. Clean up
        print("[Main Thread] Stopping threads and hardware...")
        app_running = False  # Signal the analysis thread to stop
        analysis_thread.join()  # Wait for thread to finish
        picam2.stop()
        cv2.destroyAllWindows()
        print("[Main Thread] Shutdown complete.")

# starts app
if __name__ == "__main__":
    main_app()