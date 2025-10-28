from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGO_CANDIDATES = [
    BASE_DIR / "assets" / "boeira_logo.png",
    BASE_DIR / "assets" / "boeira_logo.jpg",
    BASE_DIR / "assets" / "boeira_logo.jpeg",
]
QRCODE_CANDIDATES = [
    BASE_DIR / "assets" / "qrcode.png",
    BASE_DIR / "assets" / "qrcode.jpg",
    BASE_DIR / "assets" / "qrcode.jpeg",
    BASE_DIR / "assets" / "qrcode.svg",
]


def get_logo_path() -> Path:
    """Retorna o caminho absoluto do logotipo."""
    for candidate in LOGO_CANDIDATES:
        if candidate.exists():
            return candidate
    return LOGO_CANDIDATES[0]


@lru_cache(maxsize=1)
def get_logo_data_uri() -> str:
    """Retorna o logotipo como data URI (base64) para uso em HTML/CSS."""
    logo_path = get_logo_path()
    if not logo_path.exists():
        return ""
    data = logo_path.read_bytes()
    suffix = logo_path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def get_qrcode_path() -> Path:
    """Retorna o caminho do QR Code, se existir."""
    for candidate in QRCODE_CANDIDATES:
        if candidate.exists():
            return candidate
    return QRCODE_CANDIDATES[0]


@lru_cache(maxsize=1)
def get_qrcode_data_uri() -> str:
    """Retorna o QR Code como data URI."""
    qrcode_path = get_qrcode_path()
    if not qrcode_path.exists():
        return ""
    data = qrcode_path.read_bytes()
    suffix = qrcode_path.suffix.lower()
    if suffix == ".svg":
        mime = "image/svg+xml"
    elif suffix == ".png":
        mime = "image/png"
    else:
        mime = "image/jpeg"
    encoded = base64.b64encode(data).decode("utf-8")
    return f"data:{mime};base64,{encoded}"
