import unittest

from moderation import Moderator, calculate_nsfw_score


class FakeDetector:
    def __init__(self, detections):
        self._detections = detections

    def detect(self, image_path):
        return self._detections


class ModerationScoringTests(unittest.TestCase):
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

    def test_cloud_vision_racy_signal_marks_unsafe(self):
        moderator = Moderator()
        moderator._detector = FakeDetector([
            {"label": "VISION_RACY", "confidence": 0.8},
        ])

        result = moderator.analyze("/tmp/example.jpg")

        self.assertFalse(result["safe"])
        self.assertEqual(result["nsfw_score"], 0.8)
        self.assertEqual(result["detections"][0]["label"], "VISION_RACY")

    def test_calculate_nsfw_score_caps_at_one(self):
        self.assertEqual(calculate_nsfw_score([0.95, 0.9, 0.8]), 1.0)


if __name__ == "__main__":
    unittest.main()
