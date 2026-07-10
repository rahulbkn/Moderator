import logging
from functools import lru_cache

from nudenet import NudeDetector

logger = logging.getLogger(__name__)

NSFW_LABELS = {
    "EXPOSED_BREAST_F",
    "EXPOSED_BREAST_M",
    "EXPOSED_GENITALIA_F",
    "EXPOSED_GENITALIA_M",
    "EXPOSED_ANUS",
    "EXPOSED_BUTTOCKS",
    "EXPOSED_PUBIC_AREA",
}

LABEL_MAP = {
    "EXPOSED_BREAST_F": "EXPOSED_BREAST_F",
    "EXPOSED_BREAST_M": "EXPOSED_BREAST_M",
    "EXPOSED_GENITALIA_F": "EXPOSED_GENITALIA_F",
    "EXPOSED_GENITALIA_M": "EXPOSED_GENITALIA_M",
    "EXPOSED_ANUS": "EXPOSED_ANUS",
    "EXPOSED_BUTTOCKS": "EXPOSED_BUTTOCKS",
    "EXPOSED_PUBIC_AREA": "EXPOSED_PUBIC_AREA",
    "FEMALE_BREAST_EXPOSED": "EXPOSED_BREAST_F",
    "FEMALE_GENITALIA_EXPOSED": "EXPOSED_GENITALIA_F",
    "MALE_GENITALIA_EXPOSED": "EXPOSED_GENITALIA_M",
    "ANUS_EXPOSED": "EXPOSED_ANUS",
    "BUTTOCKS_EXPOSED": "EXPOSED_BUTTOCKS",
}


class Moderator:
    def __init__(self):
        self._detector: NudeDetector | None = None

    def load_model(self):
        if self._detector is None:
            logger.info("Loading NudeNet model")
            self._detector = NudeDetector("light")
            logger.info("NudeNet model loaded successfully")

    @property
    def detector(self) -> NudeDetector:
        if self._detector is None:
            self.load_model()
        return self._detector

    def analyze(self, image_path: str) -> dict:
        raw_results = self.detector.detect(image_path)

        detections = []
        max_confidence = 0.0

        for result in raw_results:
            label = result.get("class", "")
            confidence = result.get("score", 0.0)

            mapped_label = LABEL_MAP.get(label, label)
            if mapped_label in NSFW_LABELS and confidence > 0.0:
                detections.append({
                    "label": mapped_label,
                    "confidence": round(confidence, 4),
                })
                if confidence > max_confidence:
                    max_confidence = confidence

        nsfw_score = round(max_confidence, 4)
        safe = nsfw_score < 0.5

        return {
            "success": True,
            "safe": safe,
            "nsfw_score": nsfw_score,
            "detections": detections,
        }


@lru_cache(maxsize=1)
def get_moderator() -> Moderator:
    return Moderator()
