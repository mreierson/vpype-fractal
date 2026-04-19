"""Tests for region detection, auto-depth calculation, and mask clipping."""

import numpy as np
import pytest
import vpype as vp

from vpype_fractal._region import RegionContext, auto_depth, get_region_context
from vpype_fractal.commands._shared import clip_lines_to_mask

# ---------------------------------------------------------------------------
# auto_depth
# ---------------------------------------------------------------------------


class TestAutoDepth:
    """Test auto_depth() for all three curve types."""

    def test_hilbert_basic(self):
        # 100 units / 1 unit pitch -> ratio 100, log2(100) ~ 6
        depth = auto_depth(100.0, 100.0, 1.0, "hilbert")
        assert depth == 6

    def test_hilbert_coarse_pitch(self):
        # 100 / 10 = 10, log2(10) ~ 3
        depth = auto_depth(100.0, 100.0, 10.0, "hilbert")
        assert depth == 3

    def test_hilbert_clamps_to_10(self):
        # Very fine pitch should clamp at 10
        depth = auto_depth(10000.0, 10000.0, 0.01, "hilbert")
        assert depth == 10

    def test_hilbert_clamps_to_1(self):
        # Very coarse pitch should clamp at 1
        depth = auto_depth(10.0, 10.0, 100.0, "hilbert")
        assert depth == 1

    def test_gosper_basic(self):
        # ratio 100, log(100)/log(sqrt(7)) ~ 4.7 -> 4
        depth = auto_depth(100.0, 100.0, 1.0, "gosper")
        assert depth == 4

    def test_gosper_clamps_to_10(self):
        depth = auto_depth(100000.0, 100000.0, 0.001, "gosper")
        assert depth == 10

    def test_peano_basic(self):
        # ratio 100, log(100)/log(3) ~ 4.2 -> 4
        depth = auto_depth(100.0, 100.0, 1.0, "peano")
        assert depth == 4

    def test_peano_clamps_to_8(self):
        depth = auto_depth(100000.0, 100000.0, 0.001, "peano")
        assert depth == 8

    def test_peano_clamps_to_1(self):
        depth = auto_depth(5.0, 5.0, 100.0, "peano")
        assert depth == 1

    def test_unknown_curve_type_raises(self):
        with pytest.raises(ValueError, match="Unknown curve type"):
            auto_depth(100.0, 100.0, 1.0, "unknown")

    def test_zero_extent_returns_1(self):
        assert auto_depth(0.0, 100.0, 1.0, "hilbert") == 1

    def test_zero_pitch_returns_1(self):
        assert auto_depth(100.0, 100.0, 0.0, "hilbert") == 1

    def test_uses_min_dimension(self):
        # Rectangle: min(50, 200) = 50, 50 / 1 = 50, log2(50) ~ 5
        depth = auto_depth(50.0, 200.0, 1.0, "hilbert")
        assert depth == 5


# ---------------------------------------------------------------------------
# get_region_context
# ---------------------------------------------------------------------------


class TestGetRegionContext:
    """Test get_region_context() detection logic."""

    def test_empty_document_no_page_returns_none(self):
        doc = vp.Document()
        result = get_region_context(doc)
        assert result is None

    def test_document_with_page_size(self):
        doc = vp.Document()
        doc.page_size = (200.0, 300.0)
        ctx = get_region_context(doc)
        assert ctx is not None
        assert ctx.bounds == (0.0, 0.0, 200.0, 300.0)
        assert ctx.width == 200.0
        assert ctx.height == 300.0
        assert ctx.mask is None
        assert ctx.is_region is False

    def test_document_with_existing_geometry(self):
        doc = vp.Document()
        lc = vp.LineCollection()
        lc.append(np.array([10 + 20j, 110 + 120j]))
        doc.add(lc, 1)
        ctx = get_region_context(doc)
        assert ctx is not None
        assert ctx.is_region is False
        # Bounds should cover the line's extent
        assert ctx.bounds[0] == pytest.approx(10.0)
        assert ctx.bounds[1] == pytest.approx(20.0)
        assert ctx.bounds[2] == pytest.approx(110.0)
        assert ctx.bounds[3] == pytest.approx(120.0)

    def test_forregion_metadata_detected(self):
        """Simulate a vpype-raster forregion block via metadata injection."""
        doc = vp.Document()

        class FakeRegion:
            bounds = (50.0, 100.0, 200.0, 150.0)
            mask = np.ones((150, 200), dtype=bool)

        doc.metadata["vpype_raster.current_region"] = FakeRegion()
        ctx = get_region_context(doc)
        assert ctx is not None
        assert ctx.is_region is True
        assert ctx.bounds == (50.0, 100.0, 250.0, 250.0)
        assert ctx.mask is not None
        assert ctx.width == 200.0
        assert ctx.height == 150.0


