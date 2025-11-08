"""
Vision module for detecting faces and analyzing player emotions.
Supports webcam input (current) and can be adapted for Raspberry Pi camera.
"""

import cv2
import numpy as np
from deepface import DeepFace
from typing import Dict, Optional, Tuple
from collections import deque


class EmotionSmoother:
    """
    Smooths emotion predictions to prevent rapid switching.
    Uses a sliding window approach to require consistent detections.
    """
    def __init__(self, window_size: int = 5, confidence_threshold: int = 3):
        """
        Args:
            window_size: Number of recent emotions to track
            confidence_threshold: How many times an emotion must appear to be accepted
        """
        self.window_size = window_size
        self.confidence_threshold = confidence_threshold
        self.left_history = deque(maxlen=window_size)
        self.right_history = deque(maxlen=window_size)
        self.left_current = 'unknown'
        self.right_current = 'unknown'
    
    def smooth_emotion(self, new_emotion: str, history: deque, current_emotion: str) -> str:
        """
        Smooth a single emotion based on history.
        
        Args:
            new_emotion: The newly detected emotion
            history: Deque containing recent emotion history
            current_emotion: The current stable emotion
        
        Returns:
            Smoothed emotion string
        """
        # Add new emotion to history
        history.append(new_emotion)
        
        # If we don't have enough samples yet, return the most common so far
        if len(history) < self.confidence_threshold:
            if len(history) > 0:
                return max(set(history), key=history.count)
            return new_emotion
        
        # Count occurrences of each emotion in the window
        emotion_counts = {}
        for emotion in history:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Find the most common emotion
        most_common = max(emotion_counts.items(), key=lambda x: x[1])
        
        # Only update if the most common emotion appears at least confidence_threshold times
        if most_common[1] >= self.confidence_threshold:
            return most_common[0]
        
        # Otherwise, keep the current emotion (don't change) to prevent flickering
        return current_emotion
    
    def update(self, left_emotion: str, right_emotion: str) -> Dict[str, str]:
        """
        Update emotions with smoothing.
        
        Args:
            left_emotion: New left player emotion
            right_emotion: New right player emotion
        
        Returns:
            Dictionary with smoothed 'left' and 'right' emotions
        """
        self.left_current = self.smooth_emotion(left_emotion, self.left_history, self.left_current)
        self.right_current = self.smooth_emotion(right_emotion, self.right_history, self.right_current)
        
        return {
            'left': self.left_current,
            'right': self.right_current
        }


# Global emotion smoother instance
_emotion_smoother = EmotionSmoother(window_size=7, confidence_threshold=4)


class BaselineCalibrator:
    """
    Calibrates emotion detection by establishing a baseline neutral state.
    Compares subsequent emotions against this baseline for more accurate detection.
    """
    def __init__(self):
        self.left_baseline = None
        self.right_baseline = None
        self.calibrated = False
        self.calibration_samples = []  # Store multiple samples for averaging
        self.samples_needed = 10  # Number of frames to average for baseline
    
    def add_calibration_sample(self, left_emotion_scores: Dict[str, float], 
                               right_emotion_scores: Optional[Dict[str, float]] = None):
        """
        Add a sample for baseline calibration.
        
        Args:
            left_emotion_scores: Emotion scores for left player
            right_emotion_scores: Emotion scores for right player (optional)
        """
        self.calibration_samples.append({
            'left': left_emotion_scores,
            'right': right_emotion_scores
        })
    
    def calculate_baseline(self):
        """
        Calculate baseline emotion scores by averaging calibration samples.
        """
        if len(self.calibration_samples) < self.samples_needed:
            return False
        
        # Average left player baseline
        left_avg = {}
        for sample in self.calibration_samples:
            if sample['left']:
                for emotion, score in sample['left'].items():
                    left_avg[emotion] = left_avg.get(emotion, 0) + score
        
        # Divide by number of samples
        num_samples = len(self.calibration_samples)
        self.left_baseline = {k: v / num_samples for k, v in left_avg.items()}
        
        # Average right player baseline (if available)
        right_samples = [s for s in self.calibration_samples if s['right']]
        if right_samples:
            right_avg = {}
            for sample in right_samples:
                for emotion, score in sample['right'].items():
                    right_avg[emotion] = right_avg.get(emotion, 0) + score
            
            num_right_samples = len(right_samples)
            self.right_baseline = {k: v / num_right_samples for k, v in right_avg.items()}
        else:
            self.right_baseline = None
        
        self.calibrated = True
        return True
    
    def reset(self):
        """Reset calibration."""
        self.left_baseline = None
        self.right_baseline = None
        self.calibrated = False
        self.calibration_samples = []
    
    def get_baseline(self, player: str = 'left') -> Optional[Dict[str, float]]:
        """
        Get baseline for a player.
        
        Args:
            player: 'left' or 'right'
        
        Returns:
            Baseline emotion scores or None if not calibrated
        """
        if player == 'left':
            return self.left_baseline
        else:
            return self.right_baseline


