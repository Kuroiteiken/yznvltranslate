import sys
import os
import configparser
from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox, 
    QMessageBox, QLabel, QApplication, QTextEdit, QListWidget, 
    QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QInputDialog,
    QSpinBox, QCheckBox, QGroupBox, QSplitter, QWidget, QProgressBar
)
from PyQt6.QtGui import QIntValidator, QFont, QIcon, QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QSize
from logger import app_logger

# ─── V2.1.0 Geriye Uyumluluk Re-export'lar ───
# ui/ paketine taşınan sınıflar burada da erişilebilir kalır.
# Eski "from dialogs import X" çağrıları kırılmaz.
try:
    from ui.app_settings_dialog import AppSettingsDialog
    from ui.file_preview_dialog import FilePreviewDialog
except ImportError:
    pass  # ui paketi henüz mevcut değilse sessizce geç



# --- Yardımcı Fonksiyonlar ---
def get_config_path(subfolder):
    """AppConfigs altındaki klasör yollarını döndürür."""
    base_path = os.getcwd()
    path = os.path.join(base_path, "AppConfigs", subfolder)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def load_files_to_combo(combobox, subfolder):
    """Belirtilen klasördeki txt dosyalarını combobox'a yükler."""
    folder = get_config_path(subfolder)
    combobox.clear()
    combobox.addItem("Seçiniz...", None)
    if os.path.exists(folder):
        files = sorted([f for f in os.listdir(folder) if f.endswith('.txt')])
        for f in files:
            file_path = os.path.join(folder, f)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read().strip()
                # Item text: Dosya Adı, Item Data: Dosya İçeriği
                combobox.addItem(f.replace('.txt', ''), content)
            except:
                pass


class ApiKeyEditorDialog(QDialog):
    """API Anahtarlarını yönetmek için editör."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Key Editörü")
        self.resize(600, 400)
        self.keys_folder = get_config_path("APIKeys")
        
        main_layout = QHBoxLayout(self)
        
        # Sol Panel
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Kayıtlı Anahtarlar:"))
        self.key_list = QListWidget()
        self.key_list.currentItemChanged.connect(self.on_key_selected)
        left_layout.addWidget(self.key_list)
        
        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("Yeni")
        self.new_btn.clicked.connect(self.new_key)
        self.del_btn = QPushButton("Sil")
        self.del_btn.setStyleSheet("color: red;")
        self.del_btn.clicked.connect(self.delete_key)
        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.del_btn)
        left_layout.addLayout(btn_layout)
        
        # Sağ Panel
        right_layout = QVBoxLayout()
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Anahtar Adı (Örn: Ana Hesabım)")
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("AIzaSy...")
        form.addRow("Ad:", self.name_input)
        form.addRow("Key:", self.key_input)
        right_layout.addLayout(form)
        
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.clicked.connect(self.save_key)
        right_layout.addWidget(self.save_btn)
        right_layout.addStretch()
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        
        self.load_keys()
        
    def load_keys(self):
        self.key_list.clear()
        if os.path.exists(self.keys_folder):
            files = [f for f in os.listdir(self.keys_folder) if f.endswith('.txt')]
            for f in files:
                self.key_list.addItem(f.replace('.txt', ''))
        self.new_key()
        
    def on_key_selected(self, current, prev):
        if not current: return
        filename = current.text() + ".txt"
        path = os.path.join(self.keys_folder, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.name_input.setText(current.text())
                self.key_input.setText(f.read().strip())
                
    def new_key(self):
        self.key_list.clearSelection()
        self.name_input.clear()
        self.key_input.clear()
        
    def save_key(self):
        name = self.name_input.text().strip()
        key = self.key_input.text().strip()
        
        if not name or not key:
            QMessageBox.warning(self, "Eksik", "Ad ve Key alanları zorunludur.")
            return
            
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
        path = os.path.join(self.keys_folder, safe_name + ".txt")
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(key)
            self.load_keys()
            QMessageBox.information(self, "Başarılı", "API Anahtarı kaydedildi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))
            
    def delete_key(self):
        current = self.key_list.currentItem()
        if not current: return
        
        if QMessageBox.question(self, "Sil", "Emin misiniz?") == QMessageBox.StandardButton.Yes:
            path = os.path.join(self.keys_folder, current.text() + ".txt")
            try:
                os.remove(path)
                self.load_keys()
            except: pass
