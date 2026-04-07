"""
Translation Cache — Paragraf bazlı çeviri önbelleği.

Özellikler:
  - Paragraf bazlı cache: her paragraf ayrı ayrı cache'lenir
  - Exact hash match: SHA-1(normalized_text + model_id + prompt_hash)
  - Fuzzy matching: Karakter n-gram Jaccard similarity ile %85+ benzerlikte cache hit
  - LRU temizlik: max_entries aşıldığında en az kullanılan girişler silinir
  - JSON dosya bazlı kalıcı depolama
  - Thread-safe: Asenkron çeviri için RLock korumalı
"""

import os
import json
import hashlib
import time
import threading
import unicodedata
import re
from logger import app_logger


class TranslationCache:
    """Proje bazlı paragraf seviyesinde çeviri önbelleği. Thread-safe."""

    FUZZY_THRESHOLD = 0.85
    NGRAM_SIZE = 3
    MAX_FUZZY_SCAN = 5000

    def __init__(self, project_path: str, max_entries: int = 100000):
        self.cache_folder = os.path.join(project_path, "config", "cache")
        os.makedirs(self.cache_folder, exist_ok=True)
        self.cache_file = os.path.join(self.cache_folder, "translation_cache.json")
        self.max_entries = max_entries
        # Thread-safe erişim için yeniden girilebilir kilit (RLock)
        self._lock = threading.RLock()
        self._cache = self._load()

        # In-memory normalize text index: {key: normalized_text}
        self._norm_index: dict[str, str] = {}
        self._build_norm_index()

    # ────────────────────── Yükleme / Kaydetme ──────────────────────

    def _load(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                app_logger.warning(f"Cache dosyası yüklenemedi: {e}")
        return {}

    def _save(self):
        """Cache'i diske kaydeder. Snapshot alarak kilit dışında yazar (deadlock önlemi)."""
        try:
            with self._lock:
                snapshot = dict(self._cache)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False)
        except Exception as e:
            app_logger.error(f"Cache dosyası kaydedilemedi: {e}")

    def _build_norm_index(self):
        """Mevcut cache girişlerinden normalize text index'i oluşturur."""
        with self._lock:
            self._norm_index.clear()
            for key, entry in self._cache.items():
                orig = entry.get("original_text", "")
                if orig:
                    self._norm_index[key] = self._normalize(orig)

    # ────────────────────── Hash / Normalize ──────────────────────

    @staticmethod
    def _normalize(text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    @staticmethod
    def _make_key(text: str, model_id: str, prompt_hash: str) -> str:
        norm = TranslationCache._normalize(text)
        raw = f"{norm}|{model_id}|{prompt_hash}"
        return hashlib.sha1(raw.encode('utf-8')).hexdigest()

    @staticmethod
    def hash_prompt(prompt: str) -> str:
        return hashlib.sha1(prompt.encode('utf-8')).hexdigest()[:12]

    # ────────────────────── N-gram Similarity ──────────────────────

    @staticmethod
    def _char_ngrams(text: str, n: int = 3) -> set:
        if len(text) < n:
            return {text} if text else set()
        return {text[i:i + n] for i in range(len(text) - n + 1)}

    @classmethod
    def _ngram_similarity(cls, a: str, b: str) -> float:
        if a == b:
            return 1.0
        if not a or not b:
            return 0.0
        len_ratio = min(len(a), len(b)) / max(len(a), len(b))
        if len_ratio < 0.5:
            return 0.0
        ngrams_a = cls._char_ngrams(a, cls.NGRAM_SIZE)
        ngrams_b = cls._char_ngrams(b, cls.NGRAM_SIZE)
        intersection = len(ngrams_a & ngrams_b)
        union = len(ngrams_a | ngrams_b)
        if union == 0:
            return 0.0
        return intersection / union

    # ────────────────────── Paragraf Bazlı API ──────────────────────

    def get_paragraph(self, text: str, model_id: str, prompt_hash: str) -> str | None:
        """Tek paragraf için cache arar. Thread-safe."""
        key = self._make_key(text, model_id, prompt_hash)

        with self._lock:
            entry = self._cache.get(key)
            if entry:
                entry["last_access"] = time.time()
                return entry.get("translation")

        return self._fuzzy_search(text, model_id, prompt_hash)

    def set_paragraph(self, text: str, model_id: str, prompt_hash: str, translation: str):
        """Tek paragrafı cache'e yazar. Thread-safe."""
        key = self._make_key(text, model_id, prompt_hash)
        norm_text = self._normalize(text)

        needs_cleanup = False
        with self._lock:
            self._cache[key] = {
                "original_text": text,
                "translation": translation,
                "model_id": model_id,
                "prompt_hash": prompt_hash,
                "created_at": time.time(),
                "last_access": time.time(),
            }
            self._norm_index[key] = norm_text
            if len(self._cache) > self.max_entries:
                needs_cleanup = True

        if needs_cleanup:
            self._cleanup()

        # _save() kilit DIŞINDA, snapshot alarak çalışır
        self._save()

    def _fuzzy_search(self, text: str, model_id: str, prompt_hash: str) -> str | None:
        """
        Cache'deki girişleri tarayarak fuzzy eşleşme arar.
        Thread-safe: norm_index'in anlık kopyası üzerinde çalışır.
        """
        norm_text = self._normalize(text)
        if not norm_text or len(norm_text) < 10:
            return None

        # Anlık kopya al → iterasyon sırasında dict değişmez
        with self._lock:
            index_snapshot = list(self._norm_index.items())

        best_score = 0.0
        best_key = None
        scan_count = 0

        for key, cached_norm in index_snapshot:
            scan_count += 1
            if scan_count > self.MAX_FUZZY_SCAN:
                break

            with self._lock:
                entry = self._cache.get(key)
            if not entry:
                continue
            if entry.get("model_id") != model_id:
                continue
            if entry.get("prompt_hash") != prompt_hash:
                continue

            score = self._ngram_similarity(norm_text, cached_norm)
            if score > best_score:
                best_score = score
                best_key = key

        if best_score >= self.FUZZY_THRESHOLD and best_key:
            with self._lock:
                entry = self._cache.get(best_key)
                if entry:
                    entry["last_access"] = time.time()
                    result = entry.get("translation")
                else:
                    result = None
            if result:
                app_logger.info(
                    f"Fuzzy cache hit (benzerlik: {best_score:.2%}): "
                    f"'{text[:50]}...' → cached"
                )
            return result

        return None

    # ────────────────────── Eski API (geriye uyumluluk) ──────────────────────

    def get(self, text: str, model_id: str, prompt_hash: str) -> str | None:
        return self.get_paragraph(text, model_id, prompt_hash)

    def set(self, text: str, model_id: str, prompt_hash: str, translation: str):
        self.set_paragraph(text, model_id, prompt_hash, translation)

    # ────────────────────── Paragraf Bölme Yardımcısı ──────────────────────

    @staticmethod
    def split_into_paragraphs(text: str, min_length: int = 20) -> list[str]:
        """Metni paragraflara böler. Çift satır sonu ile ayırır."""
        raw_parts = re.split(r'\n\s*\n', text.strip())
        paragraphs = []
        buffer = ""

        for part in raw_parts:
            part = part.strip()
            if not part:
                continue
            if buffer:
                buffer += "\n\n" + part
            else:
                buffer = part
            if len(buffer) >= min_length:
                paragraphs.append(buffer)
                buffer = ""

        if buffer:
            if paragraphs:
                paragraphs[-1] += "\n\n" + buffer
            else:
                paragraphs.append(buffer)

        return paragraphs if paragraphs else [text]

    # ────────────────────── Temizlik / İstatistik ──────────────────────

    def remove(self, text: str, model_id: str, prompt_hash: str):
        """Belirli bir cache girişini siler."""
        key = self._make_key(text, model_id, prompt_hash)
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._norm_index.pop(key, None)
        self._save()
        app_logger.info(f"Hatalı cache girişi silindi: {key[:12]}...")

    def _cleanup(self):
        """En eski girişleri siler (LRU). Thread-safe."""
        with self._lock:
            if len(self._cache) <= self.max_entries:
                return
            entries = sorted(self._cache.items(), key=lambda x: x[1].get("last_access", 0))
            remove_count = len(self._cache) - self.max_entries
            for i in range(remove_count):
                key = entries[i][0]
                self._cache.pop(key, None)
                self._norm_index.pop(key, None)
        app_logger.info(f"Cache temizliği: {remove_count} giriş silindi.")

    def clear(self):
        """Tüm cache'i temizler."""
        with self._lock:
            self._cache = {}
            self._norm_index.clear()
        self._save()

    def stats(self) -> dict:
        """Cache istatistikleri."""
        with self._lock:
            count = len(self._cache)
        return {
            "entries": count,
            "max_entries": self.max_entries,
            "file_size": os.path.getsize(self.cache_file) if os.path.exists(self.cache_file) else 0,
        }
