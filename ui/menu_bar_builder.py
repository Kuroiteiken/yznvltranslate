"""
MenuBarBuilder — Ana pencere menü barı oluşturucu.

Sorumluluklar:
  - Menü barı yapısını oluşturma
  - Menü aksiyonlarını bağlama
  - JS dosya kaydetme işlemi
"""

import os
import shutil
from PyQt6.QtWidgets import QMessageBox, QFileDialog


def build_menu_bar(main_window):
    """Ana pencere menü barını oluşturur ve aksiyonları bağlar."""
    win = main_window
    menu_bar = win.menuBar()

    # ── Dosya Menüsü ──
    file_menu = menu_bar.addMenu("Dosya")
    new_project_action = file_menu.addAction("Yeni Proje")
    new_project_action.triggered.connect(win.new_project_clicked)
    save_action = file_menu.addAction("Ayarları Kaydet")
    save_action.triggered.connect(win.open_project_settings_dialog)
    exit_action = file_menu.addAction("Çıkış")
    exit_action.triggered.connect(win.close)

    # ── Proje Menüsü ──
    project_menu = menu_bar.addMenu("Proje")
    delete_project_action = project_menu.addAction("Proje Sil")
    delete_project_action.triggered.connect(win.delete_project_clicked)
    project_settings_action = project_menu.addAction("Proje Ayarları")
    project_settings_action.triggered.connect(win.open_project_settings_dialog)

    # ── Ayarlar Menüsü ──
    settings_menu = menu_bar.addMenu("Ayarlar")
    prompt_editor_action = settings_menu.addAction("Promt Editörü")
    prompt_editor_action.triggered.connect(win.open_prompt_editor)
    apikey_editor_action = settings_menu.addAction("API Key Editörü")
    apikey_editor_action.triggered.connect(win.open_apikey_editor)
    gemini_version_action = settings_menu.addAction("Gemini Versiyon")
    gemini_version_action.triggered.connect(win.open_gemini_version_dialog)
    mcp_action = settings_menu.addAction("Yapay Zeka Kaynağı (MCP)")
    mcp_action.triggered.connect(win.open_mcp_dialog)
    app_settings_action = settings_menu.addAction("⚙️ Uygulama Ayarları")
    app_settings_action.triggered.connect(win.open_app_settings_dialog)

    # ── JS Kaydet Menüsü ──
    js_save_menu = menu_bar.addMenu("JS Kaydet")
    save_booktoki_action = js_save_menu.addAction("Booktoki")
    save_booktoki_action.triggered.connect(lambda: _save_js_file(win, "booktoki.js"))
    save_69shuba_action = js_save_menu.addAction("69shuba")
    save_69shuba_action.triggered.connect(lambda: _save_js_file(win, "69shuba.js"))
    save_novelfire_action = js_save_menu.addAction("Novelfire")
    save_novelfire_action.triggered.connect(lambda: _save_js_file(win, "novelfire.js"))

    # ── Yardım Menüsü ──
    help_menu = menu_bar.addMenu("Yardım")
    about_action = help_menu.addAction("Hakkında")
    about_action.triggered.connect(win.show_about_dialog)
    api_stats_action = help_menu.addAction("📊 API Kullanım İstatistikleri")
    api_stats_action.triggered.connect(win.show_api_stats_dialog)


def _save_js_file(main_window, js_filename):
    """Kullanıcının seçtiği JS dosyasını istediği yere kaydetmesini sağlar."""
    source_path = os.path.join(os.getcwd(), js_filename)

    if not os.path.exists(source_path):
        try:
            from core.js_create import create_js_file
            create_js_file(js_filename)
        except Exception:
            pass

    if not os.path.exists(source_path):
        QMessageBox.warning(main_window, "Dosya Bulunamadı", f"'{js_filename}' dosyası ana dizinde bulunamadı!")
        return

    default_save_path = os.path.join(os.path.expanduser("~"), "Desktop", js_filename)
    save_path, _ = QFileDialog.getSaveFileName(
        main_window, f"{js_filename} Dosyasını Kaydet", default_save_path,
        "JavaScript Files (*.js);;All Files (*)"
    )

    if save_path:
        try:
            shutil.copy2(source_path, save_path)
            QMessageBox.information(main_window, "Başarılı", f"Dosya başarıyla kaydedildi:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(main_window, "Kayıt Hatası", f"Dosya kaydedilirken bir hata oluştu:\n{str(e)}")
