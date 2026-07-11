import io
import logging
import tempfile
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image

from config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def validate_image_url(url: str) -> str | None:
    if not url or not isinstance(url, str):
        return "URL must be a non-empty string"

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return "URL must use HTTP or HTTPS scheme"

    ext = Path(parsed.path).suffix.lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        return f"URL must point to an image file ({', '.join(ALLOWED_EXTENSIONS)})"

    if settings.allowed_domains:
        hostname = parsed.hostname or ""
        if not any(hostname.endswith(domain) for domain in settings.allowed_domains):
            return f"Only images from allowed domains are accepted ({', '.join(settings.allowed_domains)})"

    return None


async def download_image(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "image" not in content_type:
            raise ValueError(f"URL does not point to an image (Content-Type: {content_type})")
        return response.content


def resize_image(image_bytes: bytes, max_size: int, min_size: int) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    longest_edge = max(image.width, image.height)
    if longest_edge > max_size:
        ratio = max_size / longest_edge
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.LANCZOS)
    elif longest_edge < min_size:
        ratio = min_size / longest_edge
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.LANCZOS)
    if image.mode != "RGB":
        image = image.convert("RGB")

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=90)
    return output.getvalue()


async def prepare_image(url: str) -> str:
    error = validate_image_url(url)
    if error:
        raise ValueError(error)

    logger.info("Downloading image: %s", url)
    image_data = await download_image(url)

    logger.info(
        "Resizing image to min %dpx and max %dpx",
        settings.min_image_size,
        settings.max_image_size,
    )
    resized = resize_image(
        image_data, settings.max_image_size, settings.min_image_size
    )

    # Create temporary file and write image data
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
    
    try:
        with os.fdopen(tmp_fd, 'wb') as tmp_file:
            tmp_file.write(resized)
    except Exception:
        try:
            os.close(tmp_fd)
        except OSError:
            pass
        os.unlink(tmp_path)
        raise

    # Convert to absolute string path
    final_path = str(Path(tmp_path).resolve())
    logger.info("Image saved to temporary file: %s", final_path)
    
    return final_path
