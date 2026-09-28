import random
import sys
import unittest
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "drawing-pixel-art" / "scripts"))

import bands  # noqa: E402

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def brute_force_layer(spans, width, height):
    """Independent ground truth: multi-source BFS on a grid padded with a transparent border,
    so the canvas edge counts as an immediate boundary exactly like bands() intends."""
    solid = [[False] * width for _ in range(height)]
    for y, (a, b) in spans.items():
        for x in range(a, b + 1):
            solid[y][x] = True

    pw, ph = width + 2, height + 2
    psolid = [[False] * pw for _ in range(ph)]
    for y in range(height):
        for x in range(width):
            psolid[y + 1][x + 1] = solid[y][x]

    dist = [[None] * pw for _ in range(ph)]
    dq = deque()
    for y in range(ph):
        for x in range(pw):
            if not psolid[y][x]:
                dist[y][x] = 0
                dq.append((x, y))
    while dq:
        x, y = dq.popleft()
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < pw and 0 <= ny < ph and dist[ny][nx] is None:
                dist[ny][nx] = dist[y][x] + 1
                dq.append((nx, ny))
    layer = [[dist[y + 1][x + 1] for x in range(width)] for y in range(height)]
    return solid, layer


def random_spans(rng, width, height):
    spans = {}
    for y in range(height):
        if rng.random() < 0.15:
            continue  # some rows are fully transparent, to force concave shapes
        a = rng.randint(0, width - 1)
        b = rng.randint(a, width - 1)
        spans[y] = (a, b)
    return spans


class BandsTest(unittest.TestCase):
    def test_matches_brute_force_bfs_on_a_solid_square(self):
        spans = {y: (2, 9) for y in range(2, 10)}
        self.assertEqual(bands.bands(spans, 12, 12), brute_force_layer(spans, 12, 12))

    def test_matches_brute_force_bfs_on_a_staircase(self):
        # each row narrower than the last on one side: concave across rows despite a single span per row
        spans = {0: (0, 9), 1: (0, 9), 2: (2, 9), 3: (2, 9), 4: (5, 9), 5: (5, 9), 6: (0, 9), 7: (0, 9)}
        self.assertEqual(bands.bands(spans, 10, 8), brute_force_layer(spans, 10, 8))

    def test_matches_brute_force_bfs_on_random_shapes(self):
        rng = random.Random(1234)
        for _ in range(20):
            w, h = rng.randint(4, 16), rng.randint(4, 16)
            spans = random_spans(rng, w, h)
            if not spans:
                continue
            self.assertEqual(bands.bands(spans, w, h), brute_force_layer(spans, w, h))

    def test_rejects_a_span_outside_the_canvas(self):
        with self.assertRaises(ValueError):
            bands.bands({0: (0, 5)}, 4, 4)

    def test_rejects_a_row_outside_the_canvas(self):
        with self.assertRaises(ValueError):
            bands.bands({9: (0, 2)}, 4, 4)


class BevelIndexTest(unittest.TestCase):
    """An 8x8 solid square in a 12x12 canvas (rows/cols 2..9), light from the upper-left."""

    def setUp(self):
        self.solid, _ = bands.bands({y: (2, 9) for y in range(2, 10)}, 12, 12)

    def index(self, x, y):
        return bands.bevel_index(x, y, self.solid, lo=0, hi=6)

    def test_true_diagonal_corner_facing_the_light_reads_as_the_brightest_step(self):
        self.assertEqual(self.index(2, 2), 6)

    def test_true_diagonal_corner_facing_away_reads_as_the_darkest_step(self):
        self.assertEqual(self.index(9, 9), 0)

    def test_corner_perpendicular_to_the_light_axis_averages_to_a_neutral_step(self):
        # top-right and bottom-left are each equidistant from two boundary directions at a right
        # angle to each other; averaging them (instead of picking whichever the scan saw first)
        # gives a neutral mid-ramp step, not a value indistinguishable from the lit corner.
        self.assertEqual(self.index(9, 2), 3)
        self.assertEqual(self.index(2, 9), 3)

    def test_a_flat_edge_with_a_single_nearest_direction_is_unaffected(self):
        self.assertEqual(self.index(5, 2), 5)   # top edge
        self.assertEqual(self.index(9, 5), 1)   # right edge

    def test_pixel_deeper_than_radius_is_the_darkest_step(self):
        solid, _ = bands.bands({y: (0, 19) for y in range(20)}, 20, 20)
        self.assertEqual(bands.bevel_index(10, 10, solid, lo=0, hi=6, radius=3), 6)


if __name__ == "__main__":
    unittest.main()
