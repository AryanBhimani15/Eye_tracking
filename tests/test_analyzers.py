"""Unit tests for the analyzer helpers in app.py."""

from app import (
    generate_heatmap_grid,
    calculate_attention_metrics,
    identify_hotspots,
    identify_cold_zones,
    generate_gaze_path,
)


def _point(x, y, relative_x=None, relative_y=None, timestamp=0):
    return {
        "x": x,
        "y": y,
        "relative_x": x / 1920 if relative_x is None else relative_x,
        "relative_y": y / 1080 if relative_y is None else relative_y,
        "timestamp": timestamp,
    }


class TestGenerateHeatmapGrid:
    def test_empty_points_returns_zero_grid(self):
        grid = generate_heatmap_grid([], grid_size=10)
        assert len(grid) == 10
        assert all(len(row) == 10 for row in grid)
        assert all(cell == 0 for row in grid for cell in row)

    def test_grid_normalizes_to_one(self):
        points = [_point(960, 540) for _ in range(20)]
        grid = generate_heatmap_grid(points, grid_size=10)
        flat_max = max(max(row) for row in grid)
        assert flat_max == 1.0

    def test_grid_is_centered_on_input(self):
        points = [_point(0, 0, relative_x=0.5, relative_y=0.5) for _ in range(5)]
        grid = generate_heatmap_grid(points, grid_size=10)
        # The peak should be at (5, 5)
        assert grid[5][5] == 1.0

    def test_grid_size_is_respected(self):
        grid = generate_heatmap_grid([_point(100, 100)], grid_size=25)
        assert len(grid) == 25
        assert len(grid[0]) == 25


class TestCalculateAttentionMetrics:
    def test_empty_points_returns_empty_dict(self):
        assert calculate_attention_metrics([]) == {}

    def test_single_point_has_zero_dispersion(self):
        metrics = calculate_attention_metrics([_point(100, 200)])
        assert metrics["dispersion"] == 0
        assert metrics["mean_x"] == 100
        assert metrics["mean_y"] == 200
        assert metrics["scan_path_length"] == 0

    def test_scan_path_length_sums_segments(self):
        # Three points forming a 3-4-5 triangle leg: (0,0) -> (3,0) -> (3,4)
        points = [_point(0, 0), _point(3, 0), _point(3, 4)]
        metrics = calculate_attention_metrics(points)
        assert metrics["scan_path_length"] == 7.0

    def test_dispersion_is_nonzero_for_spread_points(self):
        points = [_point(0, 0), _point(1000, 1000)]
        metrics = calculate_attention_metrics(points)
        assert metrics["dispersion"] > 0

    def test_efficiency_is_path_per_point(self):
        points = [_point(0, 0), _point(10, 0)]
        metrics = calculate_attention_metrics(points)
        assert metrics["scan_path_efficiency"] == 5.0  # 10 / 2 points


class TestIdentifyHotspots:
    def test_empty_grid_returns_no_hotspots(self):
        grid = [[0 for _ in range(10)] for _ in range(10)]
        assert identify_hotspots(grid) == []

    def test_hotspots_above_threshold(self):
        grid = [[0 for _ in range(10)] for _ in range(10)]
        grid[3][4] = 0.9
        grid[7][1] = 0.85
        grid[0][0] = 0.5  # below default threshold of 0.8
        hotspots = identify_hotspots(grid)
        assert len(hotspots) == 2
        # Top-ranked should be the higher intensity one
        assert hotspots[0]["intensity"] == 0.9

    def test_hotspots_capped_at_ten(self):
        grid = [[0.95 for _ in range(20)] for _ in range(20)]
        hotspots = identify_hotspots(grid)
        assert len(hotspots) == 10


class TestIdentifyColdZones:
    def test_uniform_cold_grid_yields_one_big_zone(self):
        grid = [[0.0 for _ in range(10)] for _ in range(10)]
        cold = identify_cold_zones(grid)
        assert len(cold) == 1
        assert cold[0]["size"] == 100

    def test_small_regions_filtered_out(self):
        # Create a grid where everything is hot except a few isolated cells
        grid = [[1.0 for _ in range(10)] for _ in range(10)]
        grid[0][0] = 0.0  # 1-cell region, should be filtered
        cold = identify_cold_zones(grid)
        assert cold == []

    def test_cold_zones_capped_at_five(self):
        grid = [[0.0 for _ in range(50)] for _ in range(50)]
        cold = identify_cold_zones(grid)
        assert len(cold) <= 5


class TestGenerateGazePath:
    def test_too_few_points_returns_empty(self):
        assert generate_gaze_path([]) == []
        assert generate_gaze_path([_point(0, 0)]) == []

    def test_path_is_downsampled(self):
        points = [_point(i, i) for i in range(500)]
        path = generate_gaze_path(points)
        # Sampling rate is len // 50, so we get ~50 points back
        assert len(path) <= 60

    def test_path_preserves_relative_coords(self):
        points = [_point(0, 0, relative_x=0.25, relative_y=0.75) for _ in range(2)]
        path = generate_gaze_path(points)
        assert path[0]["x"] == 0.25
        assert path[0]["y"] == 0.75
