import unittest

from config import settings
from falconsai_detector import FalconsAIModerator
from moderation import Moderator, calculate_nsfw_score


class FakeDetector:
    def __init__(self, detections):
        self._detections = detections

    def detect(self, image_path):
        return self._detections


class ModerationScoringTests(unittest.TestCase):
    def setUp(self):
        self._falconsai_enabled = settings.falconsai_enabled
        settings.falconsai_enabled = False

    def tearDown(self):
        settings.falconsai_enabled = self._falconsai_enabled

    def test_aggregates_multiple_sensitive_covered_detections(self):
        moderator = Moderator()
        moderator._detector = FakeDetector([
            {"class": "FEMALE_BREAST_COVERED", "score": 0.30},
            {"class": "BUTTOCKS_COVERED", "score": 0.30},
            {"class": "FEMALE_GENITALIA_COVERED", "score": 0.20},
        ])

        result = moderator.analyze("/tmp/example.jpg")

        self.assertFalse(result["safe"])
        self.assertEqual(result["nsfw_score"], 0.4275)
        self.assertEqual(
            [detection["label"] for detection in result["detections"]],
            ["COVERED_BREAST_F", "COVERED_BUTTOCKS", "COVERED_GENITALIA_F"],
        )

    def test_single_weak_covered_detection_is_not_unsafe(self):
        moderator = Moderator()
        moderator._detector = FakeDetector([
            {"class": "FEMALE_BREAST_COVERED", "score": 0.30},
        ])

        result = moderator.analyze("/tmp/example.jpg")

        self.assertTrue(result["safe"])
        self.assertEqual(result["nsfw_score"], 0.255)

    def test_falconsai_nsfw_signal_marks_unsafe(self):
        moderator = Moderator()
        moderator._detector = FakeDetector([
            {"label": "FALCONSAI_NSFW", "confidence": 0.8},
        ])

        result = moderator.analyze("/tmp/example.jpg")

        self.assertFalse(result["safe"])
        self.assertEqual(result["nsfw_score"], 0.8)
        self.assertEqual(result["detections"][0]["label"], "FALCONSAI_NSFW")

    def test_calculate_nsfw_score_caps_at_one(self):
        self.assertEqual(calculate_nsfw_score([0.95, 0.9, 0.8]), 1.0)


class FalconsAIModeratorTests(unittest.TestCase):
    def setUp(self):
        self._falconsai_enabled = settings.falconsai_enabled
        settings.falconsai_enabled = True

    def tearDown(self):
        settings.falconsai_enabled = self._falconsai_enabled

    def test_maps_classifier_nsfw_output(self):
        moderator = FalconsAIModerator()
        moderator._classifier = lambda image_path: [
            {"label": "normal", "score": 0.01},
            {"label": "nsfw", "score": 0.93},
        ]

        self.assertEqual(
            moderator.analyze("/tmp/example.jpg"),
            [{"label": "FALCONSAI_NSFW", "confidence": 0.93}],
        )


if __name__ == "__main__":
    unittest.main()