# ---------------------------------------------------------------------------
# clip_lines_to_mask
# ---------------------------------------------------------------------------


class TestClipLinesToMask:
    """Test clip_lines_to_mask() clipping behavior."""

    def test_fully_inside_mask(self):
        """A line entirely inside the mask should pass through."""
        mask = np.ones((100, 100), dtype=bool)
        bounds = (0.0, 0.0, 100.0, 100.0)
        lc = vp.LineCollection()
        lc.append(np.array([10 + 10j, 50 + 50j, 90 + 90j]))
        result = clip_lines_to_mask(lc, mask, bounds)
        assert len(result) == 1
        assert len(result[0]) == 3

    def test_fully_outside_mask(self):
        """A line entirely outside the mask should be removed."""
        mask = np.zeros((100, 100), dtype=bool)
        bounds = (0.0, 0.0, 100.0, 100.0)
        lc = vp.LineCollection()
        lc.append(np.array([10 + 10j, 50 + 50j, 90 + 90j]))
        result = clip_lines_to_mask(lc, mask, bounds)
        assert len(result) == 0

    def test_partially_inside_mask(self):
        """A line crossing the mask boundary should be split."""
        mask = np.zeros((100, 100), dtype=bool)
        # Only left half is inside
        mask[:, :50] = True
        bounds = (0.0, 0.0, 100.0, 100.0)
        lc = vp.LineCollection()
        # Line goes from left (inside) to right (outside)
        pts = np.array([10 + 50j, 20 + 50j, 30 + 50j, 40 + 50j, 60 + 50j, 70 + 50j, 80 + 50j])
        lc.append(pts)
        result = clip_lines_to_mask(lc, mask, bounds)
        # Should have at least one segment from the inside portion
        assert len(result) >= 1
        # All points in result should be in the left half
        for line in result:
            assert np.all(line.real < 51)

    def test_empty_input(self):
        """Empty input should produce empty output."""
        mask = np.ones((100, 100), dtype=bool)
        bounds = (0.0, 0.0, 100.0, 100.0)
        lc = vp.LineCollection()
        result = clip_lines_to_mask(lc, mask, bounds)
        assert len(result) == 0

    def test_circular_mask(self):
        """A circular mask should clip a horizontal line to the circle interior."""
        mask = np.zeros((100, 100), dtype=bool)
        # Create a circular mask centered at (50, 50) with radius 30
        yy, xx = np.mgrid[0:100, 0:100]
        mask[(xx - 50) ** 2 + (yy - 50) ** 2 <= 30**2] = True

        bounds = (0.0, 0.0, 100.0, 100.0)
        lc = vp.LineCollection()
        # Horizontal line through the center
        pts = np.array([complex(x, 50) for x in range(0, 100, 2)])
        lc.append(pts)
        result = clip_lines_to_mask(lc, mask, bounds)
        assert len(result) >= 1
        # Result should be shorter than input
        total_pts = sum(len(line) for line in result)
        assert total_pts < len(pts)

    def test_multiple_lines(self):
        """Multiple input lines should be processed independently."""
        mask = np.ones((100, 100), dtype=bool)
        mask[:, 45:55] = False  # Vertical stripe removed
        bounds = (0.0, 0.0, 100.0, 100.0)
        lc = vp.LineCollection()
        for y_pos in [20, 50, 80]:
            pts = np.array([complex(x, y_pos) for x in range(0, 100, 2)])
            lc.append(pts)
        result = clip_lines_to_mask(lc, mask, bounds)
        # Each input line should be split into 2 segments (left + right of gap)
        assert len(result) >= 3


# ---------------------------------------------------------------------------
# Integration: auto_depth with region context
# ---------------------------------------------------------------------------


class TestRegionIntegration:
    """Test that auto_depth works correctly with RegionContext dimensions."""

    @pytest.mark.parametrize(
        "curve_type,expected_min",
        [
            ("hilbert", 1),
            ("gosper", 1),
            ("peano", 1),
        ],
    )
    def test_auto_depth_from_region_context(self, curve_type: str, expected_min: int):
        """auto_depth should produce valid depths from region dimensions."""
        ctx = RegionContext(
            bounds=(0.0, 0.0, 500.0, 500.0),
            mask=None,
            width=500.0,
            height=500.0,
            is_region=True,
        )
        depth = auto_depth(ctx.width, ctx.height, 2.0, curve_type)
        assert depth >= expected_min
        assert depth <= 10

    @pytest.mark.parametrize("curve_type", ["hilbert", "gosper", "peano"])
    def test_finer_pitch_gives_deeper_depth(self, curve_type: str):
        """Finer pitch should produce equal or deeper recursion."""
        d_coarse = auto_depth(500.0, 500.0, 10.0, curve_type)
        d_fine = auto_depth(500.0, 500.0, 1.0, curve_type)
        assert d_fine >= d_coarse
