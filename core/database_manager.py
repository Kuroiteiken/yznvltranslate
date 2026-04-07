"""
DatabaseManager — Projeler için SQLite veritabanı işlemlerini yönetir.
Klasör aramaları (os.listdir) yerine I/O işlemlerini hızlandırmayı sağlar.
"""
import sqlite3
import os
import time
from logger import app_logger

class DatabaseManager:
    """Proje dosyaları için SQLite veritabanı adaptörü."""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.db_path = os.path.join(project_path, 'config', 'project_data.db')

    def db_exists(self) -> bool:
        """Veritabanının var olup olmadığını kontrol eder."""
        return os.path.exists(self.db_path)

    def init_db(self):
        """Veritabanı bağlantısı açar, tablo yoksa oluşturur."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Files Tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                sort_key TEXT PRIMARY KEY,
                original_file_name TEXT,
                original_file_path TEXT,
                original_creation_time TEXT,
                original_file_size TEXT,
                translated_file_name TEXT,
                translated_file_path TEXT,
                translation_status TEXT,
                cleaning_status TEXT,
                is_translated BOOLEAN,
                is_cleaned BOOLEAN,
                original_token_count TEXT,
                translated_token_count TEXT,
                display_status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_all_files(self) -> list[dict]:
        """Tüm kayıtları 'sort_key' bazlı (doğal sayı okuma uyumlu olarak daha sonra list manager'da sortlanır) çeker."""
        if not self.db_exists():
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM files")
        rows = cursor.fetchall()
        conn.close()
        
        # SQLite satırlarını dict objesine dönüştür
        results = []
        for row in rows:
            results.append({
                "sort_key": row["sort_key"],
                "original_file_name": row["original_file_name"],
                "original_file_path": row["original_file_path"],
                "original_creation_time": row["original_creation_time"],
                "original_file_size": row["original_file_size"],
                "translated_file_name": row["translated_file_name"],
                "translated_file_path": row["translated_file_path"],
                "translation_status": row["translation_status"],
                "cleaning_status": row["cleaning_status"],
                "is_translated": bool(row["is_translated"]),
                "is_cleaned": bool(row["is_cleaned"]),
                "original_token_count": row["original_token_count"],
                "translated_token_count": row["translated_token_count"],
                "display_status": row["display_status"]
            })
            
        return results

    def upsert_files(self, files_data: list[dict]):
        """Liste halindeki dosya objelerini veritabanına yazar (varsa günceller, yoksa ekler)."""
        if not files_data:
            return

        self.init_db() # Tablo yoksa emin ol
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        insert_query = '''
            INSERT INTO files (
                sort_key, original_file_name, original_file_path, original_creation_time, original_file_size,
                translated_file_name, translated_file_path, translation_status, cleaning_status,
                is_translated, is_cleaned, original_token_count, translated_token_count, display_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sort_key) DO UPDATE SET
                original_file_name=excluded.original_file_name,
                original_file_path=excluded.original_file_path,
                original_creation_time=excluded.original_creation_time,
                original_file_size=excluded.original_file_size,
                translated_file_name=excluded.translated_file_name,
                translated_file_path=excluded.translated_file_path,
                translation_status=excluded.translation_status,
                cleaning_status=excluded.cleaning_status,
                is_translated=excluded.is_translated,
                is_cleaned=excluded.is_cleaned,
                original_token_count=excluded.original_token_count,
                translated_token_count=excluded.translated_token_count,
                display_status=excluded.display_status
        '''

        # Veriyi demet(tuple) listesine çevirelim
        data_tuples = []
        for entry in files_data:
            data_tuples.append((
                entry.get("sort_key"),
                entry.get("original_file_name"),
                entry.get("original_file_path"),
                entry.get("original_creation_time"),
                entry.get("original_file_size"),
                entry.get("translated_file_name"),
                entry.get("translated_file_path"),
                entry.get("translation_status"),
                entry.get("cleaning_status"),
                entry.get("is_translated", False),
                entry.get("is_cleaned", False),
                entry.get("original_token_count"),
                entry.get("translated_token_count"),
                entry.get("display_status")
            ))

        try:
            # executemany ile çok hızlı insert
            cursor.executemany(insert_query, data_tuples)
            conn.commit()
            app_logger.info(f"DB Upsert: {len(files_data)} dosya işlemi başarılı.")
        except Exception as e:
            app_logger.error(f"Veritabanı kayıt hatası (upsert_files): {e}")
            conn.rollback()
        finally:
            conn.close()

    def sync_directory_to_db(self, legacy_file_list_manager) -> bool:
        """
        Klasik FileListManager vasıtasıyla tek seferliğine dizinleri tarayıp tüm veriyi SQLite'a geçirir.
        Dışa dönük bir 'Migration' fonksiyonu olarak konumlandırılmıştır.
        """
        try:
            # Geri dönüşümden kaçınmak ve yavaş taramayı tek kullanımlık koşturmak
            data = legacy_file_list_manager.get_file_list_data_legacy()
            files_data = data.get("sorted_entries", [])
            self.upsert_files(files_data)
            return True
        except Exception as e:
            app_logger.error(f"Migration hatası (sync_directory_to_db): {e}")
            return False
