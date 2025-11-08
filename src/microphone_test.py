# microphone_test.py
# Simple yell detector for MAX4466 analog mic using MCP3008
# Author: Michael Camargo (Hackathon Test)

from gpiozero import MCP3008
import numpy as np
import time

# --- CONFIG ---
CHANNEL = 0              # MCP3008 channel connected to MAX4466
YELL_THRESHOLD = 0.7      # Tune this between 0.5–0.9 depending on gain
SAMPLE_WINDOW = 0.1       # seconds of audio per reading

adc = MCP3008(channel=CHANNEL)

def read_volume(samples=100):
    """Reads samples from ADC and returns RMS volume level (0.0–1.0)."""
    readings = [adc.value for _ in range(samples)]
    rms = np.sqrt(np.mean(np.square(readings)))
    return rms

def test_microphone():
    print("--- MAX4466 MICROPHONE TEST ---")
    print("Normal talk vs yell detection.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            volume = read_volume()
            bar_length = int(volume * 40)
            bar = "#" * bar_length + "-" * (40 - bar_length)
            print(f"Volume: [{bar}] {volume:.2f}", end="\r")

            if volume > YELL_THRESHOLD:
                print(f"\n!!! YELL DETECTED !!! (Volume: {volume:.2f})\n")
                time.sleep(0.5)

            time.sleep(SAMPLE_WINDOW)
    except KeyboardInterrupt:
        print("\nStopping microphone test.")
    finally:
        adc.close()

if __name__ == "__main__":
    test_microphone()

