from PyQt6.QtCore import QThread, pyqtSignal

class MLTerminologyWorker(QThread):
    """
    MLTerminologyExtractor'ı arka planda çalıştırmak için kullanılan işçi sınıfı."""
    progress_update = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path

    def run(self):
        try:
            from core.workers.ml_terminology_extractor import MLTerminologyExtractor
            self.progress_update.emit("Terminoloji çıkarma arka planda başlatıldı...")
            extractor = MLTerminologyExtractor(self.project_path)
            extractor.run(append=True)
            self.progress_update.emit("Terminoloji başarıyla çıkartıldı.")
            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(f"Hata: {e}")
