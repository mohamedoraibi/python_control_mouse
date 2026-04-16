import mediapipe as mp
import cv2
import numpy as np


PINCH_THRESHOLD = 45
CLICK_DEBOUNCE_FRAMES = 3


class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.72,
            min_tracking_confidence=0.6,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles
        self._pinch_frames = 0
        self._release_frames = 0
        self._is_clicking = False

    def process(self, frame: np.ndarray) -> dict | None:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.hands.process(rgb)
        rgb.flags.writeable = True

        if not results.multi_hand_landmarks:
            return None

        landmarks = results.multi_hand_landmarks[0]
        h, w, _ = frame.shape

        self.mp_draw.draw_landmarks(
            frame,
            landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            self.mp_styles.get_default_hand_landmarks_style(),
            self.mp_styles.get_default_hand_connections_style(),
        )

        index_tip = landmarks.landmark[8]
        thumb_tip = landmarks.landmark[4]
        middle_tip = landmarks.landmark[12]

        ix, iy = index_tip.x, index_tip.y
        tx, ty = thumb_tip.x, thumb_tip.y

        pinch_dist = np.hypot((ix - tx) * w, (iy - ty) * h)

        if pinch_dist < PINCH_THRESHOLD:
            self._pinch_frames += 1
            self._release_frames = 0
            if self._pinch_frames >= CLICK_DEBOUNCE_FRAMES:
                self._is_clicking = True
        else:
            self._release_frames += 1
            self._pinch_frames = 0
            if self._release_frames >= CLICK_DEBOUNCE_FRAMES:
                self._is_clicking = False

        px, py = int(ix * w), int(iy * h)
        if self._is_clicking:
            cv2.circle(frame, (px, py), 22, (0, 220, 100), -1)
            cv2.circle(frame, (px, py), 26, (255, 255, 255), 2)
        else:
            cv2.circle(frame, (px, py), 12, (0, 160, 255), -1)
            cv2.circle(frame, (px, py), 16, (255, 255, 255), 2)

        # Wrist for reference line
        wrist = landmarks.landmark[0]
        wx, wy = int(wrist.x * w), int(wrist.y * h)
        cv2.line(frame, (wx, wy), (px, py), (100, 200, 255), 1)

        return {
            "position": (ix, iy),
            "clicking": self._is_clicking,
            "pinch_dist": float(pinch_dist),
            "frame": frame,
        }

    def reset(self):
        self._pinch_frames = 0
        self._release_frames = 0
        self._is_clicking = False
