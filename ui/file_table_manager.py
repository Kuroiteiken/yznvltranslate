"""
FileTableManager — Ana penceredeki QTableWidget (Dosya Listesi) yönetimini sağlar.
"""
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class FileTableManager:
    """QTableWidget üzerinde dosya verilerini göstermek için UI yöneticisi."""
    def __init__(self, table_widget: QTableWidget):
        self.table = table_widget
        self._setup_table()

    def _setup_table(self):
        """Tablonun sütun ve görünüm ayarlarını yapar."""
        headers = ["Seç", "Orijinal Dosya", "Çevrilen Dosya", "Oluşturma Tarihi", "Boyut", "Durum", "Orijinal Token", "Çevrilen Token"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Seç
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          # Orijinal Dosya
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          # Çevrilen Dosya
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)      # Oluşturma Tarihi
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)      # Boyut
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)      # Durum
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)      # Orijinal Token
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)      # Çevrilen Token
        
        # Sütunları daraltarak ekrana sığdır
        self.table.setColumnWidth(0, 30)   # Seç
        self.table.setColumnWidth(1, 110)  # Orijinal Dosya
        self.table.setColumnWidth(2, 160)  # Çevrilen Dosya
        self.table.setColumnWidth(3, 125) # Tarih
        self.table.setColumnWidth(4, 70)  # Boyut
        self.table.setColumnWidth(5, 90)  # Durum
        self.table.setColumnWidth(6, 100)  # Orijinal Token
        self.table.setColumnWidth(7, 100)  # Çevrilen Token
        self.table.setAlternatingRowColors(True)

    def populate(self, sorted_entries: list[dict]):
        """FileListManager'dan gelen verilerle tabloyu doldurur."""
        self.table.setRowCount(len(sorted_entries))
        for row, entry_data in enumerate(sorted_entries):
            self._populate_row(row, entry_data)

    def _populate_row(self, row: int, entry_data: dict):
        # Column 0: Checkbox
        checkbox_item = QTableWidgetItem()
        checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        checkbox_item.setCheckState(Qt.CheckState.Unchecked)
        self.table.setItem(row, 0, checkbox_item)

        # Column 1: Original File Name
        self.table.setItem(row, 1, QTableWidgetItem(entry_data["original_file_name"]))

        # Column 2: Translated File Name
        self.table.setItem(row, 2, QTableWidgetItem(entry_data["translated_file_name"] if entry_data["translated_file_name"] else "Yok"))
        
        # Column 3: Creation Date (Original)
        self.table.setItem(row, 3, QTableWidgetItem(entry_data["original_creation_time"]))
        
        # Column 4: Size (Original)
        self.table.setItem(row, 4, QTableWidgetItem(entry_data["original_file_size"]))
        
        # Column 5: Status 
        status_text = entry_data["display_status"]
        status_item = QTableWidgetItem(status_text)
        
        if status_text.startswith("Hata:"):
            status_item.setForeground(QColor(Qt.GlobalColor.red)) 
            status_item.setToolTip(status_text)
        elif status_text == "Çevrildi" or status_text == "Birleştirildi": 
            status_item.setForeground(QColor(Qt.GlobalColor.darkGreen)) 
        elif status_text == "Orijinali Yok, Çevrildi":
            status_item.setForeground(QColor(Qt.GlobalColor.darkGreen)) 
        elif status_text == "Orijinali Yok":
            status_item.setForeground(QColor(Qt.GlobalColor.darkMagenta)) 
        else: 
            status_item.setForeground(QColor(Qt.GlobalColor.darkGray)) 
        
        self.table.setItem(row, 5, status_item)

        # Column 6: Original Token Count
        original_token_item = QTableWidgetItem(str(entry_data["original_token_count"]))
        if isinstance(entry_data["original_token_count"], str) and "Hesaplanmadı" in entry_data["original_token_count"]:
            original_token_item.setForeground(QColor(Qt.GlobalColor.blue))
        self.table.setItem(row, 6, original_token_item)
        
        # Column 7: Translated Token Count
        translated_token_item = QTableWidgetItem(str(entry_data["translated_token_count"]))
        if isinstance(entry_data["translated_token_count"], str) and ("Hesaplanmadı" in entry_data["translated_token_count"] or "Yok" in entry_data["translated_token_count"]):
            translated_token_item.setForeground(QColor(Qt.GlobalColor.blue))
        self.table.setItem(row, 7, translated_token_item)
