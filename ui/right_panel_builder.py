"""
RightPanelBuilder — Sağ panel (butonlar, progress bar, durum etiketi) oluşturucu.

Sorumluluklar:
  - Sağ paneldeki tüm butonları, widget'ları ve layout'u oluşturma
  - Butonların sinyal bağlantılarını yapma
"""

from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QCheckBox, QSpinBox, QProgressBar, QMessageBox
)


def build_right_panel(main_window):
    """Sağ paneli oluşturur ve main_layout'a ekler. Tüm widget'lar main_window üzerine atanır."""
    win = main_window
    right_layout = QVBoxLayout()

    # ── İndirme Yöntemi ──
    win.downloadMethodCombo = QComboBox()
    win.downloadMethodCombo.addItems([
        "Booktoki JS İle İndir (Selenium)",
        "69shuba JS İle İndir (Selenium)",
        "Novelfire JS İle İndir (Selenium)",
        "Normal Web Kazıma (Requests) (Tavsiye Edilmez)"
    ])
    win.downloadMethodCombo.setStyleSheet(
        "QComboBox QAbstractItemView { background-color: #2D2D30; color: white; "
        "selection-background-color: #3F51B5; } padding: 5px; font-size: 10pt;"
    )
    right_layout.addWidget(QLabel("İndirme Yöntemi:"))
    right_layout.addWidget(win.downloadMethodCombo)

    # ── İndirme Butonu ──
    win.startButton = QPushButton("İndirmeyi Başlat")
    win.startButton.setFont(QFont("Arial", 11, QFont.Weight.Bold))
    win.startButton.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 5px; padding: 10px;")
    win.startButton.clicked.connect(win.start_download_process)
    right_layout.addWidget(win.startButton)

    # ── Toplu Bölüm Ekle ──
    win.splitButton = QPushButton("Toplu Bölüm Ekle")
    win.splitButton.setFont(QFont("Arial", 11, QFont.Weight.Bold))
    win.splitButton.setStyleSheet("background-color: #3F51B5; color: white; border-radius: 5px; padding: 10px;")
    win.splitButton.clicked.connect(win.start_split_process)
    right_layout.addWidget(win.splitButton)

    # ── Çeviri Butonu ──
    win.translateButton = QPushButton("Seçilenleri Çevir")
    win.translateButton.setFont(QFont("Arial", 11, QFont.Weight.Bold))
    win.translateButton.setStyleSheet("background-color: #2196F3; color: white; border-radius: 5px; padding: 10px;")
    win.translateButton.clicked.connect(win.start_translation_process)
    win.translateButton.setEnabled(False)
    right_layout.addWidget(win.translateButton)

    # ── Sayılı Çevir ──
    limit_layout = QHBoxLayout()
    win.limit_checkbox = QCheckBox("Sayılı çevir")
    win.limit_checkbox.setFont(QFont("Arial", 9))
    win.limit_checkbox.setToolTip("İşaretlenirse sadece yandaki sayı kadar dosya çevrilip durur.")
    win.limit_spinbox = QSpinBox()
    win.limit_spinbox.setMinimum(1)
    win.limit_spinbox.setMaximum(99999)
    win.limit_spinbox.setValue(20)
    win.limit_spinbox.setEnabled(True)
    win.limit_checkbox.toggled.connect(win.limit_spinbox.setEnabled)
    limit_layout.addWidget(win.limit_checkbox)
    limit_layout.addWidget(win.limit_spinbox)
    right_layout.addLayout(limit_layout)

    # ── Kapatma Checkbox ──
    win.shutdown_checkbox = QCheckBox("Çeviri Bitince Bilgisayarı Kapat")
    win.shutdown_checkbox.setFont(QFont("Arial", 9))
    win.shutdown_checkbox.setStyleSheet("margin-left: 5px; margin-bottom: 5px;")
    win.shutdown_checkbox.toggled.connect(win.on_shutdown_checkbox_toggled)
    right_layout.addWidget(win.shutdown_checkbox)

    # ── Birleştirme Butonu ──
    win.mergeButton = QPushButton("Seçili Çevirileri Birleştir")
    win.mergeButton.setFont(QFont("Arial", 11, QFont.Weight.Bold))
    win.mergeButton.setStyleSheet("background-color: #9C27B0; color: white; border-radius: 5px; padding: 10px;")
    win.mergeButton.clicked.connect(win.start_merging_process)
    win.mergeButton.setEnabled(False)
    right_layout.addWidget(win.mergeButton)

    # ── Durdur Butonu ──
    win.stopTranslationButton = QPushButton("■ Çeviriyi Durdur")
    win.stopTranslationButton.setFont(QFont("Arial", 9, QFont.Weight.Bold))
    win.stopTranslationButton.setStyleSheet("background-color: #F44336; color: white; border-radius: 5px; padding: 6px;")
    win.stopTranslationButton.clicked.connect(win.stop_translation_process)
    win.stopTranslationButton.setVisible(False)
    right_layout.addWidget(win.stopTranslationButton)

    # ── Hata Kontrol Butonu ──
    win.errorCheckButton = QPushButton("Çeviri Hata Kontrol")
    win.errorCheckButton.setFont(QFont("Arial", 11, QFont.Weight.Bold))
    win.errorCheckButton.setStyleSheet("background-color: #009688; color: white; border-radius: 5px; padding: 10px;")
    win.errorCheckButton.clicked.connect(win.start_error_check_process)
    win.errorCheckButton.setEnabled(False)
    right_layout.addWidget(win.errorCheckButton)

    # ── EPUB Butonu ──
    win.epubButton = QPushButton("Seçilenleri EPUB Yap")
    win.epubButton.setFont(QFont("Arial", 11, QFont.Weight.Bold))
    win.epubButton.setStyleSheet("background-color: #795548; color: white; border-radius: 5px; padding: 10px;")
    win.epubButton.clicked.connect(win.start_epub_process)
    win.epubButton.setEnabled(False)
    right_layout.addWidget(win.epubButton)

    # ── Token Say Butonu ──
    win.token_count_button = QPushButton("Token Say")
    win.token_count_button.setFont(QFont("Arial", 11, QFont.Weight.Bold))
    win.token_count_button.setStyleSheet("background-color: #673AB7; color: white; border-radius: 5px; padding: 10px;")
    win.token_count_button.clicked.connect(win.start_token_counting_manually)
    win.token_count_button.setEnabled(False)
    right_layout.addWidget(win.token_count_button)

    # ── Progress Bar ──
    win.progressBar = QProgressBar(win)
    win.progressBar.setTextVisible(True)
    win.progressBar.setAlignment(Qt.AlignmentFlag.AlignCenter)
    win.progressBar.setVisible(False)
    right_layout.addWidget(win.progressBar)

    # ── Durum Etiketi ──
    win.statusLabel = QLabel("Durum: Hazır")
    win.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
    win.statusLabel.setFont(QFont("Arial", 10))
    win.statusLabel.setWordWrap(True)
    right_layout.addWidget(win.statusLabel)

    # ── Token Bilgileri ──
    win.total_tokens_label = QLabel("Toplam Token: 0")
    win.total_original_tokens_label = QLabel("Orijinal Token: 0")
    win.total_translated_tokens_label = QLabel("Çevrilen Token: 0")
    win.token_progress_bar = QProgressBar(win)
    win.token_progress_bar.setTextVisible(True)
    win.token_progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
    win.token_progress_bar.setVisible(False)
    token_info_layout = QVBoxLayout()
    token_info_layout.addWidget(win.total_tokens_label)
    token_info_layout.addWidget(win.total_original_tokens_label)
    token_info_layout.addWidget(win.total_translated_tokens_label)
    token_info_layout.addWidget(win.token_progress_bar)
    right_layout.addLayout(token_info_layout)

    # ── Seç (Vurgulananları İşaretle) ──
    win.selectHighlightedButton = QPushButton("Seç (Vurgulananları İşaretle)")
    win.selectHighlightedButton.setFont(QFont("Arial", 10))
    win.selectHighlightedButton.setStyleSheet("background-color: #607D8B; color: white; border-radius: 5px; padding: 7px;")
    win.selectHighlightedButton.clicked.connect(win.mark_highlighted_rows_checked)
    right_layout.addWidget(win.selectHighlightedButton)

    # ── Terminoloji Butonu ──
    win.generateTerminologyButton = QPushButton("Yapay Zeka İle Terminoloji Üret")
    win.generateTerminologyButton.setFont(QFont("Arial", 10, QFont.Weight.Bold))
    win.generateTerminologyButton.setStyleSheet("background-color: #E91E63; color: white; border-radius: 5px; padding: 7px;")
    win.generateTerminologyButton.clicked.connect(win.start_ml_terminology_process)
    win.generateTerminologyButton.setEnabled(False)
    right_layout.addWidget(win.generateTerminologyButton)

    # ── Proje Ayarları ──
    win.projectSettingsButton = QPushButton("Proje Ayarları")
    win.projectSettingsButton.setFont(QFont("Arial", 10))
    win.projectSettingsButton.setStyleSheet("background-color: #008CBA; color: white; border-radius: 5px; padding: 7px;")
    win.projectSettingsButton.clicked.connect(win.open_project_settings_dialog)
    right_layout.addWidget(win.projectSettingsButton)

    # ── Yardım ──
    win.helpButton = QPushButton("Yardım")
    win.helpButton.setFont(QFont("Arial", 10))
    win.helpButton.setStyleSheet("background-color: #008CBA; color: white; border-radius: 5px; padding: 7px;")
    win.helpButton.clicked.connect(win.show_help_clicked)
    right_layout.addWidget(win.helpButton)

    right_layout.addStretch()
    win.main_layout.addLayout(right_layout, 1)
