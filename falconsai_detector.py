import logging
from functools import lru_cache

from config import settings

logger = logging.getLogger(__name__)

NSFW_OUTPUT_LABELS = {
    "nsfw",
    "porn",
    "sexy",
    "hentai",
}


class FalconsAIModerator:
    def __init__(self):
        self._classifier = None

    @property
    def enabled(self) -> bool:
        return settings.falconsai_enabled

    def load_model(self):
        if self._classifier is not None:
            return

        from transformers import pipeline

        logger.info("Loading FalconsAI NSFW model: %s", settings.falconsai_model_name)
        self._classifier = pipeline(
            "image-classification",
            model=settings.falconsai_model_name,
        )
        logger.info("FalconsAI NSFW model loaded successfully")

    @property
    def classifier(self):
        if self._classifier is None:
            self.load_model()
        return self._classifier

    def analyze(self, image_path: str) -> list[dict]:
        if not self.enabled:
            return []

        results = self.classifier(image_path)
        detections = []
        for result in results:
            label = result.get("label", "").lower()
            confidence = result.get("score", 0.0)
            if label in NSFW_OUTPUT_LABELS and confidence >= settings.falconsai_min_score:
                detections.append({
                    "label": "FALCONSAI_NSFW",
                    "confidence": confidence,
                })

        return detections


@lru_cache(maxsize=1)
def get_falconsai_moderator() -> FalconsAIModerator:
    return FalconsAIModerator()
