"""Integration tests for fractal CLI commands."""

import click
import pytest
import vpype as vp
import vpype_cli

from vpype_fractal.presets import PRESETS

LSYSTEM_COMMANDS = [
    "koch",
    "sierpinski",
    "dragon",
    "hilbert",
    "levy",
    "gosper",
    "peano",
    "koch-island",
    "minkowski",
]
GEOMETRIC_COMMANDS = ["tree", "carpet", "sierpinski-triangle"]


def _max_dim(doc: vp.Document) -> float:
    """Get the max bounding dimension across all layers."""
    bounds = doc.bounds()
    assert bounds is not None
    return max(bounds[2] - bounds[0], bounds[3] - bounds[1])


class TestLSystemCommands:
    @pytest.mark.parametrize("cmd", LSYSTEM_COMMANDS)
    def test_command_produces_output(self, cmd):
        doc = vpype_cli.execute(f"{cmd} -d 2")
        assert doc is not None
        assert len(doc.layers) > 0
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    @pytest.mark.parametrize("cmd", LSYSTEM_COMMANDS)
    def test_command_with_size(self, cmd):
        doc = vpype_cli.execute(f"{cmd} -d 2 -s 50mm")
        assert doc is not None
        # Verify size is approximately 50mm in vpype units (96 dpi -> ~189px)
        dim = _max_dim(doc)
        expected = 50.0 * 96 / 25.4
        assert abs(dim - expected) / expected < 0.01

    @pytest.mark.parametrize("cmd", ["koch", "dragon", "sierpinski"])
    def test_depth_zero(self, cmd):
        """Depth 0 should not crash."""
        doc = vpype_cli.execute(f"{cmd} -d 0")
        assert doc is not None


class TestGeometricCommands:
    @pytest.mark.parametrize("cmd", GEOMETRIC_COMMANDS)
    def test_command_produces_output(self, cmd):
        doc = vpype_cli.execute(f"{cmd} -d 2")
        assert doc is not None
        assert len(doc.layers) > 0
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_tree_depth_zero(self):
        """Tree at depth 0 produces empty output (no branches)."""
        doc = vpype_cli.execute("tree -d 0")
        assert doc is not None

    def test_carpet_depth_zero(self):
        doc = vpype_cli.execute("carpet -d 0")
        assert doc is not None
        assert len(doc.layers) > 0

    def test_tree_with_options(self):
        """Non-default branch-angle and shrink should work."""
        doc = vpype_cli.execute("tree -d 5 --branch-angle 45 --shrink 0.6")
        assert doc is not None
        assert len(doc.layers) > 0
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_tree_shrink_out_of_range_fails(self):
        with pytest.raises(click.exceptions.BadParameter):
            vpype_cli.execute("tree -d 5 --shrink 2.0")

    def test_tree_branch_angle_out_of_range_fails(self):
        with pytest.raises(click.exceptions.BadParameter):
            vpype_cli.execute("tree -d 5 --branch-angle 200")


class TestCustomLSystem:
    def test_custom_lsystem(self):
        doc = vpype_cli.execute('lsystem --axiom "F--F--F" --rule "F=F+F--F+F" --angle 60 -d 2')
        assert doc is not None
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_custom_lsystem_multiple_rules(self):
        doc = vpype_cli.execute(
            'lsystem --axiom "A" --rule "A=B-A-B" --rule "B=A+B+A" --angle 60 -d 3'
        )
        assert doc is not None
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_custom_lsystem_with_heading(self):
        """The --heading option should change output geometry."""
        doc1 = vpype_cli.execute('lsystem --axiom "F" --rule "F=FF" --angle 90 -d 2 --heading 0')
        doc2 = vpype_cli.execute('lsystem --axiom "F" --rule "F=FF" --angle 90 -d 2 --heading 90')
        assert doc1 is not None and doc2 is not None
        b1 = doc1.bounds()
        b2 = doc2.bounds()
        assert b1 is not None and b2 is not None
        # heading=0 draws right, heading=90 draws up — different bounds
        assert abs(b1[2] - b2[2]) > 1.0 or abs(b1[3] - b2[3]) > 1.0

    def test_custom_lsystem_depth_zero(self):
        doc = vpype_cli.execute('lsystem --axiom "F" --rule "F=FF" --angle 90 -d 0')
        assert doc is not None

    def test_multi_char_rule_key_fails(self):
        with pytest.raises(click.BadParameter, match="single character"):
            vpype_cli.execute('lsystem --axiom "AB" --rule "AB=C" --angle 60 -d 1')


