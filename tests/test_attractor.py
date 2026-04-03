"""Tests for the strange attractor engines."""

import numpy as np
import pytest

from vpype_fractal.engines.attractor import (
    ATTRACTOR_PRESETS,
    attractor_to_lines,
    run_clifford,
    run_dejong,
    run_lorenz,
)


class TestRunClifford:
    def test_returns_correct_count(self):
        points = run_clifford(-1.4, 1.6, 1.0, 0.7, 1000, seed=42)
        assert len(points) == 1000

    def test_reproducible_with_seed(self):
        p1 = run_clifford(-1.4, 1.6, 1.0, 0.7, 500, seed=42)
        p2 = run_clifford(-1.4, 1.6, 1.0, 0.7, 500, seed=42)
        np.testing.assert_array_equal(p1, p2)

    def test_different_seeds_differ(self):
        p1 = run_clifford(-1.4, 1.6, 1.0, 0.7, 500, seed=1)
        p2 = run_clifford(-1.4, 1.6, 1.0, 0.7, 500, seed=2)
        assert not np.array_equal(p1, p2)

    def test_points_are_finite(self):
        points = run_clifford(-1.4, 1.6, 1.0, 0.7, 5000, seed=42)
        assert np.all(np.isfinite(points.real))
        assert np.all(np.isfinite(points.imag))


class TestRunDeJong:
    def test_returns_correct_count(self):
        points = run_dejong(1.4, -2.3, 2.4, -2.1, 1000, seed=42)
        assert len(points) == 1000

    def test_reproducible_with_seed(self):
        p1 = run_dejong(1.4, -2.3, 2.4, -2.1, 500, seed=42)
        p2 = run_dejong(1.4, -2.3, 2.4, -2.1, 500, seed=42)
        np.testing.assert_array_equal(p1, p2)

    def test_points_are_finite(self):
        points = run_dejong(1.4, -2.3, 2.4, -2.1, 5000, seed=42)
        assert np.all(np.isfinite(points.real))
        assert np.all(np.isfinite(points.imag))


class TestRunLorenz:
    def test_returns_correct_count(self):
        points = run_lorenz(10.0, 28.0, 8.0 / 3.0, 0.005, 1000, seed=42)
        assert len(points) == 1000

    def test_reproducible_with_seed(self):
        p1 = run_lorenz(10.0, 28.0, 8.0 / 3.0, 0.005, 500, seed=42)
        p2 = run_lorenz(10.0, 28.0, 8.0 / 3.0, 0.005, 500, seed=42)
        np.testing.assert_array_equal(p1, p2)

    def test_points_are_finite(self):
        points = run_lorenz(10.0, 28.0, 8.0 / 3.0, 0.005, 5000, seed=42)
        assert np.all(np.isfinite(points.real))
        assert np.all(np.isfinite(points.imag))

    def test_classic_params_produce_butterfly_shape(self):
        """The classic Lorenz attractor should span a reasonable range in XZ."""
        points = run_lorenz(10.0, 28.0, 8.0 / 3.0, 0.005, 10000, seed=42)
        x_range = points.real.max() - points.real.min()
        z_range = points.imag.max() - points.imag.min()
        # Should not collapse to a point or line
        assert x_range > 10
        assert z_range > 10


class TestAttractorToLines:
    @pytest.mark.parametrize("name", sorted(ATTRACTOR_PRESETS.keys()))
    def test_all_presets_produce_output(self, name):
        preset = ATTRACTOR_PRESETS[name]
        lc = attractor_to_lines(preset.kind, preset.params, 5000, seed=42, segment_length=200)
        assert len(lc) > 0

    def test_segment_length_respected(self):
        lc = attractor_to_lines(
            "clifford",
            {"a": -1.4, "b": 1.6, "c": 1.0, "d": 0.7},
            5000,
            seed=42,
            segment_length=100,
        )
        for line in lc:
            assert len(line) <= 100
