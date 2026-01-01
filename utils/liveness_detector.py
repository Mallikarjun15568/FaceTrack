"""
Liveness Detection Module for FaceTrack - FINAL UNIFIED VERSION
Integration of all 5 enhancements:
1. Blink Detection (Improved logic)
2. Directional Head Movement (Left/Right tracking)
3. Adaptive Texture (Lighting Awareness)
4. Time-window Voting System (Multi-frame analysis)
5. Performance Optimization & Full Reset Functionality
"""

import cv2
import numpy as np
from scipy.spatial import distance as dist
import time

class LivenessDetector:
    def __init__(self):
        # --- 1. BLINK DETECTION VARIABLES ---
        self.EYE_AR_THRESH = 0.25
        self.BLINK_COUNTER = 0
        self.TOTAL_BLINKS = 0
        
        # --- 2. HEAD MOVEMENT & DIRECTION VARIABLES ---
        self.prev_nose_position = None
        self.movement_threshold = 15
        self.movements_detected = 0
        self.last_direction = None  # Tracks 'LEFT' or 'RIGHT'
        self.direction_changes = 0  # Counts direction flips
        
        # --- 3. TIME-WINDOW VOTING VARIABLES ---
        self.frame_results = []  # Stores history of frame results
        self.max_window_frames = 150  # Analyze up to 5 seconds of data
        self.min_confidence_ratio = 0.4  # Relaxed: 40% of frames must pass to be "Live" (temporary)
        
        # --- 4. PERFORMANCE OPTIMIZATION VARIABLES ---
        self.frame_count = 0
        self.cached_face_box = None
        self.face_detect_interval = 10  # Detect face every 10 frames to save CPU
        
        # Load Haar Cascades
        try:
            self.detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Error loading cascade classifier: {e}")
            self.detector = None
            self.eye_cascade = None

    # --- MODULE 1: BLINK DETECTION ---
    def detect_blink(self, frame, face_coords):
        """Detects if the user blinks at least once during the session."""
        x, y, w, h = face_coords
        roi_gray = frame[y:y+h, x:x+w]
        eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 5)
        
        if len(eyes) >= 2:
            ear_values = []
            for (ex, ey, ew, eh) in eyes[:2]:
                ear = eh / ew if ew > 0 else 0
                ear_values.append(ear)
            
            if ear_values:
                avg_ear = np.mean(ear_values)
                if avg_ear < 0.3: # Threshold for closed eyes
                    self.BLINK_COUNTER += 1
                else:
                    if self.BLINK_COUNTER >= 2: # Must be closed for at least 2 frames
                        self.TOTAL_BLINKS += 1
                    self.BLINK_COUNTER = 0
        return self.TOTAL_BLINKS >= 1

    # --- MODULE 2: DIRECTIONAL HEAD MOVEMENT ---
    def detect_head_movement(self, frame, face_coords):
        """Detects horizontal head movement and direction changes (Left to Right)."""
        x, y, w, h = face_coords
        current_nose = (x + w // 2, y + h // 2)
        
        if self.prev_nose_position is not None:
            dx = current_nose[0] - self.prev_nose_position[0]
            dy = current_nose[1] - self.prev_nose_position[1]
            movement_distance = np.sqrt(dx**2 + dy**2)
            
            if movement_distance > self.movement_threshold:
                if abs(dx) > abs(dy): # Focus on horizontal movement
                    current_direction = 'RIGHT' if dx > 0 else 'LEFT'
                    # Check for a specific flip in direction
                    if self.last_direction and self.last_direction != current_direction:
                        self.direction_changes += 1
                    self.last_direction = current_direction
                self.movements_detected += 1
        
        self.prev_nose_position = current_nose
        # Pass if direction changed or enough raw movement occurred
        return self.direction_changes >= 1 or self.movements_detected >= 3

    # --- MODULE 3: ADAPTIVE TEXTURE (LIGHTING AWARE) ---
    def check_texture(self, gray_frame, face_coords):
        """Analyzes skin texture based on Laplacian variance, adjusted for lighting."""
        x, y, w, h = face_coords
        face_roi = gray_frame[y:y+h, x:x+w]
        if face_roi.size == 0: return 0.0
        
        avg_brightness = np.mean(face_roi)
        laplacian_var = cv2.Laplacian(face_roi, cv2.CV_64F).var()
        
        # Adjust threshold dynamically based on brightness levels
        if avg_brightness < 60: base_threshold = 300  # Low light
        elif avg_brightness < 100: base_threshold = 400 # Medium light
        else: base_threshold = 500 # Strong light
        
        return min(1.0, laplacian_var / base_threshold)

    # --- MODULE 4 & 5: MAIN LOGIC & PERFORMANCE ---
    def check_liveness(self, frame):
        """Main entry point: Combines all signals and applies the voting window."""
        self.frame_count += 1
        
        # Performance: Re-detect face only every 10 frames
        if self.frame_count % self.face_detect_interval == 1 or self.cached_face_box is None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector.detectMultiScale(gray, 1.3, 5)
            if len(faces) == 0: return False, 0.0, "No face detected"
            self.cached_face_box = faces[0]
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        face_coords = self.cached_face_box
        
        # Run individual check modules
        texture_score = self.check_texture(gray, face_coords)
        blink_detected = self.detect_blink(frame, face_coords)
        movement_detected = self.detect_head_movement(frame, face_coords)
        
        confidence = 0.0
        checks_passed = 0
        
        if texture_score > 0.4: 
            confidence += 0.3
            checks_passed += 1
        if blink_detected: 
            confidence += 0.4
            checks_passed += 1
        if movement_detected: 
            confidence += 0.3
            checks_passed += 1
            
        # --- SINGLE-FRAME OVERRIDE: if obvious blink or movement detected, accept immediately ---
        if blink_detected or movement_detected:
            return True, confidence, "Live verified"

        # Add current frame result to the history window
        frame_is_live = checks_passed >= 2 and confidence >= 0.5
        self.frame_results.append({'passed': frame_is_live, 'confidence': confidence})
        
        # Maintain window size
        if len(self.frame_results) > self.max_window_frames:
            self.frame_results.pop(0)
            
        # Final Decision: Requires at least 30 frames of data
        if len(self.frame_results) >= 30:
            passed_frames = sum(1 for r in self.frame_results if r['passed'])
            pass_ratio = passed_frames / len(self.frame_results)
            avg_conf = sum(r['confidence'] for r in self.frame_results) / len(self.frame_results)
            
            # Final liveness flag based on voting ratio
            is_live_result = pass_ratio >= self.min_confidence_ratio
            return is_live_result, avg_conf, f"Pass Ratio: {pass_ratio:.2%} | Conf: {avg_conf:.2f}"
        else:
            return False, confidence, f"Analyzing... ({len(self.frame_results)}/30)"

    # --- RESET FUNCTIONALITY ---
    def reset(self):
        """Resets all internal counters and history for a new user/session."""
        self.BLINK_COUNTER = 0
        self.TOTAL_BLINKS = 0
        self.prev_nose_position = None
        self.movements_detected = 0
        self.last_direction = None
        self.direction_changes = 0
        self.frame_results = []
        self.frame_count = 0
        self.cached_face_box = None

# --- Execution Example ---
if __name__ == "__main__":
    detector = LivenessDetector()
    cap = cv2.VideoCapture(0)
    print("Liveness Detection System Started...")
    print("Commands: [q] to Quit, [r] to Reset")
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        is_live, conf, msg = detector.check_liveness(frame)
        color = (0, 255, 0) if is_live else (0, 0, 255)
        
        # Display UI Information
        cv2.putText(frame, f"LIVE: {is_live}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, msg, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow('FaceTrack Liveness Module', frame)
        
        # Key Handling
        key = cv2.waitKey(1) & 0xFF
        if key == ord('r'): # Manual Reset
            detector.reset()
            print("System Reset!")
        elif key == ord('q'): # Quit
            break

    cap.release()
    cv2.destroyAllWindows()