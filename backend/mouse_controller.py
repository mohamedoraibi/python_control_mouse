import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

FRAME_MARGIN = 0.12
MIN_MOVE_THRESHOLD = 1.5


class MouseController:
    def __init__(self):
        self._screen_w, self._screen_h = pyautogui.size()
        self._smooth_x = float(self._screen_w) / 2.0
        self._smooth_y = float(self._screen_h) / 2.0
        self._initialized = False
        self._holding_click = False

    def update(self, position: tuple, clicking: bool, sensitivity: float, smoothing: float) -> None:
        raw_x, raw_y = position

        norm_x = (raw_x - FRAME_MARGIN) / (1.0 - 2.0 * FRAME_MARGIN)
        norm_y = (raw_y - FRAME_MARGIN) / (1.0 - 2.0 * FRAME_MARGIN)
        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        cx, cy = 0.5, 0.5
        dx = (norm_x - cx) * sensitivity
        dy = (norm_y - cy) * sensitivity

        target_x = max(0.0, min(float(self._screen_w - 1), (cx + dx) * self._screen_w))
        target_y = max(0.0, min(float(self._screen_h - 1), (cy + dy) * self._screen_h))

        if not self._initialized:
            self._smooth_x = target_x
            self._smooth_y = target_y
            self._initialized = True

        alpha = max(0.05, 1.0 - smoothing * 0.92)
        self._smooth_x = alpha * target_x + (1.0 - alpha) * self._smooth_x
        self._smooth_y = alpha * target_y + (1.0 - alpha) * self._smooth_y

        move_x = int(self._smooth_x)
        move_y = int(self._smooth_y)

        cur_x, cur_y = pyautogui.position()
        if abs(cur_x - move_x) > MIN_MOVE_THRESHOLD or abs(cur_y - move_y) > MIN_MOVE_THRESHOLD:
            pyautogui.moveTo(move_x, move_y)

        if clicking and not self._holding_click:
            pyautogui.mouseDown(button="left")
            self._holding_click = True
        elif not clicking and self._holding_click:
            pyautogui.mouseUp(button="left")
            self._holding_click = False

    def get_position(self) -> tuple:
        return pyautogui.position()

    def reset(self) -> None:
        if self._holding_click:
            pyautogui.mouseUp(button="left")
        self._initialized = False
        self._holding_click = False