# Global baseline calibrator instance
_baseline_calibrator = BaselineCalibrator()


def analyze_player_emotions(frame: np.ndarray) -> Dict[str, str]:
    """
    Analyze emotions for two players in a frame.
    Uses baseline calibration if available for more accurate detection.
    
    Args:
        frame: A numpy array representing a video frame (BGR format from OpenCV)
    
    Returns:
        Dictionary with 'left' and 'right' keys, each containing an emotion string
        or 'unknown' if no face is detected for that position.
    """
    try:
        # Detect faces in the frame
        faces = detect_faces(frame)
        
        if len(faces) == 0:
            return {'left': 'unknown', 'right': 'unknown'}
        
        # Sort faces by x-coordinate (leftmost = left player, rightmost = right player)
        faces_sorted = sorted(faces, key=lambda f: f[0])
        
        # Get baselines for each player
        left_baseline = _baseline_calibrator.get_baseline('left')
        right_baseline = _baseline_calibrator.get_baseline('right')
        
        # Collect calibration samples if not calibrated yet
        if not _baseline_calibrator.calibrated:
            left_scores = None
            right_scores = None
            
            if len(faces_sorted) >= 1:
                left_scores = get_raw_emotion_scores(frame, faces_sorted[0])
            if len(faces_sorted) >= 2:
                right_scores = get_raw_emotion_scores(frame, faces_sorted[1])
            
            if left_scores:  # Only add if we got valid scores
                _baseline_calibrator.add_calibration_sample(left_scores, right_scores)
                
                # Check if we have enough samples to calculate baseline
                if len(_baseline_calibrator.calibration_samples) >= _baseline_calibrator.samples_needed:
                    _baseline_calibrator.calculate_baseline()
                    print("\n✓ Baseline calibration complete! Now detecting emotions relative to your neutral state.")
        
        # Analyze left player (first face or leftmost)
        if len(faces_sorted) >= 1:
            left_face = faces_sorted[0]
            left_emotion = analyze_face_emotion(frame, left_face, left_baseline)
        else:
            left_emotion = 'unknown'
        
        # Analyze right player (second face or rightmost)
        if len(faces_sorted) >= 2:
            right_face = faces_sorted[1]
            right_emotion = analyze_face_emotion(frame, right_face, right_baseline)
        elif len(faces_sorted) == 1:
            # If only one face detected, assign it to left, right is unknown
            right_emotion = 'unknown'
        else:
            right_emotion = 'unknown'
        
        # Apply smoothing to prevent rapid emotion switching
        smoothed_emotions = _emotion_smoother.update(left_emotion, right_emotion)
        return smoothed_emotions
    
    except Exception as e:
        print(f"Error in analyze_player_emotions: {e}")
        return {'left': 'unknown', 'right': 'unknown'}


def reset_calibration():
    """Reset the baseline calibration. Call this to recalibrate."""
    _baseline_calibrator.reset()
    print("Calibration reset. New baseline will be established.")


def detect_faces(frame: np.ndarray) -> list:
    """
    Detect faces in a frame using OpenCV's DNN face detector.
    
    Args:
        frame: Input frame in BGR format
    
    Returns:
        List of face bounding boxes as (x, y, w, h) tuples
    """
    try:
        # Convert BGR to RGB for face detection (some models prefer RGB)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Load OpenCV's Haar Cascade face detector
        # This is a lightweight option that works well
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return faces.tolist() if len(faces) > 0 else []
    
    except Exception as e:
        print(f"Error in detect_faces: {e}")
        return []


