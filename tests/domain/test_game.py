"""Unit tests for game domain logic."""

from emotional_numbers_mk_ii.domain.game import generate_rule_set


class TestRuleSetGeneration:
    """Tests for deterministic rule set generation."""

    def test_regions_do_not_overlap(self):
        """No two regions share the same cell position."""
        rule_set = generate_rule_set(seed=12345)

        all_positions = []
        for region in rule_set.regions:
            all_positions.extend(region.positions)

        # If no overlaps, unique count equals total count
        assert len(all_positions) == len(set(all_positions))

    def test_generates_five_regions(self):
        """Generates exactly 5 regions, one per bucket."""
        rule_set = generate_rule_set(seed=12345)

        assert len(rule_set.regions) == 5
        buckets = [r.bucket for r in rule_set.regions]
        assert set(buckets) == {"01", "02", "03", "04", "05"}

    def test_deterministic_with_same_seed(self):
        """Same seed produces identical regions."""
        rule_set1 = generate_rule_set(seed=99999)
        rule_set2 = generate_rule_set(seed=99999)

        for r1, r2 in zip(rule_set1.regions, rule_set2.regions):
            assert r1.bucket == r2.bucket
            assert r1.positions == r2.positions

    def test_different_seeds_produce_different_regions(self):
        """Different seeds produce different region positions."""
        rule_set1 = generate_rule_set(seed=11111)
        rule_set2 = generate_rule_set(seed=22222)

        positions1 = set(pos for r in rule_set1.regions for pos in r.positions)
        positions2 = set(pos for r in rule_set2.regions for pos in r.positions)

        # Very unlikely to be identical with different seeds
        assert positions1 != positions2
