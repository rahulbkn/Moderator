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


def resize_image(image_bytes: bytes, max_size: int) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    if max(image.width, image.height) > max_size:
        ratio = max_size / max(image.width, image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.LANCZOS)
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85)
    return output.getvalue()


async def prepare_image(url: str) -> str:
    error = validate_image_url(url)
    if error:
        raise ValueError(error)

    logger.info("Downloading image: %s", url)
    image_data = await download_image(url)

    logger.info("Resizing image to max %dpx", settings.max_image_size)
    resized = resize_image(image_data, settings.max_image_size)

    # Force using an absolute string path cleanly generated across platforms
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
    
    try:
        with os.fdopen(tmp_fd, 'wb') as tmp_file:
            tmp_file.write(resized)
    except Exception as e:
        os.unlink(tmp_path)
        raise e

    # Cast to pure absolute string path to destroy any temporary file pointer objects
    final_path = str(Path(tmp_path).resolve())
    logger.info("Image saved to temporary file: %s", final_path)
    
    return final_path