def get_raw_emotion_scores(frame: np.ndarray, face_box: Tuple[int, int, int, int]) -> Optional[Dict[str, float]]:
    """
    Get raw emotion scores from DeepFace without any processing.
    Used for baseline calibration.
    
    Args:
        frame: Input frame in BGR format
        face_box: Face bounding box as (x, y, w, h)
    
    Returns:
        Dictionary of emotion scores or None on error
    """
    try:
        x, y, w, h = face_box
        
        # Extract face region with some padding
        padding = 10
        x_start = max(0, x - padding)
        y_start = max(0, y - padding)
        x_end = min(frame.shape[1], x + w + padding)
        y_end = min(frame.shape[0], y + h + padding)
        
        face_roi = frame[y_start:y_end, x_start:x_end]
        
        if face_roi.size == 0:
            return None
        
        # DeepFace expects RGB format
        face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
        
        # Analyze emotion using DeepFace
        result = DeepFace.analyze(
            face_rgb,
            actions=['emotion'],
            enforce_detection=False,
            silent=True,
            detector_backend='opencv'
        )
        
        if isinstance(result, list):
            result = result[0]
        
        return result.get('emotion', {})
    
    except Exception as e:
        print(f"Error in get_raw_emotion_scores: {e}")
        return None


def analyze_face_emotion(frame: np.ndarray, face_box: Tuple[int, int, int, int], 
                         baseline: Optional[Dict[str, float]] = None) -> str:
    """
    Analyze the emotion of a single face using DeepFace.
    Enhanced with baseline comparison and increased sensitivity to anger/rage detection.
    
    Args:
        frame: Input frame in BGR format
        face_box: Face bounding box as (x, y, w, h)
        baseline: Optional baseline emotion scores for comparison
    
    Returns:
        Emotion string (e.g., 'angry', 'happy', 'neutral', etc.) or 'unknown' on error
    """
    try:
        x, y, w, h = face_box
        
        # Extract face region with some padding
        padding = 10
        x_start = max(0, x - padding)
        y_start = max(0, y - padding)
        x_end = min(frame.shape[1], x + w + padding)
        y_end = min(frame.shape[0], y + h + padding)
        
        face_roi = frame[y_start:y_end, x_start:x_end]
        
        if face_roi.size == 0:
            return 'unknown'
        
        # DeepFace expects RGB format
        face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
        
        # Analyze emotion using DeepFace
        # The analyze function returns a dictionary with emotion predictions
        result = DeepFace.analyze(
            face_rgb,
            actions=['emotion'],
            enforce_detection=False,  # Don't fail if face detection is uncertain
            silent=True,  # Suppress verbose output
            detector_backend='opencv'  # Use OpenCV for faster detection
        )
        
        # Extract the result
        if isinstance(result, list):
            result = result[0]
        
        # Get emotion scores (confidence values for each emotion)
        emotion_scores = result.get('emotion', {})
        
        # BASELINE COMPARISON: Calculate changes from baseline if available
        if baseline:
            # Calculate deltas (changes from baseline)
            emotion_deltas = {}
            for emotion, current_score in emotion_scores.items():
                baseline_score = baseline.get(emotion, 0)
                emotion_deltas[emotion] = current_score - baseline_score
            
            # Use deltas for more accurate detection
            # For example, if baseline anger is 5% and current is 15%, delta is +10%
            anger_delta = emotion_deltas.get('angry', 0)
            disgust_delta = emotion_deltas.get('disgust', 0)
            sad_delta = emotion_deltas.get('sad', 0)
            fear_delta = emotion_deltas.get('fear', 0)
            happy_delta = emotion_deltas.get('happy', 0)
            
            # Detect anger based on INCREASE from baseline
            # If anger increased significantly from baseline, that's a sign of rage
            if anger_delta > 8:  # 8% increase from baseline
                return 'angry'
            
            # Detect frustration as increase in negative emotions
            negative_delta_sum = anger_delta + disgust_delta + sad_delta
            if negative_delta_sum > 12:  # Combined increase in negative emotions
                if anger_delta > 3 or disgust_delta > 6:
                    return 'angry'
            
            # If disgust increased significantly from baseline
            if disgust_delta > 10:
                return 'angry'
            
            # If anger increased moderately but happiness decreased (frustration)
            if anger_delta > 5 and happy_delta < -5:
                return 'angry'
        
        # Get dominant emotion
        dominant_emotion = result.get('dominant_emotion', 'unknown').lower()
        
        # Extract all emotion scores for aggressive rage detection
        anger_score = emotion_scores.get('angry', 0)
        disgust_score = emotion_scores.get('disgust', 0)
        fear_score = emotion_scores.get('fear', 0)
        sad_score = emotion_scores.get('sad', 0)
        neutral_score = emotion_scores.get('neutral', 0)
        surprise_score = emotion_scores.get('surprise', 0)
        
        # AGGRESSIVE RAGE/FRUSTRATION DETECTION (fallback if no baseline)
        # Much more sensitive thresholds for detecting rage and visible frustration
        
        # Strategy 1: Direct anger detection with very low threshold
        ANGER_THRESHOLD = 8  # Very low threshold - detect even subtle anger (was 15)
        ANGER_BOOST_FACTOR = 2.5  # Aggressive boost - give anger 2.5x weight (was 1.5)
        
        if anger_score >= ANGER_THRESHOLD:
            boosted_anger = anger_score * ANGER_BOOST_FACTOR
            dominant_score = emotion_scores.get(dominant_emotion, 0)
            
            # Much more aggressive comparison - anger wins if it's 40% of dominant (was 60%)
            if boosted_anger >= dominant_score * 0.4:
                return 'angry'
        
        # Strategy 2: Detect frustration as combination of negative emotions
        # Frustration often shows as disgust + anger, or sad + anger
        negative_emotion_sum = anger_score + disgust_score + sad_score
        if negative_emotion_sum > 25:  # Combined negative emotions indicate frustration
            if anger_score > 5 or disgust_score > 12:  # At least some anger or high disgust
                return 'angry'
        
        # Strategy 3: Neutral face with underlying negative emotions = suppressed rage
        # People often try to look neutral when frustrated, but negative emotions leak through
        if neutral_score > 30 and (anger_score > 8 or disgust_score > 10):
            return 'angry'
        
        # Strategy 4: High disgust often indicates frustration/rage (especially in gaming)
        if disgust_score > 18:  # Lowered from 20, more sensitive
            return 'angry'
        
        # Strategy 5: Fear + Anger combination (panic/frustration)
        if fear_score > 15 and anger_score > 8:
            return 'angry'
        
        # Strategy 6: Surprise + Anger (shocked frustration, like "WTF?!")
        if surprise_score > 20 and anger_score > 6:
            return 'angry'
        
        # Strategy 7: Any moderate anger with low positive emotions = likely frustration
        happy_score = emotion_scores.get('happy', 0)
        if anger_score > 10 and happy_score < 15:  # Angry but not happy
            # Check if anger is in top 2 emotions
            sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_emotions) >= 2:
                top_two_scores = [score for _, score in sorted_emotions[:2]]
                if anger_score in top_two_scores or anger_score >= top_two_scores[1] * 0.7:
                    return 'angry'
        
        return dominant_emotion.lower()
    
    except Exception as e:
        print(f"Error in analyze_face_emotion: {e}")
        return 'unknown'


