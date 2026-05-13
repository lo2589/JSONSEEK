import locale
from typing import Optional


def detect_file_encoding(path: str) -> str:
    """Detect file encoding by trying common encodings.

    Order:
    1. Check BOM markers
    2. Try UTF-8
    3. Try locale preferred encoding
    4. Try common CJK encodings
    Falls back to UTF-8 if all fail.
    """
    with open(path, "rb") as f:
        raw = f.read()

    if not raw:
        return "utf-8"

    # 1. BOM detection
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if raw.startswith(b"\xfe\xff"):
        return "utf-16-be"

    # 2. Try UTF-8 with heuristic validation
    try:
        text = raw.decode("utf-8")
        if _looks_like_utf8(text):
            return "utf-8"
    except UnicodeDecodeError:
        pass

    # 3. Try locale preferred encoding
    system_encoding = locale.getpreferredencoding(False)
    if system_encoding and system_encoding.lower() != "utf-8":
        try:
            raw.decode(system_encoding)
            return system_encoding
        except (UnicodeDecodeError, LookupError):
            pass

    # 4. Try common CJK encodings
    for enc in ("gb18030", "gbk", "gb2312", "big5", "shift_jis", "euc-kr", "utf-16"):
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            pass


def _looks_like_utf8(text: str) -> bool:
    """Heuristic: detect UTF-8 misdetection of GBK/Chinese text.

    GBK bytes sometimes form valid UTF-8 sequences but decode to
    Hebrew/Arabic/Thai characters. If >10% of chars fall in those
    ranges, treat as misdetected.
    """
    suspicious_ranges = [
        (0x0590, 0x08FF),   # Hebrew, Arabic, Syriac
        (0x0900, 0x097F),   # Devanagari
        (0x0E00, 0x0E7F),   # Thai
    ]
    suspicious = 0
    for ch in text:
        cp = ord(ch)
        for start, end in suspicious_ranges:
            if start <= cp <= end:
                suspicious += 1
                break
    if not text:
        return True
    return (suspicious / len(text)) <= 0.1


def resolve_encoding(path: str, encoding: Optional[str] = None) -> str:
    """Resolve final encoding: use explicit if given, else auto-detect."""
    if encoding:
        return encoding
    return detect_file_encoding(path)
