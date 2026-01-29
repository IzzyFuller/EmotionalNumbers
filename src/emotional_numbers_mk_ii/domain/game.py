"""Game domain entity - owns grid, selection, classification, progress."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class Cell:
    """A single cell in the grid."""

    x: int
    y: int
    value: int
    selected: bool = False
    classified: bool = False


@dataclass
class Region:
    """A hidden region belonging to a bucket."""

    bucket: str
    positions: list[tuple[int, int]]


@dataclass
class RegionBehavior:
    """Behavior parameters for a bucket's region."""

    bucket: str
    jiggle_intensity: float  # 0.0 - 1.0
    jiggle_frequency: float  # How often cells jiggle
    sound_id: str  # Reference to sound asset


@dataclass
class RuleSet:
    """Collection of regions that define the puzzle."""

    regions: list[Region]
    behaviors: list[RegionBehavior] = field(default_factory=list)
    buckets: list[str] = field(default_factory=lambda: ["01", "02", "03", "04", "05"])

    def get_bucket_for_position(self, x: int, y: int) -> str | None:
        """Return the bucket a position belongs to, or None if not in any region."""
        for region in self.regions:
            if (x, y) in region.positions:
                return region.bucket
        return None


class Game:
    """Game state - grid, selection, classification, progress."""

    def __init__(self, rows: int, cols: int, rule_set: RuleSet, seed: int | None = None):
        self.rows = rows
        self.cols = cols
        self.rule_set = rule_set
        self._rng = random.Random(seed)
        self._grid = self._generate_grid()
        self._bins: dict[str, int] = {b: 0 for b in rule_set.buckets}

    def _generate_grid(self) -> list[list[Cell]]:
        """Generate grid with random values."""
        grid = []
        for y in range(self.rows):
            row = []
            for x in range(self.cols):
                value = self._rng.randint(0, 9)
                row.append(Cell(x=x, y=y, value=value))
            grid.append(row)
        return grid

    @property
    def grid(self) -> list[list[Cell]]:
        return self._grid

    @property
    def bins(self) -> dict[str, int]:
        return self._bins

    @property
    def progress(self) -> int:
        """Calculate completion percentage."""
        total = self.rows * self.cols
        classified = sum(
            1 for row in self._grid for cell in row if cell.classified
        )
        return round((classified / total) * 100) if total > 0 else 0

    @property
    def selected_positions(self) -> list[tuple[int, int]]:
        """Return list of selected positions."""
        return [
            (cell.x, cell.y)
            for row in self._grid
            for cell in row
            if cell.selected
        ]

    def toggle_selection(self, x: int, y: int) -> None:
        """Toggle selection of a cell."""
        cell = self._grid[y][x]
        cell.selected = not cell.selected

    def clear_selection(self) -> int:
        """Clear all selections. Returns count cleared."""
        count = 0
        for row in self._grid:
            for cell in row:
                if cell.selected:
                    cell.selected = False
                    count += 1
        return count

    def classify(self, bucket: str) -> tuple[bool, int]:
        """
        Classify selected cells to a bucket.

        Returns (success, count).
        Success is True only if ALL selected cells belong to that bucket's region.
        """
        selected = [(cell.x, cell.y) for row in self._grid for cell in row if cell.selected]

        # Check if all selected cells belong to the target bucket
        for x, y in selected:
            cell_bucket = self.rule_set.get_bucket_for_position(x, y)
            if cell_bucket != bucket:
                # Wrong bucket - clear selection and fail
                self.clear_selection()
                return False, 0

        # Success - classify the cells
        count = 0
        for row in self._grid:
            for cell in row:
                if cell.selected and not cell.classified:
                    cell.classified = True
                    cell.selected = False
                    count += 1

        self._bins[bucket] += count
        return True, count

    def get_hint(self) -> dict | None:
        """Return a hint about an unclassified region."""
        for region in self.rule_set.regions:
            # Find unclassified positions in this region
            unclassified = [
                pos for pos in region.positions
                if not self._grid[pos[1]][pos[0]].classified
            ]
            if unclassified:
                return {
                    "bucket": region.bucket,
                    "positions": unclassified[:4],  # Hint shows up to 4 positions
                }
        return None


def answers_to_seed(answers: list[dict]) -> int:
    """Convert answers to a numeric seed."""
    combined = "|".join(f"{a['questionId']}:{a['answer']}" for a in answers)
    hash_val = 0
    for char in combined:
        hash_val = ((hash_val << 5) - hash_val + ord(char)) & 0xFFFFFFFF
    return hash_val


def generate_rule_set(seed: int, rows: int = 25, cols: int = 40) -> RuleSet:
    """Generate a deterministic RuleSet from a seed."""
    rng = random.Random(seed)
    buckets = ["01", "02", "03", "04", "05"]
    sound_pool = ["tone_01", "tone_02", "tone_03", "tone_04", "tone_05"]
    regions = []
    behaviors = []
    used_positions: set[tuple[int, int]] = set()

    for bucket in buckets:
        # Try to place a non-overlapping region
        for _ in range(100):  # Max attempts
            region_x = rng.randint(2, cols - 6)
            region_y = rng.randint(2, rows - 6)
            region_w = rng.randint(2, 4)
            region_h = rng.randint(2, 4)

            positions = [
                (region_x + dx, region_y + dy)
                for dy in range(region_h)
                for dx in range(region_w)
            ]

            # Check for overlap
            if not any(pos in used_positions for pos in positions):
                used_positions.update(positions)
                regions.append(Region(bucket=bucket, positions=positions))
                break

    # Generate behaviors for each bucket (using same seeded RNG)
    for bucket in buckets:
        behaviors.append(
            RegionBehavior(
                bucket=bucket,
                jiggle_intensity=rng.random(),  # 0.0 - 1.0
                jiggle_frequency=rng.uniform(0.5, 2.0),  # 0.5 - 2.0 Hz
                sound_id=rng.choice(sound_pool),
            )
        )

    return RuleSet(regions=regions, behaviors=behaviors, buckets=buckets)
