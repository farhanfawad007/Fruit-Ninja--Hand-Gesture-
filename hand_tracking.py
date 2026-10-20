import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import pygame
import os

class HandTracker:
    def __init__(self, width=1024, height=768, webcam_index=0):
        self.width = width
        self.height = height
        self.webcam_index = webcam_index
        
        # Check if the model task file exists
        model_path = "hand_landmarker.task"
        if not os.path.exists(model_path):
            # Fallback if downloaded in another path
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")
            
        print(f"Loading MediaPipe model from: {model_path}")
        
        # Initialize MediaPipe Tasks Hand Landmarker
        try:
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_hands=1
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            self.has_detector = True
        except Exception as e:
            print(f"Error initializing MediaPipe Landmarker: {e}")
            self.has_detector = False
            
        # Initialize Video Capture
        self.cap = cv2.VideoCapture(self.webcam_index)
        
        # Check if webcam opened successfully
        if not self.cap.isOpened() or not self.has_detector:
            print(f"Warning: Could not open webcam or initialize detector. Hand tracking disabled (Mouse fallback mode active).")
            self.has_webcam = False
        else:
            self.has_webcam = True
            # Set camera resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
    def get_frame(self):
        """
        Reads a frame from the webcam, processes it with MediaPipe Tasks,
        draws hand landmarks manually, and returns:
        - index_finger_coords: tuple (x, y) scaled to Pygame screen dimensions, or None
        - cam_surface: Pygame Surface of the camera feed (for PiP display)
        """
        if not self.has_webcam or not self.has_detector:
            return None, None
            
        ret, frame = self.cap.read()
        if not ret:
            return None, None
            
        # Flip the frame horizontally to make movement intuitive (mirror)
        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image object
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Perform hand detection
        results = self.detector.detect(mp_image)
        
        index_finger_pos = None
        
        # Process detection results
        if results.hand_landmarks and len(results.hand_landmarks) > 0:
            landmarks = results.hand_landmarks[0]
            
            # Get index finger tip coordinate (landmark index: 8)
            tip = landmarks[8]
            x = int(tip.x * self.width)
            y = int(tip.y * self.height)
            index_finger_pos = (x, y)
            
            # Map normalized landmarks to pixel coordinates on the camera frame
            pts = []
            for lm in landmarks:
                px = int(lm.x * w)
                py = int(lm.y * h)
                pts.append((px, py))
                
            # Define standard 21 landmarks hand connection skeleton lines
            connections = [
                # Thumb
                (0, 1), (1, 2), (2, 3), (3, 4),
                # Index finger
                (0, 5), (5, 6), (6, 7), (7, 8),
                # Middle finger
                (0, 9), (9, 10), (10, 11), (11, 12),
                # Ring finger
                (0, 13), (13, 14), (14, 15), (15, 16),
                # Pinky
                (0, 17), (17, 18), (18, 19), (19, 20),
                # Palm base connections
                (5, 9), (9, 13), (13, 17)
            ]
            
            # Draw custom neon green skeletal connection lines
            for start, end in connections:
                if start < len(pts) and end < len(pts):
                    cv2.line(frame, pts[start], pts[end], (57, 255, 20), 2)
                    
            # Draw custom bright cyan landmark joints and red blade index tip
            for i, pt in enumerate(pts):
                if i == 8: # Index finger tip (blade point)
                    cv2.circle(frame, pt, 7, (0, 0, 255), -1) # Red glowing tip
                else:
                    cv2.circle(frame, pt, 4, (255, 255, 0), -1) # Cyan joints
        
        # Resize frame for PiP overlay (e.g., width=200, height=150)
        pip_w, pip_h = 200, 150
        pip_frame = cv2.resize(frame, (pip_w, pip_h))
        pip_rgb = cv2.cvtColor(pip_frame, cv2.COLOR_BGR2RGB)
        
        # Convert to Pygame Surface
        cam_surface = pygame.image.frombuffer(pip_rgb.tobytes(), (pip_w, pip_h), "RGB")
        
        return index_finger_pos, cam_surface
        
    def release(self):
        """Releases the camera and detector resources."""
        if self.has_webcam:
            self.cap.release()
        if self.has_detector:
            self.detector.close()
        print("Camera and MediaPipe detector closed.")

if __name__ == "__main__":
    # Test hand tracking standalone (OpenCV window)
    tracker = HandTracker(1024, 768)
    if not tracker.has_webcam:
        print("No webcam or tracker initialized. Test aborted.")
        exit(1)
        
    print("Starting standalone tracking window. Press 'q' to quit.")
    while True:
        pos, surface = tracker.get_frame()
        # Just grab raw frame to show cv2 test
        ret, frame = tracker.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            res = tracker.detector.detect(mp_img)
            if res.hand_landmarks:
                for hl in res.hand_landmarks:
                    pts = [(int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])) for lm in hl]
                    for pt in pts:
                        cv2.circle(frame, pt, 4, (0, 255, 0), -1)
            cv2.imshow("Hand Tracker Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    tracker.release()
    cv2.destroyAllWindows()
