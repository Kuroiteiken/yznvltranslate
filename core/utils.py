import re

def format_file_size(size_bytes: int) -> str:
    """Dosya boyutunu okunabilir formata dönüştürür."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def natural_sort_key(s):
    """Metinleri doğal (insan dostu) sıraya göre sıralamak için bir anahtar döndürür."""
    # Sayıları alfanümerik olarak değil, sayısal olarak sıralar
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]