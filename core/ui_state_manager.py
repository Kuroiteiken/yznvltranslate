"""
UIStateManager — Buton etkinleştirme/devre dışı bırakma ve UI durum yönetimi.

Sorumluluklar:
  - İşlem başladığında / bittiğinde tüm butonların durumunu güncelleme
  - Tek bir merkezi noktadan UI durumu kontrolü
"""

from PyQt6.QtWidgets import QPushButton, QProgressBar, QLabel


class UIStateManager:
    """
    Ana penceredeki UI elemanlarının durum yönetimini merkezileştirir.
    
    Kullanım:
        self.ui_state = UIStateManager(self)
        self.ui_state.process_start(self.startButton, "İndiriliyor...")
        self.ui_state.process_end(self.startButton, "İndirmeyi Başlat")
    """

    def __init__(self, main_window):
        self.win = main_window

    def process_start(
        self,
        active_button: QPushButton,
        button_label: str,
        button_color: str = "#FFC107",
        button_text_color: str = "black",
        progress_max: int = 100,
        status_text: str = "İşlem başlatıldı...",
    ):
        """İşlem başlangıcında UI'ı hazırlar."""
        win = self.win
        active_button.setText(button_label)
        active_button.setStyleSheet(
            f"background-color: {button_color}; color: {button_text_color}; "
            f"border-radius: 5px; padding: 10px; font-weight: bold;"
        )
        active_button.setEnabled(False)

        win.progressBar.setMaximum(progress_max)
        win.progressBar.setValue(0)
        win.progressBar.setVisible(True)
        win.statusLabel.setText(f"Durum: {status_text}")

        self._disable_all_buttons(except_button=active_button)

    def process_end(
        self,
        active_button: QPushButton,
        button_label: str,
        button_color: str = "#4CAF50",
        button_text_color: str = "white",
        status_text: str = "Hazır",
    ):
        """İşlem bitişinde UI'ı normal haline getirir."""
        win = self.win
        active_button.setText(button_label)
        active_button.setStyleSheet(
            f"background-color: {button_color}; color: {button_text_color}; "
            f"border-radius: 5px; padding: 10px; font-weight: bold;"
        )
        active_button.setEnabled(True)

        win.progressBar.setVisible(False)
        win.statusLabel.setText(f"Durum: {status_text}")

        self._enable_all_buttons()

    def _disable_all_buttons(self, except_button: QPushButton = None):
        """Tüm aksiyonel butonları devre dışı bırakır."""
        win = self.win
        buttons = self._get_all_action_buttons()
        for btn in buttons:
            if btn is not except_button:
                btn.setEnabled(False)

    def _enable_all_buttons(self):
        """Proje seçiliyse tüm aksiyonel butonları etkinleştirir."""
        win = self.win
        project_selected = win.current_project_path is not None
        buttons_needing_project = self._get_all_action_buttons()
        for btn in buttons_needing_project:
            btn.setEnabled(project_selected)

    def _get_all_action_buttons(self) -> list[QPushButton]:
        """Tüm aksiyonel butonların listesini döndürür."""
        win = self.win
        buttons = []
        for attr in [
            "startButton", "splitButton", "translateButton", "mergeButton",
            "token_count_button", "errorCheckButton", "epubButton",
            "projectSettingsButton", "helpButton", "selectHighlightedButton",
            "generateTerminologyButton",
        ]:
            btn = getattr(win, attr, None)
            if btn is not None:
                buttons.append(btn)
        return buttons