def get_webcam_frame(cap: cv2.VideoCapture) -> Optional[np.ndarray]:
    """
    Capture a frame from the webcam.
    
    Args:
        cap: OpenCV VideoCapture object
    
    Returns:
        Frame as numpy array or None if capture fails
    """
    try:
        ret, frame = cap.read()
        if ret:
            return frame
        return None
    except Exception as e:
        print(f"Error capturing frame: {e}")
        return None


# ============================================================================
# RASPBERRY PI CAMERA ADAPTATION
# ============================================================================
# To use a Raspberry Pi camera instead of a webcam, you have two options:
#
# Option 1: Use picamera2 library (recommended for Pi 5)
#   - Install: pip install picamera2
#   - Replace get_webcam_frame() with:
#     ```python
#     from picamera2 import Picamera2
#     
#     def get_pi_camera_frame(picam2: Picamera2) -> Optional[np.ndarray]:
#         try:
#             frame = picam2.capture_array()
#             # picamera2 returns RGB, convert to BGR for OpenCV
#             frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
#             return frame_bgr
#         except Exception as e:
#             print(f"Error capturing Pi camera frame: {e}")
#             return None
#     ```
#
# Option 2: Use OpenCV with v4l2 backend
#   - On Raspberry Pi, you can use: cap = cv2.VideoCapture(0)
#   - But you may need to set specific camera properties:
#     ```python
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
#     cap.set(cv2.CAP_PROP_FPS, 30)
#     ```
#
# The analyze_player_emotions() function will work the same way regardless
# of the camera source, as long as you pass it a frame in BGR format.
# ============================================================================


