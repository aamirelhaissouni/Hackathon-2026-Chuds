"""
microphone.py
----------------
Handles audio input and yelling detection using the system microphone.
Can be tested standalone or imported by main.py.
"""

import sounddevice as sd
import numpy as np
import time

# --- CONFIGURATION ---
YELL_THRESHOLD = 0.35     # Adjust for environment & mic sensitivity
SAMPLE_RATE = 44100       # Audio sampling rate (Hz)
BLOCK_SIZE = 1024         # Number of samples per audio block
DEBUG = True              # Set False in production

# --- FUNCTIONS ---

def is_yelling(volume, threshold=YELL_THRESHOLD):
    """Returns True if volume level exceeds yelling threshold."""
    return volume > threshold


def get_volume_rms(indata):
    """Compute the root mean square (RMS) volume of audio input."""
    rms = np.sqrt(np.mean(np.square(indata)))
    return min(rms * 10, 1.0)  # scaled 0–1


def start_yell_detection(callback=None):
    """
    Start listening to the microphone in real-time.
    Optionally call a function (callback) when a yell is detected.

    Example:
        from microphone import start_yell_detection
        start_yell_detection()
    """

    print("\n--- MICROPHONE ACTIVE ---")
    print("Speak normally, then yell to trigger detection.")
    print(f"Yell Threshold = {YELL_THRESHOLD}")
    print("Press Ctrl+C to stop.\n")

    # --- Inner callback for audio stream ---
    def audio_callback(indata, frames, time_info, status):
        if status:
            print(status)
        volume = get_volume_rms(indata)
        bar = "#" * int(volume * 40)
        print(f"Volume: [{bar:<40}] {volume:.2f}", end="\r")

        if is_yelling(volume):
            print(f"\n!!! YELL DETECTED !!! (Volume: {volume:.2f})\n")
            if callback:
                callback(volume)

    # --- Open audio stream ---
    try:
        with sd.InputStream(
            channels=1,
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            callback=audio_callback
        ):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping yell detection.")
    except Exception as e:
        print(f"Error: {e}")


def test_microphone():
    """Standalone test mode for debugging microphone input."""
    start_yell_detection()


# --- MAIN ENTRY POINT ---
if __name__ == "__main__":
    test_microphone()



# 2. Using It from main.py
# In your main file (main.py), you can easily hook it into your logic like this:
# from microphone import start_yell_detection

# def on_yell(volume):
#     print(f"🔥 Rage triggered at volume {volume:.2f}!")
#     # TODO: update LED, display, or send event

# start_yell_detection(callback=on_yell)
