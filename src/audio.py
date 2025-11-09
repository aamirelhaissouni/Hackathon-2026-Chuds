import pygame
from gtts import gTTS
import os
import time

# --- THIS IS YOUR CONTRACT WITH MAIN.PY ---

class Speaker:
    """
    Handles Text-to-Speech (gTTS) and audio playback (Pygame).
    Assumes audio is already routed to GPIO 18 via /boot/config.txt
    """
    
    # Define a temporary file to save the MP3
    # Using '__temp.mp3' is a common convention
    TEMP_AUDIO_FILE = "_roast.mp3"

    def __init__(self):
        """
        Initializes the Pygame mixer.
        """
        try:
            pygame.mixer.init()
            print("Audio: Pygame mixer initialized.")
        except Exception as e:
            print(f"AUDIO ERROR: Failed to initialize pygame.mixer: {e}")
            print("Audio: Speaker will be disabled.")
            # We don't set a 'ready' flag because gTTS might still work
            # But we should be careful.
            
    def speak(self, text_to_speak):
        """
        Takes a string of text, saves it as an MP3, and plays it.
        This is a BLOCKING function - it will wait until the audio is done.
        """
        print(f"Audio: Speaking... '{text_to_speak[:30]}...'")
        
        # --- 1. Generate MP3 from Text (gTTS) ---
        try:
            tts = gTTS(text=text_to_speak, lang='en')
            tts.save(self.TEMP_AUDIO_FILE)
        except Exception as e:
            print(f"AUDIO ERROR: gTTS failed: {e}")
            print("Audio: Do you have an internet connection?")
            return # Exit the function

        # --- 2. Play the MP3 (Pygame) ---
        try:
            # Load the file we just saved
            pygame.mixer.music.load(self.TEMP_AUDIO_FILE)
            
            # Play it
            pygame.mixer.music.play()

            # --- IMPORTANT ---
            # Wait for the audio to finish playing
            # This prevents the main loop from trying to play
            # multiple roasts on top of each other.
            while pygame.mixer.music.get_busy():
                time.sleep(0.05) # Check 20 times a second
                
        except Exception as e:
            print(f"AUDIO ERROR: Pygame failed to play: {e}")
            print("Audio: Is the audio device configured correctly on the Pi?")
            
        finally:
            # --- 3. Clean up ---
            # We can (optionally) remove the file after playing
            # This is good practice.
            try:
                if os.path.exists(self.TEMP_AUDIO_FILE):
                    os.remove(self.TEMP_AUDIO_FILE)
            except Exception as e:
                print(f"AUDIO ERROR: Failed to remove temp file: {e}")