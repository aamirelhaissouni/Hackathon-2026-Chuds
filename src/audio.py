import pygame
from gtts import gTTS
import os
import time

def test_audio_pipeline():
    """
    Tests the full text-to-speech and playback pipeline.
    """
    print("--- TESTING AUDIO ---")
    
    # --- 1. Test gTTS (Text -> MP3) ---
    print("Step 1: Generating MP3 with gTTS...")
    # Import get_roasts here so failures in roaster.py don't break module import
    try:
        from roaster import get_roasts
        text_to_say = get_roasts()
    except Exception as e:
        print(f"Could not import/get roasts: {e}. Using fallback text.")
        text_to_say = "This is a short test audio to verify playback and cleanup."
    temp_file = "test_audio.mp3"
    
    try:
        tts = gTTS(text=text_to_say, lang='en', tld='co.in') #co.in is indian accent
        tts.save(temp_file)
        print(f"Successfully saved '{temp_file}'.")
    except Exception as e:
        print(f"gTTS FAILED: {e}")
        print("Do you have an internet connection?")
        return

    # --- 2. Test Pygame (MP3 -> Sound) ---
    print("Step 2: Playing MP3 with Pygame...")
    
    try:
        # Initialize the mixer
        pygame.mixer.init()
        
        # Load the audio file
        pygame.mixer.music.load(temp_file)
        
        # Play the audio file
        pygame.mixer.music.play()
        print("Playing audio... You should hear it now.")
        
        # Wait for the music to finish playing
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        print("Audio playback finished.")
        
    except Exception as e:
        print(f"Pygame FAILED: {e}")
        print("Do you have an audio output device selected?")
    
    finally:
        # Ensure pygame releases the file and mixer is shutdown before deleting the temp file
        try:
            # Only try to stop/unload/quit if the mixer was initialized
            if pygame.mixer.get_init():
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass

                # pygame 2.0+ has unload to free the music file; use if available
                try:
                    if hasattr(pygame.mixer.music, 'unload'):
                        pygame.mixer.music.unload()
                except Exception:
                    pass

                try:
                    pygame.mixer.quit()
                except Exception:
                    pass
        except Exception:
            # Defensive: if anything goes wrong accessing pygame, continue to cleanup attempt
            pass

        # Clean up the test file (handle case where file is still locked)
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                print(f"Cleaned up '{temp_file}'.")
            except PermissionError as e:
                print(f"Could not remove '{temp_file}': {e}. It may still be in use by another process.")

# --- This makes the script runnable ---
if __name__ == "__main__":
    test_audio_pipeline()
    print("--- AUDIO TEST COMPLETE ---")