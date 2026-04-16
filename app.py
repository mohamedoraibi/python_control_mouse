import os

from PySide6.QtCore import QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow

from backend.bridge import Bridge
from backend.camera_worker import CameraWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HandMouse — Camera Mouse Control")
        self.setMinimumSize(1280, 820)

        self._setup_web_view()
        self._setup_worker()
        self._connect_signals()

        ui_path = os.path.join(os.path.dirname(__file__), "ui", "index.html")
        self._web_view.load(QUrl.fromLocalFile(ui_path))

        self._worker.start()

    def _setup_web_view(self):
        self._web_view = QWebEngineView()
        self.setCentralWidget(self._web_view)

        self._channel = QWebChannel()
        self._bridge = Bridge()
        self._channel.registerObject("bridge", self._bridge)
        self._web_view.page().setWebChannel(self._channel)

    def _setup_worker(self):
        self._worker = CameraWorker()

    def _connect_signals(self):
        self._worker.frame_ready.connect(self._bridge.on_frame)
        self._worker.status_update.connect(self._bridge.on_status)

        self._bridge._sig_start.connect(self._worker.start_tracking)
        self._bridge._sig_stop.connect(self._worker.stop_tracking)
        self._bridge._sig_sensitivity.connect(self._worker.set_sensitivity)
        self._bridge._sig_smoothing.connect(self._worker.set_smoothing)

    def closeEvent(self, event):
        self._worker.stop()
        super().closeEvent(event)
