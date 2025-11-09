import pygame
from gtts import gTTS
import os
import time

class Speaker:
    """
    Text-to-speech speaker using gTTS and pygame.
    """
    def __init__(self):
        """Initialize the speaker (pygame mixer will be initialized on first use)."""
        self.temp_file = "temp_roast_audio.mp3"
        pygame.mixer.init()
    
    def speak(self, text):
        """
        Generate audio from text and play it.
        
        Args:
            text (str): The text to speak
        """
        try:
            # Generate the audio file
            print(f"Generating audio: '{text[:50]}...'")
            tts = gTTS(text=text, lang='en', tld='co.in')  # Indian accent
            tts.save(self.temp_file)
            
            # Play the audio
            pygame.mixer.music.load(self.temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            print("Audio playback finished.")
            
        except Exception as e:
            print(f"Speaker ERROR: {e}")
        
        finally:
            # Clean up
            self._cleanup()
    
    def _cleanup(self):
        """Clean up temporary audio file."""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                if hasattr(pygame.mixer.music, 'unload'):
                    pygame.mixer.music.unload()
            
            # Remove temp file
            if os.path.exists(self.temp_file):
                time.sleep(0.2)  # Give a moment for file to be released
                os.remove(self.temp_file)
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def __del__(self):
        """Cleanup on object destruction."""
        try:
            pygame.mixer.quit()
        except:
            pass


def test_audio_pipeline():
    """
    Tests the full text-to-speech and playback pipeline.
    """
    print("--- TESTING AUDIO ---")
    
    # Test with RoastMaster
    try:
        from roaster import RoastMaster
        
        roaster = RoastMaster()
        speaker = Speaker()
        
        print("\n=== Testing different roast categories ===\n")
        
        # Test angry roast
        print("1. Testing ANGRY roast:")
        text_to_say = roaster.get_roast(emotion_key='angry', player_id='left') 
        print(f"   Roast: {text_to_say}")
        speaker.speak(text_to_say)
        time.sleep(1)

        # Test sad roast
        print("\n2. Testing SAD roast:")
        text_to_say = roaster.get_roast(emotion_key='sad', player_id='left')
        print(f"   Roast: {text_to_say}")
        speaker.speak(text_to_say)
        time.sleep(1)

        # Test shake roast
        print("\n2. Testing SHAKE roast:")
        text_to_say = roaster.get_roast(emotion_key='shake', player_id='right')
        print(f"   Roast: {text_to_say}")
        speaker.speak(text_to_say)
        time.sleep(1)

        # Test yell roast
        print("\n2. Testing YELL roast:")
        text_to_say = roaster.get_roast(emotion_key='yell', player_id='left')
        print(f"   Roast: {text_to_say}")
        speaker.speak(text_to_say)
        time.sleep(1)
        
        # Test neutral roast
        print("\n3. Testing NEUTRAL roast:")
        text_to_say = roaster.get_roast(emotion_key='neutral', player_id='right')
        print(f"   Roast: {text_to_say}")
        speaker.speak(text_to_say)
        
    except Exception as e:
        print(f"Could not import RoastMaster: {e}")
        print("Testing with fallback text...")
        text_to_say = "This is a short test audio to verify playback and cleanup."
        speaker = Speaker()
        speaker.speak(text_to_say)
    
    print("\n--- AUDIO TEST COMPLETE ---")


if __name__ == "__main__":
    test_audio_pipeline()