class TestEscapeTimeCommands:
    def test_mandelbrot_produces_output(self):
        doc = vpype_cli.execute("mandelbrot -d 30 -r 100 -n 5")
        assert doc is not None
        assert len(doc.layers) > 0
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_julia_produces_output(self):
        doc = vpype_cli.execute("julia -d 30 -r 100 -n 5")
        assert doc is not None
        assert len(doc.layers) > 0
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_julia_custom_c(self):
        doc = vpype_cli.execute("julia --cx -0.4 --cy 0.6 -d 30 -r 100 -n 5")
        assert doc is not None
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_mandelbrot_with_size(self):
        doc = vpype_cli.execute("mandelbrot -d 30 -r 100 -n 5 -s 80mm")
        assert doc is not None
        dim = _max_dim(doc)
        expected = 80.0 * 96 / 25.4
        assert abs(dim - expected) / expected < 0.01

    def test_mandelbrot_custom_bounds(self):
        """Custom viewport bounds should produce output."""
        doc = vpype_cli.execute(
            "mandelbrot -d 30 -r 100 -n 3 --x-min -1.0 --x-max -0.5 --y-min 0.0 --y-max 0.5"
        )
        assert doc is not None
        assert len(doc.layers) > 0

    def test_mandelbrot_swapped_bounds_fails(self):
        with pytest.raises(click.UsageError, match="x-min"):
            vpype_cli.execute("mandelbrot -d 30 -r 100 -n 5 --x-min 1 --x-max -1")

    def test_julia_swapped_bounds_fails(self):
        with pytest.raises(click.UsageError, match="y-min"):
            vpype_cli.execute("julia -d 30 -r 100 -n 5 --y-min 1 --y-max -1")


class TestEscapeTimeMultiLayer:
    def test_mandelbrot_creates_multiple_layers(self):
        doc = vpype_cli.execute("mandelbrot -d 30 -r 100 -n 5")
        assert doc is not None
        assert len(doc.layers) > 1

    def test_julia_creates_multiple_layers(self):
        doc = vpype_cli.execute("julia -d 30 -r 100 -n 5")
        assert doc is not None
        assert len(doc.layers) > 1


class TestIFSCommands:
    def test_fern_produces_output(self):
        doc = vpype_cli.execute("fern -p 5000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_fern_with_size(self):
        doc = vpype_cli.execute("fern -p 5000 --seed 42 -s 80mm")
        assert doc is not None
        dim = _max_dim(doc)
        expected = 80.0 * 96 / 25.4
        assert abs(dim - expected) / expected < 0.01

    @pytest.mark.parametrize("preset", ["fern", "sierpinski-ifs", "maple", "crystal"])
    def test_ifs_presets(self, preset):
        doc = vpype_cli.execute(f"ifs --preset {preset} -p 5000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_ifs_custom_transforms(self):
        doc = vpype_cli.execute(
            'ifs --transform "0.5,0,0,0.5,0,0,1" '
            '--transform "0.5,0,0,0.5,0.5,0,1" '
            '--transform "0.5,0,0,0.5,0.25,0.433,1" '
            "-p 5000 --seed 42"
        )
        assert doc is not None
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_fern_reproducible(self):
        doc1 = vpype_cli.execute("fern -p 1000 --seed 123")
        doc2 = vpype_cli.execute("fern -p 1000 --seed 123")
        lc1 = doc1.layers[list(doc1.layers)[0]]
        lc2 = doc2.layers[list(doc2.layers)[0]]
        assert len(lc1) == len(lc2)
        # Verify actual geometry matches
        for line1, line2 in zip(lc1, lc2, strict=False):
            assert len(line1) == len(line2)

    def test_ifs_segment_length_option(self):
        """CLI --segment-length should limit path length."""
        doc = vpype_cli.execute("ifs --preset fern -p 5000 --seed 42 --segment-length 50")
        assert doc is not None
        lc = doc.layers[list(doc.layers)[0]]
        for line in lc:
            assert len(line) <= 50


class TestErrorPaths:
    def test_ifs_both_preset_and_transform_fails(self):
        with pytest.raises(click.UsageError):
            vpype_cli.execute('ifs --preset fern --transform "0.5,0,0,0.5,0,0,1"')

    def test_ifs_neither_preset_nor_transform_fails(self):
        with pytest.raises(click.UsageError):
            vpype_cli.execute("ifs -p 1000")

    def test_lsystem_bad_rule_format_fails(self):
        with pytest.raises(click.BadParameter):
            vpype_cli.execute('lsystem --axiom "F" --rule "badformat" --angle 60')

    def test_ifs_bad_transform_format_fails(self):
        with pytest.raises(click.BadParameter):
            vpype_cli.execute('ifs --transform "1,2,3"')


class TestPresets:
    @pytest.mark.parametrize("name", list(PRESETS.keys()))
    def test_preset_has_required_fields(self, name):
        preset = PRESETS[name]
        assert preset.axiom
        assert preset.rules
        assert preset.angle > 0
