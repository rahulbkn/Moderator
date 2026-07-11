import json
import logging
from functools import lru_cache
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

LIKELIHOOD_SCORES = {
    0: 0.0,   # UNKNOWN
    1: 0.05,  # VERY_UNLIKELY
    2: 0.15,  # UNLIKELY
    3: 0.5,   # POSSIBLE
    4: 0.8,   # LIKELY
    5: 0.95,  # VERY_LIKELY
}

SAFE_SEARCH_LABELS = {
    "adult": "VISION_ADULT",
    "racy": "VISION_RACY",
}


class CloudVisionModerator:
    def __init__(self):
        self._client = None

    @property
    def enabled(self) -> bool:
        return bool(
            settings.cloud_vision_enabled
            or settings.google_cloud_vision_credentials_json
        )

    def load_client(self):
        if self._client is not None:
            return

        from google.cloud import vision
        from google.oauth2 import service_account

        if settings.google_cloud_vision_credentials_json:
            credential_info = json.loads(settings.google_cloud_vision_credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credential_info
            )
            self._client = vision.ImageAnnotatorClient(credentials=credentials)
        else:
            self._client = vision.ImageAnnotatorClient()

        logger.info("Google Cloud Vision client loaded successfully")

    @property
    def client(self):
        if self._client is None:
            self.load_client()
        return self._client

    def analyze(self, image_path: str) -> list[dict]:
        if not self.enabled:
            return []

        from google.cloud import vision

        content = Path(image_path).read_bytes()
        image = vision.Image(content=content)
        response = self.client.safe_search_detection(image=image)

        if response.error.message:
            raise RuntimeError(f"Cloud Vision SafeSearch failed: {response.error.message}")

        annotation = response.safe_search_annotation
        detections = []
        for attribute, label in SAFE_SEARCH_LABELS.items():
            likelihood = getattr(annotation, attribute)
            score = LIKELIHOOD_SCORES.get(likelihood, 0.0)
            if score >= settings.cloud_vision_min_score:
                detections.append({
                    "label": label,
                    "confidence": score,
                })

        return detections


@lru_cache(maxsize=1)
def get_cloud_vision_moderator() -> CloudVisionModerator:
    return CloudVisionModerator()
