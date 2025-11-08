import cv2
from deepface import DeepFace
import time

def run_vision_test():
    """
    This function runs the full test for the camera and DeepFace.
    """
    print("CV Test Script Loaded.")
    print(f"OpenCV version: {cv2.__version__}")

    # --- GOAL 1 & 2: Connect and Show Camera ---
    cap = cv2.VideoCapture(0) # 0 is usually the default. May be 1.
    if not cap.isOpened():
        print("FATAL ERROR: Could not open camera.")
        return # Exit the function
        
    print("Camera connected. Starting feed...")

    # --- GOAL 3 & 4: Analyze Emotions in Real Time ---

    # We'll analyze once per interval to save performance
    analysis_interval = 3  # seconds
    last_analysis_time = 0

    try:
        while True:
            # Get a single frame
            ret, frame = cap.read()
            if not ret:
                print("Error: Can't receive frame. Exiting.")
                break

            current_time = time.time()
            
            # Get the dimensions for 2-player logic
            try:
                frame_height, frame_width, _ = frame.shape
                center_line = frame_width // 2
            except Exception as e:
                print(f"Error reading frame shape: {e}")
                continue

            # --- This is a 'copy' of the frame we will draw on ---
            display_frame = frame.copy()

            # --- Run analysis only on the interval ---
            if current_time - last_analysis_time > analysis_interval:
                last_analysis_time = current_time
                print("\n--- RUNNING ANALYSIS ---")

                try:
                    # This is the magic line.
                    # It finds ALL faces and analyzes them.
                    results = DeepFace.analyze(
                        img_path=frame,
                        actions=['emotion'],
                        enforce_detection=False, # Don't crash if no face found
                        silent=True              # Hide DeepFace's internal logs
                    )
                    
                    # 'results' is a LIST of dictionaries, one per face.
                    print(f"Faces found: {len(results)}")

                    # --- GOAL 4: 2-Player Logic ---
                    for face in results:
                        x = face['region']['x']
                        w = face['region']['w']
                        y = face['region']['y']
                        h = face['region']['h']
                        
                        emotion = face['dominant_emotion']
                        
                        # Draw a box on the display_frame
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                        # Determine player and print
                        if x + (w/2) < center_line: # Use center of face for better accuracy
                            print(f"LEFT PLAYER: {emotion}")
                            cv2.putText(display_frame, f"LEFT: {emotion}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        else:
                            print(f"RIGHT PLAYER: {emotion}")
                            cv2.putText(display_frame, f"RIGHT: {emotion}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                except Exception as e:
                    # This catches errors if DeepFace fails
                    print(f"Analysis error: {e}")
            
            
            # Draw the center line for testing
            cv2.line(display_frame, (center_line, 0), (center_line, frame_height), (255, 0, 0), 2)
            
            # Show the live feed
            cv2.imshow('CV Test - Press Q to Quit', display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("CV Test Stopped.")

# --- This makes the script runnable ---
if __name__ == "__main__":
    run_vision_test()