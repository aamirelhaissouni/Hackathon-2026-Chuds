import subprocess
from gtts import gTTS
import os
import time
import tempfile

class Speaker:
    """
    Text-to-speech speaker using gTTS and aplay for LM386 amplifier.
    """
    def __init__(self, volume=85):
        """
        Initialize the speaker for LM386 hardware.
        
        Args:
            volume (int): Volume level 0-100 (default: 85)
        """
        self.temp_file = "temp_roast_audio.mp3"
        self.temp_wav = "temp_roast_audio.wav"
        self.volume = volume
        self._check_dependencies()
        self._set_volume(volume)
    
    def _check_dependencies(self):
        """Check if required audio tools are installed."""
        missing = []
        
        # Check for aplay
        try:
            subprocess.run(['aplay', '--version'], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("aplay (install: sudo apt-get install alsa-utils)")
        
        # Check for ffmpeg
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append("ffmpeg (install: sudo apt-get install ffmpeg)")
        
        if missing:
            print(f"WARNING: Missing dependencies: {', '.join(missing)}")
            print("Audio playback may not work properly!")
    
    def _set_volume(self, volume):
        """
        Set system volume.
        
        Args:
            volume (int): Volume level 0-100
        """
        try:
            volume = max(0, min(100, volume))
            subprocess.run([
                'amixer', 'set', 'Master', f'{volume}%'
            ], capture_output=True)
        except Exception as e:
            print(f"Could not set volume: {e}")
    
    def _convert_to_wav(self, mp3_file, wav_file):
        """
        Convert MP3 to WAV format for aplay.
        
        Args:
            mp3_file (str): Input MP3 file path
            wav_file (str): Output WAV file path
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert MP3 to mono WAV at 44.1kHz (optimal for small speakers)
            subprocess.run([
                'ffmpeg', '-i', mp3_file,
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '44100',          # 44.1kHz sample rate
                '-ac', '1',              # Mono (single speaker)
                '-y',                    # Overwrite if exists
                wav_file
            ], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Conversion error: {e}")
            return False
        except FileNotFoundError:
            print("ffmpeg not found. Install with: sudo apt-get install ffmpeg")
            return False
    
    def speak(self, text):
        """
        Generate audio from text and play it through LM386 speaker.
        
        Args:
            text (str): The text to speak
        """
        try:
            # Generate the audio file
            print(f"Generating audio: '{text[:50]}...'")
            tts = gTTS(text=text, lang='en', tld='co.in')  # Indian accent
            tts.save(self.temp_file)
            
            # Convert MP3 to WAV
            print("Converting audio format...")
            if not self._convert_to_wav(self.temp_file, self.temp_wav):
                print("ERROR: Could not convert audio file")
                return
            
            # Play the audio through LM386 using aplay
            print("Playing audio through LM386 speaker...")
            subprocess.run(['aplay', '-q', self.temp_wav], check=True)
            
            print("Audio playback finished.")
            
        except subprocess.CalledProcessError as e:
            print(f"Playback ERROR: {e}")
        except Exception as e:
            print(f"Speaker ERROR: {e}")
        
        finally:
            # Clean up
            self._cleanup()
    
    def _cleanup(self):
        """Clean up temporary audio files."""
        try:
            # Small delay to ensure files are released
            time.sleep(0.1)
            
            # Remove temp files
            for file in [self.temp_file, self.temp_wav]:
                if os.path.exists(file):
                    try:
                        os.remove(file)
                    except Exception as e:
                        print(f"Cleanup warning for {file}: {e}")
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def test_speaker(self):
        """Test the LM386 speaker with a system tone."""
        print("Testing LM386 speaker...")
        try:
            subprocess.run([
                'speaker-test', '-t', 'wav', '-c', '1', '-l', '1'
            ], timeout=5)
            print("Speaker test complete!")
            return True
        except Exception as e:
            print(f"Speaker test failed: {e}")
            return False
    
    def set_volume(self, volume):
        """
        Change the volume level.
        
        Args:
            volume (int): Volume level 0-100
        """
        self.volume = volume
        self._set_volume(volume)


def test_audio_pipeline():
    """
    Tests the full text-to-speech and playback pipeline.
    """
    print("--- TESTING AUDIO WITH LM386 SPEAKER ---")
    
    # Initialize speaker
    speaker = Speaker(volume=80)
    
    # Test speaker hardware first
    print("\n=== Hardware Test ===")
    speaker.test_speaker()
    time.sleep(1)
    
    # Test with RoastMaster
    try:
        from roaster import RoastMaster
        
        roaster = RoastMaster()
        
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
        print("\n3. Testing SHAKE roast:")
        text_to_say = roaster.get_roast(emotion_key='shake', player_id='right')
        print(f"   Roast: {text_to_say}")
        speaker.speak(text_to_say)
        time.sleep(1)
        
        # Test yell roast
        print("\n4. Testing YELL roast:")
        text_to_say = roaster.get_roast(emotion_key='yell', player_id='left')
        print(f"   Roast: {text_to_say}")
        speaker.speak(text_to_say)
        time.sleep(1)
        
        # Test neutral roast
        print("\n5. Testing NEUTRAL roast:")
        text_to_say = roaster.get_roast(emotion_key='neutral', player_id='right')
        print(f"   Roast: {text_to_say}")
        speaker.speak(text_to_say)
        
    except Exception as e:
        print(f"Could not import RoastMaster: {e}")
        print("Testing with fallback text...")
        text_to_say = "This is a short test audio to verify playback through the LM386 amplifier."
        speaker.speak(text_to_say)
    
    print("\n--- AUDIO TEST COMPLETE ---")


if __name__ == "__main__":
    test_audio_pipeline()