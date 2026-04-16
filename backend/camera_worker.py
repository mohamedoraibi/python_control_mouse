import base64
import json
import time

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal, Slot

from .hand_tracker import HandTracker
from .mouse_controller import MouseController

DISPLAY_W = 640
DISPLAY_H = 480
JPEG_QUALITY = 68
TARGET_FPS = 30


class CameraWorker(QThread):
    frame_ready = Signal(str)
    status_update = Signal(str)

    def __init__(self):
        super().__init__()
        self._running = False
        self._tracking = False
        self._sensitivity = 1.5
        self._smoothing = 0.55
        self._hand_tracker = HandTracker()
        self._mouse = MouseController()

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, DISPLAY_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DISPLAY_H)
        cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._running = True
        fps_count = 0
        fps_timer = time.perf_counter()
        current_fps = 0.0
        frame_interval = 1.0 / TARGET_FPS
        last_frame_time = time.perf_counter()

        while self._running:
            now = time.perf_counter()
            elapsed = now - last_frame_time
            if elapsed < frame_interval:
                time.sleep(max(0, frame_interval - elapsed - 0.001))

            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            last_frame_time = time.perf_counter()
            frame = cv2.flip(frame, 1)

            hand_detected = False
            clicking = False
            pinch_dist = 0.0

            if self._tracking:
                result = self._hand_tracker.process(frame)
                if result:
                    hand_detected = True
                    clicking = result["clicking"]
                    pinch_dist = result["pinch_dist"]
                    frame = result["frame"]
                    self._mouse.update(
                        result["position"],
                        clicking,
                        self._sensitivity,
                        self._smoothing,
                    )

            self._draw_overlay(frame, hand_detected, clicking)

            resized = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))
            _, buf = cv2.imencode(
                ".jpg", resized, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
            )
            b64 = base64.b64encode(buf).decode("utf-8")
            self.frame_ready.emit(b64)

            fps_count += 1
            fp_elapsed = time.perf_counter() - fps_timer
            if fp_elapsed >= 1.0:
                current_fps = fps_count / fp_elapsed
                fps_count = 0
                fps_timer = time.perf_counter()

            mx, my = self._mouse.get_position()
            status = {
                "hand_detected": hand_detected,
                "tracking_active": self._tracking,
                "fps": round(current_fps, 1),
                "mouse_x": mx,
                "mouse_y": my,
                "clicking": clicking,
                "pinch_dist": round(pinch_dist, 1),
            }
            self.status_update.emit(json.dumps(status))

        cap.release()

    def _draw_overlay(self, frame: np.ndarray, hand_detected: bool, clicking: bool) -> None:
        h, w = frame.shape[:2]

        if self._tracking:
            color = (0, 200, 80) if hand_detected else (60, 140, 255)
            label = "HAND DETECTED" if hand_detected else "SEARCHING..."
            cv2.putText(frame, label, (12, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

            border_color = (0, 220, 100) if hand_detected else (60, 140, 255)
            cv2.rectangle(frame, (2, 2), (w - 2, h - 2), border_color, 2)
        else:
            cv2.rectangle(frame, (2, 2), (w - 2, h - 2), (80, 80, 80), 2)
            cv2.putText(frame, "TRACKING PAUSED", (12, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 120, 120), 1, cv2.LINE_AA)

    @Slot()
    def start_tracking(self):
        self._hand_tracker.reset()
        self._mouse.reset()
        self._tracking = True

    @Slot()
    def stop_tracking(self):
        self._tracking = False
        self._mouse.reset()

    @Slot(float)
    def set_sensitivity(self, value: float):
        self._sensitivity = float(value)

    @Slot(float)
    def set_smoothing(self, value: float):
        self._smoothing = float(value)

    def stop(self):
        self._running = False
        self._tracking = False
        self._mouse.reset()
        self.wait(3000)
