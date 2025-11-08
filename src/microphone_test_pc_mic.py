# microphone_test_pc.py
# Yell detector test for your computer microphone
# Works with built-in or USB mic

import sounddevice as sd
import numpy as np
import time

# --- CONFIGURATION ---
YELL_THRESHOLD = 0.4  # Start around 0.3, adjust if needed
SAMPLE_RATE = 44100   # Standard audio sample rate
BLOCK_SIZE = 1024     # Samples per chunk of audio

def test_microphone():
    """Live test for yell detection using your computer microphone."""
    print("--- MICROPHONE TEST (PC VERSION) ---")
    print("Talk normally, then yell to test threshold.")
    print("Press Ctrl+C to stop.\n")

    try:
        # List available devices
        print("Available audio devices:\n")
        print(sd.query_devices())
        
        # Automatically use the default input
        input_device = sd.query_devices(kind='input')
        print(f"\nUsing default input device: {input_device['name']}\n")

    except Exception as e:
        print(f"Error: Could not query devices. {e}")
        return

    # Callback runs every audio block
    def audio_callback(indata, frames, time_info, status):
        if status:
            print(status)

        # Compute RMS volume
        volume_rms = np.sqrt(np.mean(np.square(indata)))
        volume_rms = min(volume_rms * 10, 1.0)  # Scale & clamp to 0–1

        # Draw a live volume bar
        bar = "#" * int(volume_rms * 40)
        print(f"Volume: [{bar:<40}] {volume_rms:.2f}", end="\r")

        # Yell detection
        if volume_rms > YELL_THRESHOLD:
            print(f"\n!!! YELL DETECTED !!! (Volume: {volume_rms:.2f})\n")

    print(f"Starting stream (Threshold: {YELL_THRESHOLD})\n")

    try:
        with sd.InputStream(callback=audio_callback,
                            channels=1,
                            samplerate=SAMPLE_RATE,
                            blocksize=BLOCK_SIZE):
            while True:
                time.sleep(0.1)  # Keep alive
    except KeyboardInterrupt:
        print("\nStopping microphone test.")
    except Exception as e:
        print(f"Stream error: {e}")

if __name__ == "__main__":
    test_microphone()

