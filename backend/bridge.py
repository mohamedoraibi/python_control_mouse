from PySide6.QtCore import QObject, Signal, Slot


class Bridge(QObject):
    frameUpdated = Signal(str)
    statusUpdated = Signal(str)

    _sig_start = Signal()
    _sig_stop = Signal()
    _sig_sensitivity = Signal(float)
    _sig_smoothing = Signal(float)

    @Slot()
    def start(self):
        self._sig_start.emit()

    @Slot()
    def stop(self):
        self._sig_stop.emit()

    @Slot(float)
    def setSensitivity(self, value: float):
        self._sig_sensitivity.emit(float(value))

    @Slot(float)
    def setSmoothing(self, value: float):
        self._sig_smoothing.emit(float(value))

    def on_frame(self, data: str):
        self.frameUpdated.emit(data)

    def on_status(self, data: str):
        self.statusUpdated.emit(data)
