"""
AppSettingsDialog — Uygulama geneli ayarlar penceresi.

Özellikler:
  - Tema seçeneği (Karanlık / Aydınlık / Sistem)
  - ML Terminoloji maks token limiti
  - Özel JS Script kaynağı ekleme (site adı + JS dosya yolu)
  - Log seviyesi seçimi
  - Ayarlar AppConfigs/app_settings.json içinde saklanır
"""

import os
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QGroupBox, QFormLayout, QLineEdit,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QTabWidget, QWidget, QFrame
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from logger import app_logger

APP_SETTINGS_FILE = os.path.join(os.getcwd(), "AppConfigs", "app_settings.json")

DEFAULT_SETTINGS = {
    "theme": "dark",
    "ml_max_tokens": 450000,
    "log_level": "INFO",
    "custom_js_sources": [],   # [{"name": "Site Adı", "js_path": "/path/to/script.js"}, ...]
    "notifications_enabled": True,
    "promt_generator_max_tokens": 40000,
}

THEMES = {
    "dark": "Karanlık Mod",
    "light": "Aydınlık Mod",
    "system": "Sistem Varsayılanı",
}


def load_app_settings() -> dict:
    """AppConfigs/app_settings.json dosyasını okur. Yoksa varsayılanı döndürür."""
    if os.path.exists(APP_SETTINGS_FILE):
        try:
            with open(APP_SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Eksik anahtarları varsayılanla tamamla
            for k, v in DEFAULT_SETTINGS.items():
                data.setdefault(k, v)
            return data
        except Exception as e:
            app_logger.warning(f"app_settings.json okunamadı: {e}")
    return DEFAULT_SETTINGS.copy()


def save_app_settings(settings: dict):
    """Ayarları AppConfigs/app_settings.json dosyasına kaydeder."""
    os.makedirs(os.path.dirname(APP_SETTINGS_FILE), exist_ok=True)
    try:
        with open(APP_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        app_logger.error(f"app_settings.json kaydedilemedi: {e}")


def apply_theme(app, theme_name: str):
    """QSS temasını uygular. AppConfigs/themes/{theme_name}.qss dosyasını okur."""
    if theme_name == "system":
        app.setStyleSheet("")
        return

    theme_file = os.path.join(os.getcwd(), "AppConfigs", "themes", f"{theme_name}.qss")
    if os.path.exists(theme_file):
        try:
            with open(theme_file, "r", encoding="utf-8") as f:
                qss = f.read()
            app.setStyleSheet(qss)
            app_logger.info(f"Tema uygulandı: {theme_name}")
        except Exception as e:
            app_logger.error(f"Tema dosyası okunamadı ({theme_name}): {e}")
    else:
        app_logger.warning(f"Tema dosyası bulunamadı: {theme_file}")


class AppSettingsDialog(QDialog):
    """Uygulama Ayarları Penceresi."""

    settings_changed = pyqtSignal(dict)  # Ayarlar değiştiğinde sinyal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Uygulama Ayarları")
        self.resize(580, 500)
        self.settings = load_app_settings()

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Başlık
        title = QLabel("Uygulama Ayarları")
        title.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Sekmeler
        tabs = QTabWidget()

        # ── Sekme 1: Görünüm ──
        appearance_tab = QWidget()
        app_layout = QFormLayout(appearance_tab)
        app_layout.setSpacing(12)

        self.theme_combo = QComboBox()
        for key, label in THEMES.items():
            self.theme_combo.addItem(label, key)
        current_theme = self.settings.get("theme", "dark")
        idx = list(THEMES.keys()).index(current_theme) if current_theme in THEMES else 0
        self.theme_combo.setCurrentIndex(idx)

        app_layout.addRow("🎨 Tema:", self.theme_combo)

        self.notif_combo = QComboBox()
        self.notif_combo.addItems(["Etkin", "Devre Dışı"])
        self.notif_combo.setCurrentIndex(0 if self.settings.get("notifications_enabled", True) else 1)
        app_layout.addRow("🔔 Bildirimler:", self.notif_combo)

        self.log_combo = QComboBox()
        self.log_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_level = self.settings.get("log_level", "INFO")
        log_idx = ["DEBUG", "INFO", "WARNING", "ERROR"].index(log_level) if log_level in ["DEBUG", "INFO", "WARNING", "ERROR"] else 1
        self.log_combo.setCurrentIndex(log_idx)
        app_layout.addRow("📋 Log Seviyesi:", self.log_combo)

        tabs.addTab(appearance_tab, "🎨 Görünüm")

        # ── Sekme 2: ML / Terminoloji ──
        ml_tab = QWidget()
        ml_layout = QFormLayout(ml_tab)
        ml_layout.setSpacing(12)

        self.ml_token_spin = QSpinBox()
        self.ml_token_spin.setMinimum(50000)
        self.ml_token_spin.setMaximum(2000000)
        self.ml_token_spin.setSingleStep(50000)
        self.ml_token_spin.setValue(self.settings.get("ml_max_tokens", 450000))
        self.ml_token_spin.setSuffix(" token")
        ml_layout.addRow("🤖 ML Maks Token:", self.ml_token_spin)

        token_note = QLabel("Bu değer, Yapay Zeka ile Terminoloji Üret işleminde\ngönderilecek maksimum kaynak metin boyutunu belirler.")
        token_note.setStyleSheet("color: #888; font-size: 9pt;")
        ml_layout.addRow("", token_note)

        self.prompt_gen_token_spin = QSpinBox()
        self.prompt_gen_token_spin.setMinimum(5000)
        self.prompt_gen_token_spin.setMaximum(200000)
        self.prompt_gen_token_spin.setSingleStep(5000)
        self.prompt_gen_token_spin.setValue(self.settings.get("promt_generator_max_tokens", 40000))
        self.prompt_gen_token_spin.setSuffix(" token")
        ml_layout.addRow("📝 Prompt Gen Maks Token:", self.prompt_gen_token_spin)

        prompt_note = QLabel("Bu değer, Prompt Generator'ın bölüm örneklemesi sırasında\nkullanacağı maksimum token limitini belirler.")
        prompt_note.setStyleSheet("color: #888; font-size: 9pt;")
        ml_layout.addRow("", prompt_note)

        tabs.addTab(ml_tab, "🤖 ML / Terminoloji")

        # ── Sekme 3: Özel JS Kaynaklar ──
        js_tab = QWidget()
        js_layout = QVBoxLayout(js_tab)

        js_note = QLabel("İndirme yöntemi listesine özel JavaScript tabanlı site kaynaklarınızı ekleyebilirsiniz.")
        js_note.setWordWrap(True)
        js_note.setStyleSheet("color: #AAA; font-size: 9pt; margin-bottom: 6px;")
        js_layout.addWidget(js_note)

        self.js_list_widget = QListWidget()
        self.js_list_widget.setMaximumHeight(160)
        self._refresh_js_list()
        js_layout.addWidget(self.js_list_widget)

        # Ekleme alanı
        add_frame = QFrame()
        add_layout = QHBoxLayout(add_frame)
        add_layout.setContentsMargins(0, 0, 0, 0)
        self.js_name_input = QLineEdit()
        self.js_name_input.setPlaceholderText("Site adı (örn: Wuxia World)")
        self.js_path_input = QLineEdit()
        self.js_path_input.setPlaceholderText("JS dosya yolu...")
        self.js_path_input.setReadOnly(True)
        browse_btn = QPushButton("📂")
        browse_btn.setFixedWidth(36)
        browse_btn.clicked.connect(self._browse_js_file)
        add_btn = QPushButton("➕ Ekle")
        add_btn.setFixedWidth(80)
        add_btn.clicked.connect(self._add_js_source)
        remove_btn = QPushButton("🗑 Sil")
        remove_btn.setFixedWidth(80)
        remove_btn.clicked.connect(self._remove_js_source)
        add_layout.addWidget(self.js_name_input, 2)
        add_layout.addWidget(self.js_path_input, 3)
        add_layout.addWidget(browse_btn)
        add_layout.addWidget(add_btn)
        add_layout.addWidget(remove_btn)
        js_layout.addWidget(add_frame)

        tabs.addTab(js_tab, "🌐 JS Kaynaklar")

        layout.addWidget(tabs)

        # Alt butonlar
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Kaydet ve Uygula")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        save_btn.clicked.connect(self._save_and_close)
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet("padding: 8px; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    # ──────────── JS Kaynak Yönetimi ────────────

    def _refresh_js_list(self):
        self.js_list_widget.clear()
        for src in self.settings.get("custom_js_sources", []):
            name = src.get("name", "?")
            path = src.get("js_path", "")
            item = QListWidgetItem(f"📄 {name}  ←  {os.path.basename(path)}")
            item.setToolTip(path)
            self.js_list_widget.addItem(item)

    def _browse_js_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "JS Dosyası Seç", "", "JavaScript Dosyaları (*.js);;Tüm Dosyalar (*)"
        )
        if path:
            self.js_path_input.setText(path)

    def _add_js_source(self):
        name = self.js_name_input.text().strip()
        path = self.js_path_input.text().strip()
        if not name or not path:
            QMessageBox.warning(self, "Eksik Bilgi", "Site adı ve JS dosya yolunu doldurun.")
            return
        sources = self.settings.setdefault("custom_js_sources", [])
        # Aynı adda kaynak varsa güncelle
        for src in sources:
            if src["name"] == name:
                src["js_path"] = path
                self._refresh_js_list()
                self.js_name_input.clear()
                self.js_path_input.clear()
                return
        sources.append({"name": name, "js_path": path})
        self._refresh_js_list()
        self.js_name_input.clear()
        self.js_path_input.clear()

    def _remove_js_source(self):
        row = self.js_list_widget.currentRow()
        sources = self.settings.get("custom_js_sources", [])
        if 0 <= row < len(sources):
            sources.pop(row)
            self._refresh_js_list()

    # ──────────── Kaydet ────────────

    def _save_and_close(self):
        self.settings["theme"] = self.theme_combo.currentData()
        self.settings["notifications_enabled"] = self.notif_combo.currentIndex() == 0
        self.settings["log_level"] = self.log_combo.currentText()
        self.settings["ml_max_tokens"] = self.ml_token_spin.value()
        self.settings["promt_generator_max_tokens"] = self.prompt_gen_token_spin.value()
        save_app_settings(self.settings)
        self.settings_changed.emit(self.settings)
        app_logger.info(
            f"Uygulama ayarları kaydedildi: tema={self.settings['theme']}, "
            f"ml_max_tokens={self.settings['ml_max_tokens']}, "
            f"promt_generator_max_tokens={self.settings['promt_generator_max_tokens']}"
        )
        QMessageBox.information(self, "Kaydedildi", "Ayarlar kaydedildi.\nTema değişikliği hemen uygulanacaktır.")
        self.accept()

    def get_settings(self) -> dict:
        return self.settings
