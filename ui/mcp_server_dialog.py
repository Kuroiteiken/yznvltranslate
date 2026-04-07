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


class MCPServerDialog(QDialog):
    """MCP Sunucu Yönetim Paneli — Endpoint ekleme, düzenleme, silme ve anahtar yönetimi."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yapay Zeka Kaynağı Yönetimi (MCP)")
        self.resize(900, 600)
        
        main_layout = QHBoxLayout(self)
        
        # ── Sol Panel: Endpoint Listesi ──
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Kayıtlı Sunucular:"))
        
        self.endpoint_list = QListWidget()
        self.endpoint_list.currentItemChanged.connect(self.on_endpoint_selected)
        left_layout.addWidget(self.endpoint_list)
        
        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("Yeni")
        self.new_btn.clicked.connect(self.new_endpoint)
        self.del_btn = QPushButton("Sil")
        self.del_btn.setStyleSheet("color: red;")
        self.del_btn.clicked.connect(self.delete_endpoint)
        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.del_btn)
        left_layout.addLayout(btn_layout)
        
        # Aktif endpoint seçimi
        active_layout = QHBoxLayout()
        self.set_active_btn = QPushButton("Aktif Yap")
        self.set_active_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.set_active_btn.clicked.connect(self.set_active_endpoint)
        active_layout.addWidget(self.set_active_btn)
        left_layout.addLayout(active_layout)
        
        # ── Sağ Panel: Endpoint Formu ──
        right_layout = QVBoxLayout()
        
        form = QFormLayout()
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("benzersiz_kimlik")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Sunucu Adı")
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["gemini", "openai_compatible"])
        
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("model-id (ör: gemini-2.5-flash)")
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://api.example.com/v1 (boş = varsayılan)")
        
        self.rotation_check = QCheckBox("Anahtar Rotasyonu (Key Rotation)")
        self.rotation_check.setChecked(True)
        
        self.headers_input = QLineEdit()
        self.headers_input.setPlaceholderText('{"HTTP-Referer": "...", "X-Title": "..."}')
        
        form.addRow("ID:", self.id_input)
        form.addRow("Ad:", self.name_input)
        form.addRow("Tür:", self.type_combo)
        form.addRow("Model ID:", self.model_input)
        form.addRow("Base URL:", self.url_input)
        form.addRow(self.rotation_check)
        form.addRow("Headers (JSON):", self.headers_input)
        right_layout.addLayout(form)
        
        # API Anahtarları
        right_layout.addWidget(QLabel("API Anahtarları (her satıra bir tane):"))
        self.keys_edit = QTextEdit()
        self.keys_edit.setPlaceholderText("apikey_1\napikey_2\napikey_3")
        self.keys_edit.setMaximumHeight(120)
        right_layout.addWidget(self.keys_edit)
        
        # Butonlar
        action_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 Kaydet")
        self.save_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 6px;")
        self.save_btn.clicked.connect(self.save_endpoint)
        
        self.test_btn = QPushButton("🔗 Bağlantı Testi")
        self.test_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 6px;")
        self.test_btn.clicked.connect(self.test_connection)
        
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.test_btn)
        right_layout.addLayout(action_layout)
        
        self.test_result_label = QLabel("")
        self.test_result_label.setWordWrap(True)
        right_layout.addWidget(self.test_result_label)
        
        right_layout.addStretch()
        
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        
        self._load_list()
    
    def _load_list(self):
        """Endpoint listesini yükler."""
        self.endpoint_list.clear()
        try:
            from core.llm_provider import load_endpoints
            data = load_endpoints()
            self._active_id = data.get("active_endpoint_id", "")
            for ep in data.get("endpoints", []):
                prefix = "✅ " if ep["id"] == self._active_id else "   "
                self.endpoint_list.addItem(f"{prefix}{ep['name']} [{ep['type']}]")
        except Exception as e:
            QMessageBox.warning(self, "Uyarı", f"Endpoint listesi yüklenemedi: {e}")
    
    def _get_endpoints_data(self) -> dict:
        try:
            from core.llm_provider import load_endpoints
            return load_endpoints()
        except Exception:
            return {"active_endpoint_id": "", "endpoints": []}
    
    def on_endpoint_selected(self, current, previous):
        if not current:
            return
        idx = self.endpoint_list.row(current)
        data = self._get_endpoints_data()
        endpoints = data.get("endpoints", [])
        if 0 <= idx < len(endpoints):
            ep = endpoints[idx]
            self.id_input.setText(ep.get("id", ""))
            self.name_input.setText(ep.get("name", ""))
            self.type_combo.setCurrentText(ep.get("type", "gemini"))
            self.model_input.setText(ep.get("model_id", ""))
            self.url_input.setText(ep.get("base_url", "") or "")
            self.rotation_check.setChecked(ep.get("use_key_rotation", True))
            import json
            self.headers_input.setText(json.dumps(ep.get("headers", {})) if ep.get("headers") else "")
            
            # Anahtarları yükle
            try:
                from core.llm_provider import load_api_keys
                keys = load_api_keys(ep["id"])
                self.keys_edit.setText("\n".join(keys))
            except Exception:
                self.keys_edit.clear()
    
    def new_endpoint(self):
        self.endpoint_list.clearSelection()
        self.id_input.clear()
        self.name_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.model_input.clear()
        self.url_input.clear()
        self.rotation_check.setChecked(True)
        self.headers_input.clear()
        self.keys_edit.clear()
        self.test_result_label.clear()
    
    def save_endpoint(self):
        ep_id = self.id_input.text().strip()
        ep_name = self.name_input.text().strip()
        
        if not ep_id or not ep_name:
            QMessageBox.warning(self, "Eksik", "ID ve Ad alanları zorunludur.")
            return
        
        import json as _json
        headers = {}
        headers_text = self.headers_input.text().strip()
        if headers_text:
            try:
                headers = _json.loads(headers_text)
            except _json.JSONDecodeError:
                QMessageBox.warning(self, "Hata", "Headers alanı geçerli JSON formatında olmalıdır.")
                return
        
        new_ep = {
            "id": ep_id,
            "name": ep_name,
            "type": self.type_combo.currentText(),
            "model_id": self.model_input.text().strip(),
            "base_url": self.url_input.text().strip() or None,
            "use_key_rotation": self.rotation_check.isChecked(),
            "headers": headers
        }
        
        try:
            from core.llm_provider import load_endpoints, save_endpoints, save_api_keys
            data = load_endpoints()
            endpoints = data.get("endpoints", [])
            
            # Mevcut endpoint'i güncelle veya yeni ekle
            found = False
            for i, ep in enumerate(endpoints):
                if ep["id"] == ep_id:
                    endpoints[i] = new_ep
                    found = True
                    break
            if not found:
                endpoints.append(new_ep)
            
            data["endpoints"] = endpoints
            save_endpoints(data)
            
            # Anahtarları kaydet
            keys_text = self.keys_edit.toPlainText().strip()
            keys = [k.strip() for k in keys_text.split("\n") if k.strip()]
            save_api_keys(ep_id, keys)
            
            QMessageBox.information(self, "Başarılı", f"'{ep_name}' kaydedildi.")
            self._load_list()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {e}")
    
    def delete_endpoint(self):
        current = self.endpoint_list.currentItem()
        if not current:
            return
        idx = self.endpoint_list.row(current)
        
        if QMessageBox.question(self, "Sil", "Bu endpoint'i silmek istediğinize emin misiniz?") != QMessageBox.StandardButton.Yes:
            return
        
        try:
            from core.llm_provider import load_endpoints, save_endpoints
            data = load_endpoints()
            endpoints = data.get("endpoints", [])
            if 0 <= idx < len(endpoints):
                removed = endpoints.pop(idx)
                data["endpoints"] = endpoints
                # Aktif endpoint silindiyse sıfırla
                if data.get("active_endpoint_id") == removed.get("id"):
                    data["active_endpoint_id"] = endpoints[0]["id"] if endpoints else ""
                save_endpoints(data)
                self._load_list()
                self.new_endpoint()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme hatası: {e}")
    
    def set_active_endpoint(self):
        current = self.endpoint_list.currentItem()
        if not current:
            return
        idx = self.endpoint_list.row(current)
        
        try:
            from core.llm_provider import load_endpoints, save_endpoints
            data = load_endpoints()
            endpoints = data.get("endpoints", [])
            if 0 <= idx < len(endpoints):
                data["active_endpoint_id"] = endpoints[idx]["id"]
                save_endpoints(data)
                QMessageBox.information(self, "Başarılı", f"'{endpoints[idx]['name']}' aktif endpoint olarak ayarlandı.")
                self._load_list()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Aktif ayarlama hatası: {e}")
    
    def test_connection(self):
        self.test_result_label.setText("Bağlantı test ediliyor...")
        self.test_result_label.setStyleSheet("color: orange;")
        QApplication.processEvents()
        
        ep_id = self.id_input.text().strip()
        keys_text = self.keys_edit.toPlainText().strip()
        keys = [k.strip() for k in keys_text.split("\n") if k.strip()]
        
        if not keys:
            self.test_result_label.setText("❌ API anahtarı girilmemiş.")
            self.test_result_label.setStyleSheet("color: red;")
            return
        
        # Rastgele bir anahtar seç
        import random
        test_key = random.choice(keys)
        
        try:
            from core.llm_provider import LLMProvider
            import json as _json
            headers = {}
            if self.headers_input.text().strip():
                try:
                    headers = _json.loads(self.headers_input.text().strip())
                except:
                    pass
            
            ep_config = {
                "id": ep_id,
                "name": self.name_input.text().strip(),
                "type": self.type_combo.currentText(),
                "model_id": self.model_input.text().strip(),
                "base_url": self.url_input.text().strip() or None,
                "use_key_rotation": False,
                "headers": headers
            }
            
            provider = LLMProvider(endpoint=ep_config, api_key=test_key)
            success, message = provider.test_connection()
            
            if success:
                self.test_result_label.setText(f"✅ {message}")
                self.test_result_label.setStyleSheet("color: green;")
            else:
                self.test_result_label.setText(f"❌ {message}")
                self.test_result_label.setStyleSheet("color: red;")
        except Exception as e:
            self.test_result_label.setText(f"❌ Hata: {e}")
            self.test_result_label.setStyleSheet("color: red;")
