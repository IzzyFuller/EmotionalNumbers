"""Mock MLX adapter for testing - no MLX dependency."""

from emotional_numbers_mk_ii.domain.game import Region, RegionBehavior, RuleSet


class MLXQuestionGenerator:
    """Test double - returns fixed questions without MLX."""

    def generate_questions(self) -> list[dict]:
        return [
            {"id": "q1", "text": "What smell reminds you of safety?"},
            {"id": "q2", "text": "Describe the texture of comfort."},
            {"id": "q3", "text": "What color is your anxiety?"},
            {"id": "q4", "text": "Rate your compliance from 1-10."},
            {"id": "q5", "text": "What sound do you associate with work?"},
        ]


class MLXRuleGenerator:
    """Test double - returns fixed rules without MLX."""

    def generate_rules(self, answers: list[dict], rows: int, cols: int) -> RuleSet:
        return RuleSet(
            regions=[
                Region(bucket="01", positions=[(5, 10), (6, 10), (5, 11), (6, 11)]),
                Region(bucket="02", positions=[(20, 3), (21, 3), (22, 3), (20, 4), (21, 4)]),
                Region(bucket="03", positions=[(10, 15), (11, 15), (12, 15), (13, 15)]),
                Region(bucket="04", positions=[(30, 20), (31, 20), (30, 21), (31, 21)]),
                Region(bucket="05", positions=[(2, 2), (3, 2), (2, 3), (3, 3)]),
            ],
            behaviors=[
                RegionBehavior(bucket="01", jiggle_intensity=0.3, jiggle_frequency=1.2, sound_id="tone_01"),
                RegionBehavior(bucket="02", jiggle_intensity=0.7, jiggle_frequency=1.1, sound_id="tone_02"),
                RegionBehavior(bucket="03", jiggle_intensity=0.5, jiggle_frequency=1.5, sound_id="tone_03"),
                RegionBehavior(bucket="04", jiggle_intensity=0.25, jiggle_frequency=1.0, sound_id="tone_04"),
                RegionBehavior(bucket="05", jiggle_intensity=0.9, jiggle_frequency=0.6, sound_id="tone_05"),
            ],
        )
