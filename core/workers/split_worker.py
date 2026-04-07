import os
import re
from PyQt6.QtCore import QObject, pyqtSignal

class SplitWorker(QObject):
    """
    İndirilen toplu bölüm dosyasını "## Bölüm - X ##" başlıklarına göre bölerek ayrı dosyalar oluşturur.
    
    """
    finished = pyqtSignal()
    progress = pyqtSignal(int, int) # (current, total)
    error = pyqtSignal(str)
    file_created = pyqtSignal(str) # To optionally pass the created file

    def __init__(self, input_file_path, output_folder):
        super().__init__()
        self.input_file_path = input_file_path
        self.output_folder = output_folder
        self.is_running = True

    def run(self):
        try:
            os.makedirs(self.output_folder, exist_ok=True)
            
            with open(self.input_file_path, "r", encoding="utf-8") as f:
                icerik = f.read()
            
            # Bölümleri ayır (## Bölüm - X ## etiketi ile)
            bolumler = re.split(r"## Bölüm - (\d+) ##", icerik)
            
            if len(bolumler) <= 1:
                self.error.emit(f"Dosyada uygun '## Bölüm - X ##' başlığı bulunamadı.")
                self.finished.emit()
                return

            # re.split ile gelen liste: ["", "1", "bölüm metni", "2", "bölüm metni", ...]
            # Bu yüzden 1'den başlatıp 2'şer adım ilerleyeceğiz
            valid_chunks = list(range(1, len(bolumler), 2))
            total_chapters = len(valid_chunks)
            processed = 0

            for i in valid_chunks:
                if not self.is_running:
                    break

                bolum_numara = bolumler[i].strip()
                bolum_metin = bolumler[i+1].strip()

                # Çıktı dosyası formatı
                dosya_adi = f"bolum_{bolum_numara.zfill(4)}.txt"
                dosya_yolu = os.path.join(self.output_folder, dosya_adi)

                with open(dosya_yolu, "w", encoding="utf-8") as f:
                    f.write(bolum_metin)

                processed += 1
                self.progress.emit(processed, total_chapters)
                self.file_created.emit(dosya_adi)

            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()

    def stop(self):
        self.is_running = False
