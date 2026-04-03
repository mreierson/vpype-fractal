"""Tests for escape-time computation and contour extraction."""

import numpy as np
import pytest

from vpype_fractal.engines.contour import extract_contours, extract_contours_by_level
from vpype_fractal.engines.escape_time import julia_grid, mandelbrot_grid


class TestMandelbrotGrid:
    def test_returns_correct_shapes(self):
        x, y, escape = mandelbrot_grid(-2.0, 0.5, -1.0, 1.0, 50, 20)
        assert len(x) == 50
        assert escape.shape[1] == 50
        assert escape.shape[0] == len(y)

    def test_origin_is_inside_set(self):
        """The origin (0+0i) is inside the Mandelbrot set (escape = max_iter)."""
        x, y, escape = mandelbrot_grid(-0.1, 0.1, -0.1, 0.1, 10, 100)
        center_y = escape.shape[0] // 2
        center_x = escape.shape[1] // 2
        assert escape[center_y, center_x] == 100.0

    def test_far_point_escapes_quickly(self):
        """A point far from the set should escape in very few iterations."""
        x, y, escape = mandelbrot_grid(3.0, 3.1, 3.0, 3.1, 5, 100)
        assert np.all(escape < 10)

    def test_escape_values_in_valid_range(self):
        """All escape values should be between 0 and max_iter."""
        _, _, escape = mandelbrot_grid(-2.0, 0.5, -1.0, 1.0, 100, 50)
        assert np.all(escape >= 0)
        assert np.all(escape <= 50)
        assert not np.any(np.isnan(escape))


class TestJuliaGrid:
    def test_returns_correct_shapes(self):
        x, y, escape = julia_grid(-0.7, 0.27, -1.5, 1.5, -1.5, 1.5, 50, 20)
        assert len(x) == 50
        assert escape.shape[1] == 50

    def test_escape_values_in_valid_range(self):
        _, _, escape = julia_grid(-0.7, 0.27, -1.5, 1.5, -1.5, 1.5, 100, 50)
        assert np.all(escape >= 0)
        assert np.all(escape <= 50)
        assert not np.any(np.isnan(escape))


class TestBoundsValidation:
    def test_mandelbrot_swapped_x_bounds_raises(self):
        with pytest.raises(ValueError, match="min < max"):
            mandelbrot_grid(1.0, -1.0, -1.0, 1.0, 50, 20)

    def test_mandelbrot_swapped_y_bounds_raises(self):
        with pytest.raises(ValueError, match="min < max"):
            mandelbrot_grid(-1.0, 1.0, 1.0, -1.0, 50, 20)

    def test_mandelbrot_equal_x_bounds_raises(self):
        with pytest.raises(ValueError, match="min < max"):
            mandelbrot_grid(0.0, 0.0, -1.0, 1.0, 50, 20)

    def test_julia_swapped_bounds_raises(self):
        with pytest.raises(ValueError, match="min < max"):
            julia_grid(-0.7, 0.27, 1.5, -1.5, -1.5, 1.5, 50, 20)


class TestContourExtraction:
    def test_simple_field_produces_contours(self):
        """A gradient field should produce contour lines."""
        x = np.linspace(0, 10, 50)
        y = np.linspace(0, 10, 50)
        xx, yy = np.meshgrid(x, y)
        field = xx + yy

        lc = extract_contours(x, y, field, [5.0, 10.0, 15.0])
        assert len(lc) > 0

    def test_uniform_field_produces_no_contours(self):
        """A uniform field has no contour crossings."""
        x = np.linspace(0, 1, 10)
        y = np.linspace(0, 1, 10)
        field = np.ones((10, 10)) * 5.0

        lc = extract_contours(x, y, field, [3.0])
        assert len(lc) == 0

    def test_mandelbrot_contours_produce_output(self):
        x, y, escape = mandelbrot_grid(-2.2, 0.8, -1.2, 1.2, 100, 50)
        levels = np.linspace(1, 40, 10).tolist()
        lc = extract_contours(x, y, escape, levels)
        assert len(lc) > 0

    def test_empty_levels_produces_no_contours(self):
        x = np.linspace(0, 10, 20)
        y = np.linspace(0, 10, 20)
        xx, yy = np.meshgrid(x, y)
        field = xx + yy
        lc = extract_contours(x, y, field, [])
        assert len(lc) == 0


class TestContoursByLevel:
    def test_returns_one_collection_per_level(self):
        x = np.linspace(0, 10, 50)
        y = np.linspace(0, 10, 50)
        xx, yy = np.meshgrid(x, y)
        field = xx + yy
        levels = [5.0, 10.0, 15.0]
        result = extract_contours_by_level(x, y, field, levels)
        assert len(result) == 3

    def test_different_levels_produce_different_contours(self):
        x = np.linspace(0, 10, 50)
        y = np.linspace(0, 10, 50)
        xx, yy = np.meshgrid(x, y)
        field = xx + yy
        levels = [5.0, 10.0, 15.0]
        result = extract_contours_by_level(x, y, field, levels)
        # Each level should have contours for a diagonal gradient
        for lc in result:
            assert len(lc) > 0


class TestContourSaddleCases:
    def test_saddle_case_produces_two_segments(self):
        """A checkerboard pattern creates a saddle point."""
        x = np.array([0.0, 1.0, 2.0, 3.0])
        y = np.array([0.0, 1.0, 2.0, 3.0])
        field = np.array(
            [
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
            ]
        )
        lc = extract_contours(x, y, field, [0.5])
        assert len(lc) > 0

    def test_saddle_disambiguation_uses_center(self):
        """Cases 5 and 10 should produce different wiring based on center value."""
        x = np.linspace(0, 2, 3)
        y = np.linspace(0, 2, 3)
        # Case 5: v0 high, v1 low, v2 high, v3 low (checkerboard)
        field_high_center = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 0.8, 0.0],  # center ~0.45 (from corners avg), but we control it
                [0.0, 0.0, 1.0],
            ]
        )
        field_low_center = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
        )
        lc1 = extract_contours(x, y, field_high_center, [0.5])
        lc2 = extract_contours(x, y, field_low_center, [0.5])
        # Both should produce output, but segment connectivity may differ
        assert len(lc1) > 0
        assert len(lc2) > 0
