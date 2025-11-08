import time

# --- MOCK IMPORTS & FUNCTIONS (TEMPORARY) ---
# These will be replaced by real teammate modules later

# Mock for Player Emotion Analysis with a single-line "Analyzing..." animation
def mock_analyze_emotions(frame):
    if not hasattr(mock_analyze_emotions, "dot_count"):
        mock_analyze_emotions.dot_count = 0

    # Cycle through 0–3 dots
    dots = '.' * (mock_analyze_emotions.dot_count % 4)
    print(f"\rAnalyzing{dots}  ", end='', flush=True)  # \r overwrites the line
    mock_analyze_emotions.dot_count += 1

    # Return fixed emotions for testing
    return {'left': 'neutral', 'right': 'angry'}


# Mock for Gyro Sensor Shake Detection
def mock_check_for_shake(gyro_obj):
    return False  # Default false so we don't spam

# Mock for Light Control
class MockLight:
    def on(self): print("MOCK: Light ON")
    def off(self): print("MOCK: Light OFF")
    def flash(self): print("MOCK: Light FLASHING")

# Mock for Microphone Yell Detection
def mock_check_for_yell():
    return False

# --- REAL IMPORTS (Replace mocks when ready) ---
analyze_player_emotions = mock_analyze_emotions
check_for_shake = mock_check_for_shake
LightControl = MockLight
check_for_yell = mock_check_for_yell

# --- MOCK OBJECTS ---
mock_frame = "This is a fake camera frame"
mock_gyro = "This is a fake gyro object"

# --- GLOBAL CONSTANTS & VARIABLES ---
ROAST_COOLDOWN_SEC = 10
SHAKE_COOLDOWN_SEC = 15
YELL_COOLDOWN_SEC = 15

player_1_last_roast = 0
player_2_last_roast = 0
last_shake_roast = 0
last_yell_roast = 0

def main():
    print("Rage-O-Meter v0.1 Starting...")
    
    # Initialize objects
    light = LightControl()
    light.on()  # Signal app is on
    
    try:
        while True:
            current_time = time.time()
            
            # --- 1. GET INPUTS ---
            frame = mock_frame  # Replace with real camera frame later
            player_emotions = analyze_player_emotions(frame)
            p1_emotion = player_emotions.get('left', 'unknown')
            p2_emotion = player_emotions.get('right', 'unknown')
            
            is_shake = check_for_shake(mock_gyro)
            is_yell = check_for_yell()
            
            # --- 2. PROCESS LOGIC & TRIGGER ROASTS ---
            
            # Player 1 (Left)
            global player_1_last_roast
            if p1_emotion == 'angry' and (current_time - player_1_last_roast > ROAST_COOLDOWN_SEC):
                print("PLAYER 1 (LEFT) IS RAGING!")
                light.flash()
                player_1_last_roast = current_time
            
            # Player 2 (Right)
            global player_2_last_roast
            if p2_emotion == 'angry' and (current_time - player_2_last_roast > ROAST_COOLDOWN_SEC):
                print("PLAYER 2 (RIGHT) IS RAGING!")
                light.flash()
                player_2_last_roast = current_time
            
            # Shake Detection
            global last_shake_roast
            if is_shake and (current_time - last_shake_roast > SHAKE_COOLDOWN_SEC):
                print("TABLE SLAM DETECTED!")
                light.flash()
                last_shake_roast = current_time
            
            # Yell Detection
            global last_yell_roast
            if is_yell and (current_time - last_yell_roast > YELL_COOLDOWN_SEC):
                print("YELL DETECTED!")
                light.flash()
                last_yell_roast = current_time
            
            # --- 3. LOOP DELAY ---
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nShutting down... good game!")
        light.off()

    finally:
        light.off()

if __name__ == "__main__":
    main()
