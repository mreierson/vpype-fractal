"""Tests for the IFS engine."""

import numpy as np
import pytest

from vpype_fractal.engines.ifs import IFS_PRESETS, AffineTransform, ifs_to_lines, run_ifs


class TestRunIfs:
    def test_returns_correct_number_of_points(self):
        transforms = IFS_PRESETS["fern"].transforms
        points = run_ifs(transforms, 1000, seed=42)
        assert len(points) == 1000

    def test_reproducible_with_seed(self):
        transforms = IFS_PRESETS["fern"].transforms
        p1 = run_ifs(transforms, 500, seed=123)
        p2 = run_ifs(transforms, 500, seed=123)
        np.testing.assert_array_equal(p1, p2)

    def test_different_seeds_differ(self):
        transforms = IFS_PRESETS["fern"].transforms
        p1 = run_ifs(transforms, 500, seed=1)
        p2 = run_ifs(transforms, 500, seed=2)
        assert not np.array_equal(p1, p2)

    def test_single_transform(self):
        t = AffineTransform(a=0.5, b=0.0, c=0.0, d=0.5, e=0.0, f=0.0, weight=1.0)
        points = run_ifs([t], 100, seed=42)
        assert len(points) == 100

    def test_weight_normalization(self):
        """Transforms with unnormalized weights should still work."""
        transforms = [
            AffineTransform(a=0.5, b=0.0, c=0.0, d=0.5, e=0.0, f=0.0, weight=10.0),
            AffineTransform(a=0.5, b=0.0, c=0.0, d=0.5, e=1.0, f=0.0, weight=30.0),
        ]
        points = run_ifs(transforms, 500, seed=42)
        assert len(points) == 500


class TestRunIfsValidation:
    def test_zero_weights_raises(self):
        transforms = [
            AffineTransform(a=0.5, b=0.0, c=0.0, d=0.5, e=0.0, f=0.0, weight=0.0),
            AffineTransform(a=0.5, b=0.0, c=0.0, d=0.5, e=1.0, f=0.0, weight=0.0),
        ]
        with pytest.raises(ValueError, match="[Ww]eight"):
            run_ifs(transforms, 100, seed=42)

    def test_negative_weight_raises(self):
        transforms = [
            AffineTransform(a=0.5, b=0.0, c=0.0, d=0.5, e=0.0, f=0.0, weight=-1.0),
            AffineTransform(a=0.5, b=0.0, c=0.0, d=0.5, e=1.0, f=0.0, weight=2.0),
        ]
        with pytest.raises(ValueError, match="[Ww]eight"):
            run_ifs(transforms, 100, seed=42)


class TestIfsToLines:
    def test_produces_line_collection(self):
        transforms = IFS_PRESETS["fern"].transforms
        lc = ifs_to_lines(transforms, 1000, seed=42, segment_length=100)
        assert len(lc) > 0

    def test_segment_length_limits_path_length(self):
        transforms = IFS_PRESETS["fern"].transforms
        lc = ifs_to_lines(transforms, 1000, seed=42, segment_length=200)
        for line in lc:
            assert len(line) <= 200

    @pytest.mark.parametrize("name", sorted(IFS_PRESETS.keys()))
    def test_all_presets_produce_output(self, name):
        ifs_def = IFS_PRESETS[name]
        lc = ifs_to_lines(ifs_def.transforms, 500, seed=42)
        assert len(lc) > 0

    def test_very_few_points_returns_empty(self):
        """With only 1 point, can't form a line segment."""
        transforms = IFS_PRESETS["fern"].transforms
        lc = ifs_to_lines(transforms, 1, seed=42)
        assert len(lc) == 0