if __name__ == "__main__":
    """
    Test block: Continuously read frames from webcam and print analyzed emotions.
    Press 'q' to quit.
    """
    print("Initializing webcam...")
    
    # Initialize webcam
    # For Raspberry Pi camera, you would initialize picamera2 here instead
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        exit(1)
    
    # Set webcam properties (optional, adjust as needed)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Webcam initialized.")
    print("Calibrating baseline: Look neutral/relaxed for a few seconds...")
    print("Press 'q' to quit, 'r' to reset calibration\n")
    
    try:
        frame_count = 0
        while True:
            frame = get_webcam_frame(cap)
            
            if frame is None:
                print("Failed to capture frame")
                continue
            
            # Create a copy for display
            frame_display = frame.copy()
            
            # Detect faces and analyze emotions
            faces = detect_faces(frame)
            emotions = analyze_player_emotions(frame)
            
            # Show calibration status on frame
            calibration_status = ""
            if not _baseline_calibrator.calibrated:
                samples_collected = len(_baseline_calibrator.calibration_samples)
                samples_needed = _baseline_calibrator.samples_needed
                calibration_status = f"Calibrating: {samples_collected}/{samples_needed}"
            else:
                calibration_status = "Calibrated - Using baseline"
            
            # Sort faces by x-coordinate (left to right)
            faces_sorted = sorted(faces, key=lambda f: f[0])
            
            # Draw rectangles and emotion labels for each detected face
            for i, (x, y, w, h) in enumerate(faces_sorted):
                # Determine which player this face belongs to
                if i == 0:
                    emotion = emotions['left']
                    label = f"Left: {emotion.upper()}"
                    color = (0, 255, 0)  # Green for left player
                elif i == 1:
                    emotion = emotions['right']
                    label = f"Right: {emotion.upper()}"
                    color = (255, 0, 0)  # Blue for right player
                else:
                    # If more than 2 faces, just show emotion
                    emotion = analyze_face_emotion(frame, (x, y, w, h))
                    label = f"Face {i+1}: {emotion.upper()}"
                    color = (0, 165, 255)  # Orange for additional faces
                
                # Draw rectangle around face
                cv2.rectangle(frame_display, (x, y), (x + w, y + h), color, 2)
                
                # Draw background rectangle for text (for better visibility)
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
                
                # Position text above the face
                text_x = x
                text_y = max(y - 10, text_height + 10)
                
                # Draw filled rectangle for text background
                cv2.rectangle(
                    frame_display,
                    (text_x, text_y - text_height - 5),
                    (text_x + text_width + 5, text_y + baseline),
                    color,
                    -1  # Filled rectangle
                )
                
                # Draw text
                cv2.putText(
                    frame_display,
                    label,
                    (text_x + 2, text_y - 2),
                    font,
                    font_scale,
                    (255, 255, 255),  # White text
                    thickness
                )
            
            # Draw calibration status on frame
            status_font = cv2.FONT_HERSHEY_SIMPLEX
            status_font_scale = 0.5
            status_thickness = 1
            status_color = (0, 255, 255) if _baseline_calibrator.calibrated else (0, 165, 255)
            cv2.putText(
                frame_display,
                calibration_status,
                (10, 30),
                status_font,
                status_font_scale,
                status_color,
                status_thickness
            )
            
            # Display the frame
            cv2.imshow('Emotion Detection - Press Q to quit, R to reset calibration', frame_display)
            
            # Print results to console (update on same line for cleaner output)
            frame_count += 1
            print(f"\rFrame {frame_count}: Left={emotions['left']:8s} | Right={emotions['right']:8s} | {calibration_status}", 
                  end='', flush=True)
            
            # Check for key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                reset_calibration()
                print("\nCalibration reset. Look neutral for recalibration...")
            
            # Small delay to avoid overwhelming the system
            # Adjust based on your needs (lower = faster processing)
            import time
            time.sleep(0.05)  # Reduced delay for smoother video
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    except Exception as e:
        print(f"\n\nError in main loop: {e}")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print("Webcam released. Goodbye!")

    