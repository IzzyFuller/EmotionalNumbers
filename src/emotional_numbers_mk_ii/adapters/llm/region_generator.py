"""Algorithmic region generator - creates non-overlapping contiguous regions."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class GeneratedRegion:
    """A generated region with id and positions."""

    id: int
    positions: list[tuple[int, int]]


def generate_regions(
    rows: int,
    cols: int,
    num_regions: int = 5,
    min_size: int = 3,
    max_size: int = 8,
    seed: int | None = None,
) -> list[GeneratedRegion]:
    """Generate non-overlapping contiguous regions.

    Uses seed points with BFS growth to create organic, irregular shapes.

    Args:
        rows: Grid height.
        cols: Grid width.
        num_regions: Number of regions to generate.
        min_size: Minimum cells per region.
        max_size: Maximum cells per region.
        seed: Random seed for reproducibility.

    Returns:
        List of GeneratedRegion with id and positions.
    """
    rng = random.Random(seed)
    used: set[tuple[int, int]] = set()
    regions: list[GeneratedRegion] = []

    # Generate well-spaced seed points
    seeds = _generate_seed_points(rows, cols, num_regions, rng)

    for i, (sx, sy) in enumerate(seeds):
        target_size = rng.randint(min_size, max_size)
        positions = _grow_region(sx, sy, target_size, rows, cols, used, rng)

        if len(positions) >= min_size:
            used.update(positions)
            regions.append(GeneratedRegion(id=i + 1, positions=positions))

    return regions


def _generate_seed_points(
    rows: int, cols: int, count: int, rng: random.Random
) -> list[tuple[int, int]]:
    """Generate well-spaced seed points using simple grid subdivision."""
    seeds: list[tuple[int, int]] = []

    # Divide grid into roughly equal zones
    zone_cols = cols // 3
    zone_rows = rows // 2

    # Generate candidate positions in different zones
    zones = [
        (0, 0, zone_cols, zone_rows),
        (zone_cols, 0, zone_cols * 2, zone_rows),
        (zone_cols * 2, 0, cols, zone_rows),
        (0, zone_rows, zone_cols, rows),
        (zone_cols, zone_rows, zone_cols * 2, rows),
        (zone_cols * 2, zone_rows, cols, rows),
    ]

    rng.shuffle(zones)

    for i in range(min(count, len(zones))):
        x1, y1, x2, y2 = zones[i]
        # Pick random point within zone, with margin
        margin = 2
        x = rng.randint(x1 + margin, max(x1 + margin, x2 - margin - 1))
        y = rng.randint(y1 + margin, max(y1 + margin, y2 - margin - 1))
        seeds.append((x, y))

    # If we need more seeds than zones, add random points
    while len(seeds) < count:
        x = rng.randint(2, cols - 3)
        y = rng.randint(2, rows - 3)
        # Check minimum distance from existing seeds
        if all(abs(x - sx) + abs(y - sy) > 5 for sx, sy in seeds):
            seeds.append((x, y))

    return seeds[:count]


def _grow_region(
    start_x: int,
    start_y: int,
    target_size: int,
    rows: int,
    cols: int,
    used: set[tuple[int, int]],
    rng: random.Random,
) -> list[tuple[int, int]]:
    """Grow a contiguous region from a seed point using randomized BFS."""
    if (start_x, start_y) in used:
        return []

    positions: list[tuple[int, int]] = [(start_x, start_y)]
    frontier: list[tuple[int, int]] = [(start_x, start_y)]

    while len(positions) < target_size and frontier:
        # Pick random cell from frontier
        current = rng.choice(frontier)
        cx, cy = current

        # Get valid neighbors
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if (
                0 <= nx < cols
                and 0 <= ny < rows
                and (nx, ny) not in used
                and (nx, ny) not in positions
            ):
                neighbors.append((nx, ny))

        if neighbors:
            # Add random neighbor to region
            new_cell = rng.choice(neighbors)
            positions.append(new_cell)
            frontier.append(new_cell)
        else:
            # No valid neighbors, remove from frontier
            frontier.remove(current)

    return positions
