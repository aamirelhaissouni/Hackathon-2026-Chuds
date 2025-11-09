import cv2
import numpy as np
from picamera2 import Picamera2
from deepface import DeepFace
import time

try:
    # -- Initialize piccam2 --
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
    picam2.start()
    time.sleep(2)  # Allow camera to warm up

except RuntimeError as e:
    print(f"Error initializing camera: {e}")
    exit()


# --- SETTINGS ---
ANALYSIS_INTERVAL = 0.3  # (in seconds)
last_analysis_time = 0

# --- FONT & BOX for drawing ---
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.7
FONT_COLOR = (255, 255, 255)  # White
BOX_COLOR = (0, 255, 0)      # Green
LINE_TYPE = 2


# --- Initialize player emotion AND box variables ---
# These will store the "last known" state
player_1_emotion = "unknown"
player_2_emotion = "unknown"
player_1_race = "unknown"
player_2_race = "unknown"
player_1_box = None  # This will store the {'x', 'y', 'w', 'h'} dict
player_2_box = None

print("Starting camera feed. Press 'q' to quit.")

try:
    while True:
        # 1. Read a frame (this is fast)
        frame_rgba = picam2.capture_array()
        ##convert the fram colors so it wokrks with cv2
        frame = cv2.cvtColor(frame_rgba, cv2.COLOR_RGBA2BGR)
        current_time = time.time()
        
        # 2. Run HEAVY analysis only on the interval
        if current_time - last_analysis_time > ANALYSIS_INTERVAL:
            last_analysis_time = current_time
            
            frame_height, frame_width, _ = frame.shape
            center_line = frame_width / 2

            try:
                results = DeepFace.analyze(
                    img_path=frame.copy(),
                    actions=['emotion', 'race'],
                    enforce_detection=False,
                    silent=True
                )

                # --- NEW: Reset boxes on each new analysis ---
                # This ensures old boxes disappear if faces are no longer found
                player_1_emotion = "unknown"
                player_2_emotion = "unknown"
                player_1_box = None
                player_2_box = None
                
                if isinstance(results, list) and len(results) > 0:
                    for face in results:
                        face_x = face['region']['x']
                        emotion = face['dominant_emotion']
                        race = face['dominant_race']
                        
                        if face_x < center_line:
                            player_1_emotion = emotion
                            player_1_race = race
                            player_1_box = face['region'] # <-- STORE THE BOX
                        else:
                            player_2_emotion = emotion
                            player_2_race = race
                            player_2_box = face['region'] # <-- STORE THE BOX
                
            except Exception as e:
                player_1_emotion = "unknown"
                player_2_emotion = "unknown"
                player_1_race = "unknown"
                player_2_race = "unknown"
                player_1_box = None
                player_2_box = None

        # 3. Draw player info on *every* frame (this is fast)
        frame_height, frame_width, _ = frame.shape
        
        # --- Draw Player 1 (Left) Info ---
        cv2.putText(
            img=frame,
            text=f"Player 1 (Left): Emotion:{player_1_emotion}, Race: {player_1_race}",
            org=(10, 30),
            fontFace=FONT,
            fontScale=FONT_SCALE,
            color=FONT_COLOR,
            thickness=LINE_TYPE
        )
        # --- NEW: Draw Player 1 Box if we have one ---
        if player_1_box:
            x, y, w, h = player_1_box['x'], player_1_box['y'], player_1_box['w'], player_1_box['h']
            cv2.rectangle(frame, (x, y), (x+w, y+h), BOX_COLOR, LINE_TYPE)

        # --- Draw Player 2 (Right) Info ---
        cv2.putText(
            img=frame,
            text=f"Player 2 (Right): Emotion: {player_2_emotion}, Race: {player_2_race}",
            org=(int(frame_width / 2) + 10, 30),
            fontFace=FONT,
            fontScale=FONT_SCALE,
            color=FONT_COLOR,
            thickness=LINE_TYPE
        )
        # --- NEW: Draw Player 2 Box if we have one ---
        if player_2_box:
            x, y, w, h = player_2_box['x'], player_2_box['y'], player_2_box['w'], player_2_box['h']
            cv2.rectangle(frame, (x, y), (x+w, y+h), BOX_COLOR, LINE_TYPE)


        # 4. Display the frame (this is fast)
        cv2.imshow("Live Test Feed - Press 'q' to quit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up
    picam2.stop()
    cv2.destroyAllWindows()
    print("Test script finished.")