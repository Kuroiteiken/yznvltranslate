"""
TokenController — Token sayma işlemi iş mantığı kontrolcüsü.

Sorumluluklar:
  - Token sayma thread/worker oluşturma ve yaşam döngüsü yönetimi
  - Token cache yönetimi
  - Tablo güncelleme mantığı (token sütunları)
"""

import os
import configparser
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from core.workers.token_counter import save_token_data
from core.workers.token_count_worker import TokenCountWorker
from logger import app_logger


class TokenController:
    """Token sayma işlemlerini yönetir."""

    def __init__(self, main_window):
        self.win = main_window
        self.thread = None
        self.worker = None

    def start(self):
        """Token sayma işlemini başlatır."""
        if not self.win.current_project_path:
            QMessageBox.warning(self.win, "Proje Seçilmedi", "Token saymak için lütfen önce bir proje seçin.")
            return

        self._stop_existing()

        # Sadece seçilen dosyaları belirle
        selected_files = []
        for row in range(self.win.file_table.rowCount()):
            checkbox_item = self.win.file_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                orig_name = self.win.file_table.item(row, 1).text() if self.win.file_table.item(row, 1) else ""
                trans_name = self.win.file_table.item(row, 2).text() if self.win.file_table.item(row, 2) else ""

                if orig_name and orig_name != "Yok" and orig_name != "Orijinali Yok":
                    selected_files.append(orig_name)
                if trans_name and trans_name != "Yok":
                    selected_files.append(trans_name)

        if not selected_files:
            QMessageBox.warning(self.win, "Uyarı", "Lütfen token hesaplanmasını istediğiniz dosyaları kutucuklarından işaretleyin.")
            return

        config_path = os.path.join(self.win.current_project_path, 'config', 'config.ini')
        api_key = ""
        mcp_endpoint_id = None
        if os.path.exists(config_path):
            try:
                self.win.config.read(config_path)
                api_key = self.win.config.get('API', 'gemini_api_key', fallback="")
                mcp_endpoint_id = self.win.config.get('MCP', 'endpoint_id', fallback=None)
            except configparser.Error:
                api_key = ""
                mcp_endpoint_id = None

        if not api_key and not mcp_endpoint_id:
            QMessageBox.warning(self.win, "API Anahtarı / MCP Eksik", "Token sayımı için Gemini API anahtarı veya MCP bağlantısı gereklidir. Lütfen proje ayarlarına girerek yapılandırın.")
            self.win.total_tokens_label.setText("Toplam Token: API Anahtarı Yok")
            self.win.total_original_tokens_label.setText("Orijinal Token: API Anahtarı Yok")
            self.win.total_translated_tokens_label.setText("Çevrilen Token: API Anahtarı Yok")
            self.win.token_progress_bar.setVisible(False)
            self.win.total_tokens_label.setVisible(True)
            self.win.total_original_tokens_label.setVisible(True)
            self.win.total_translated_tokens_label.setVisible(True)
            return

        # UI butonlarını devre dışı bırak
        self.win.startButton.setEnabled(False)
        self.win.translateButton.setEnabled(False)
        self.win.mergeButton.setEnabled(False)
        self.win.projectSettingsButton.setEnabled(False)
        self.win.selectHighlightedButton.setEnabled(False)
        self.win.token_count_button.setEnabled(False)
        self.win.token_count_button.setText("Sayılıyor...")
        self.win.token_count_button.setStyleSheet("background-color: #FFC107; color: black; border-radius: 5px; padding: 10px;")
        self.win.token_progress_bar.setValue(0)
        self.win.token_progress_bar.setMaximum(0)
        self.win.token_progress_bar.setVisible(True)
        self.win.statusLabel.setText("Durum: Token'lar hesaplanıyor...")
        self.win.total_tokens_label.setText("Toplam Token: Hesaplıyor...")
        self.win.total_original_tokens_label.setText("Orijinal Token: Hesaplıyor...")
        self.win.total_translated_tokens_label.setText("Çevrilen Token: Hesaplıyor...")
        self.win.total_tokens_label.setVisible(True)
        self.win.total_original_tokens_label.setVisible(True)
        self.win.total_translated_tokens_label.setVisible(True)

        self.thread = QThread()
        gemini_version = self.win.get_gemini_model_version()
        self.worker = TokenCountWorker(
            self.win.current_project_path, api_key, self.win.project_token_cache,
            gemini_version, selected_files, endpoint_id=mcp_endpoint_id
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_finished)
        self.worker.progress.connect(self._on_progress)
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self._cleanup)

        self.thread.start()
        app_logger.info("Token sayım thread'i başlatıldı.")

    def _on_progress(self, current, total):
        self.win.token_progress_bar.setMaximum(total)
        self.win.token_progress_bar.setValue(current)
        self.win.statusLabel.setText(f"Durum: Token sayılıyor... Dosya {current}/{total}")

    def _on_finished(self, results):
        import time as _time
        _t0 = _time.time()
        app_logger.info("Token sayımı tamamlandı. UI güncelleniyor...")
        self.win.statusLabel.setText("Durum: Token sayımı tamamlandı.")
        self.win.token_progress_bar.setVisible(False)
        self.win.token_count_button.setText("Token Say")
        self.win.token_count_button.setStyleSheet("background-color: #673AB7; color: white; border-radius: 5px; padding: 10px;")
        self.win._set_all_buttons_enabled_state(True)

        # Önbelleği güncelleyelim
        self.win.project_token_cache = results
        config_folder_path = os.path.join(self.win.current_project_path, 'config')
        save_token_data(config_folder_path, self.win.project_token_cache)

        file_tokens = results['file_token_data']
        total_original = results['total_original_tokens']
        total_translated = results['total_translated_tokens']
        total_combined = results['total_combined_tokens']

        # Tablo güncelleme (performans optimizeli)
        self.win.file_table.setSortingEnabled(False)
        self.win.file_table.setUpdatesEnabled(False)
        model = self.win.file_table.model()
        model.blockSignals(True)
        try:
            for row in range(self.win.file_table.rowCount()):
                original_file_name = self.win.file_table.item(row, 1).text()
                translated_file_name = self.win.file_table.item(row, 2).text()
                status_text = self.win.file_table.item(row, 5).text()

                original_token_str = "Yok"
                translated_token_str = "Yok"

                if original_file_name != "Orijinali Yok" and original_file_name != "N/A" and original_file_name in file_tokens:
                    original_token_val = file_tokens[original_file_name].get("original_tokens")
                    original_token_str = str(original_token_val) if original_token_val is not None else "Hata/N/A"

                if translated_file_name != "Yok" and translated_file_name != "N/A" and translated_file_name in file_tokens:
                    if "Birleştirildi" in status_text:
                        translated_token_val = file_tokens[translated_file_name].get("merged_tokens")
                    else:
                        translated_token_val = file_tokens[translated_file_name].get("translated_tokens")
                    translated_token_str = str(translated_token_val) if translated_token_val is not None else "Hata/Yok"

                original_token_item = QTableWidgetItem(original_token_str)
                translated_token_item = QTableWidgetItem(translated_token_str)

                if "Hata" in original_token_str or original_token_str == "N/A":
                    original_token_item.setForeground(QColor(Qt.GlobalColor.red))
                if "Hata" in translated_token_str or translated_token_str == "Yok" or translated_token_str == "N/A":
                    translated_token_item.setForeground(QColor(Qt.GlobalColor.red))

                self.win.file_table.setItem(row, 6, original_token_item)
                self.win.file_table.setItem(row, 7, translated_token_item)
        finally:
            model.blockSignals(False)
            self.win.file_table.setSortingEnabled(True)
            self.win.file_table.setUpdatesEnabled(True)
            self.win.file_table.viewport().update()

        # Genel token bilgilerini güncelle
        self.win.total_tokens_label.setText(f"Toplam Token (Orijinal + Çevrilen): {total_combined}")
        self.win.total_original_tokens_label.setText(f"Toplam Orijinal Token: {total_original}")
        self.win.total_translated_tokens_label.setText(f"Toplam Çevrilen Token: {total_translated}")
        self.win.total_tokens_label.setVisible(True)
        self.win.total_original_tokens_label.setVisible(True)
        self.win.total_translated_tokens_label.setVisible(True)
        app_logger.info(f"[PERF] Token sayımı UI güncellemesi tamamlandı: {_time.time()-_t0:.3f}s")

    def _on_error(self, message):
        app_logger.error(f"Token sayım hatası: {message}")
        QMessageBox.critical(self.win, "Token Sayım Hatası", f"Token sayımı sırasında bir hata oluştu:\n{message}")
        self.win.statusLabel.setText(f"Durum: Token sayım hatası - {message}")
        self.win.token_progress_bar.setVisible(False)
        self.win.token_count_button.setText("Token Say")
        self.win.token_count_button.setStyleSheet("background-color: #673AB7; color: white; border-radius: 5px; padding: 10px;")
        self.win._set_all_buttons_enabled_state(True)
        self.win.total_tokens_label.setText("Toplam Token: Hata")
        self.win.total_original_tokens_label.setText("Orijinal Token: Hata")
        self.win.total_translated_tokens_label.setText("Çevrilen Token: Hata")
        self.win.total_tokens_label.setVisible(True)
        self.win.total_original_tokens_label.setVisible(True)
        self.win.total_translated_tokens_label.setVisible(True)

    def _cleanup(self):
        """Token sayım thread'ini güvenli şekilde temizler."""
        app_logger.info("Token sayım thread'i temizleniyor...")
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        if self.thread:
            self.thread.deleteLater()
            self.thread = None
        app_logger.info("Token sayım thread'i temizlendi.")

    def _stop_existing(self):
        if self.thread and self.thread.isRunning():
            self.worker.stop()
            self.thread.quit()
            self.thread.wait(1000)
            self.thread = None
            self.worker = None

    def is_running(self):
        return self.thread is not None and self.thread.isRunning()

    def stop(self):
        if self.worker:
            self.worker.stop()
