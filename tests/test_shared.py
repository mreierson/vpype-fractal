"""Tests for shared utilities."""

import numpy as np
import vpype as vp

from vpype_fractal.commands._shared import scale_all_to_size, scale_to_size


class TestScaleToSize:
    def test_scales_to_target_size(self):
        lc = vp.LineCollection()
        lc.append(np.array([0 + 0j, 10 + 0j, 10 + 5j]))
        result = scale_to_size(lc, 100.0)
        bounds = result.bounds()
        assert bounds is not None
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        assert abs(max(width, height) - 100.0) < 1e-6

    def test_empty_collection_unchanged(self):
        lc = vp.LineCollection()
        result = scale_to_size(lc, 100.0)
        assert len(result) == 0

    def test_origin_placement(self):
        """Scaled output should have bounding box starting at origin."""
        lc = vp.LineCollection()
        lc.append(np.array([5 + 5j, 15 + 10j]))
        result = scale_to_size(lc, 50.0)
        bounds = result.bounds()
        assert bounds is not None
        assert abs(bounds[0]) < 1e-6
        assert abs(bounds[1]) < 1e-6

    def test_single_point_unchanged(self):
        """A single point has max_dim=0, should return unchanged."""
        lc = vp.LineCollection()
        lc.append(np.array([5 + 5j, 5 + 5j]))
        result = scale_to_size(lc, 100.0)
        assert len(result) == 1


class TestScaleAllToSize:
    def test_scales_multiple_collections_uniformly(self):
        lc1 = vp.LineCollection()
        lc1.append(np.array([0 + 0j, 5 + 0j]))
        lc2 = vp.LineCollection()
        lc2.append(np.array([0 + 0j, 0 + 10j]))
        result = scale_all_to_size([lc1, lc2], 200.0)
        assert len(result) == 2
        # The larger dimension (10) should scale to 200
        b2 = result[1].bounds()
        assert b2 is not None
        height = b2[3] - b2[1]
        assert abs(height - 200.0) < 1e-6
        # The smaller dimension should scale proportionally
        b1 = result[0].bounds()
        assert b1 is not None
        width = b1[2] - b1[0]
        assert abs(width - 100.0) < 1e-6

    def test_empty_collections(self):
        result = scale_all_to_size([vp.LineCollection(), vp.LineCollection()], 100.0)
        assert len(result) == 2
