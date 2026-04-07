"""
StatusBarManager — Uygulama alt bilgi barı oluşturucu ve güncelleyici.
"""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton


class StatusBarManager:
    def __init__(self, main_window):
        self.win = main_window

    def create(self):
        win = self.win
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        status_frame.setStyleSheet("""
            QFrame { background-color: #263238; color: #B0BEC5; border-top: 1px solid #37474F; padding: 2px 8px; }
            QLabel { color: #B0BEC5; font-size: 9pt; }
        """)
        status_frame.setFixedHeight(30)
        bar_layout = QHBoxLayout(status_frame)
        bar_layout.setContentsMargins(8, 0, 8, 0)
        bar_layout.setSpacing(15)

        win.sb_status_label = QLabel("🟢 Hazır")
        win.sb_model_label = QLabel("🤖 Model: -")
        win.sb_api_label = QLabel("🔑 API: -")
        win.sb_speed_label = QLabel("⚡ Hız: -")
        win.sb_requests_label = QLabel("📡 İstek: 0")
        win.sb_tokens_label = QLabel("📊 Token: 0")
        win.sb_refresh_btn = QPushButton("↻")
        win.sb_refresh_btn.setFixedWidth(30)
        win.sb_refresh_btn.setStyleSheet("color: #80CBC4; background: transparent; border: none; font-size: 12pt;")
        win.sb_refresh_btn.setToolTip("UI Yeniden Yükle")
        win.sb_refresh_btn.clicked.connect(win.update_file_list_from_selection)

        for w in [win.sb_status_label, win.sb_model_label, win.sb_api_label,
                   win.sb_speed_label, win.sb_requests_label, win.sb_tokens_label]:
            bar_layout.addWidget(w)
        bar_layout.addStretch()
        bar_layout.addWidget(win.sb_refresh_btn)
        win.outer_layout.addWidget(status_frame)

    def update(self):
        win = self.win
        status_icon = "🟢" if win._current_status == "Hazır" else "🟡"
        win.sb_status_label.setText(f"{status_icon} {win._current_status}")
        win.sb_model_label.setText(f"🤖 Model: {win._current_model or '-'}")
        win.sb_api_label.setText(f"🔑 API: {win._current_api_name or '-'}")
        current_req_count = win.request_counter_manager.get_count(win._current_model, win._current_api_name)
        win.sb_requests_label.setText(f"📡 İstek: {current_req_count}")
        win.sb_tokens_label.setText(f"📊 Token: {win._api_token_count}")
        if win._translation_speed > 0:
            win.sb_speed_label.setText(f"⚡ Hız: {win._translation_speed:.1f} dk/bölüm")
        else:
            win.sb_speed_label.setText("⚡ Hız: -")
