import base64
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

BRAND_ASSET_DIR = Path("assets/brand")
NOISE_TO_SIGNAL_LOGO_PATH = BRAND_ASSET_DIR / "cognivia-full-inverse-clean.png"
NOISE_TO_SIGNAL_INTRO_VIDEO_PATH = BRAND_ASSET_DIR / "video0.mp4"
FOCUS_MODE_ENTER_ICON_PATH = BRAND_ASSET_DIR / "focus-mode-enter-ui.png"
FOCUS_MODE_EXIT_ICON_PATH = BRAND_ASSET_DIR / "focus-mode-exit-ui.png"


@lru_cache(maxsize=32)
def _asset_data_uri(path: Path) -> str | None:
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
    }
    mime_type = mime_types.get(path.suffix.lower())
    if not mime_type or not path.exists():
        return None

    try:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    except OSError:
        logger.exception("Failed to read brand asset: %s", path)
        return None

    return f"data:{mime_type};base64,{encoded}"
