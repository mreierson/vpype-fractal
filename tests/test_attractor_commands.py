"""Integration tests for strange attractor CLI commands."""

import vpype_cli


class TestCliffordCommand:
    def test_default_produces_output(self):
        doc = vpype_cli.execute("clifford -p 1000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0

    def test_custom_params(self):
        doc = vpype_cli.execute("clifford -a 1.7 -b 1.7 -c 0.6 -d 1.2 -p 1000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0

    def test_with_size(self):
        doc = vpype_cli.execute("clifford -p 1000 --seed 42 -s 80mm")
        assert doc is not None
        bounds = doc.bounds()
        assert bounds is not None
        dim = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
        expected = 80.0 * 96 / 25.4
        assert abs(dim - expected) / expected < 0.01

    def test_multi_layer(self):
        doc = vpype_cli.execute("clifford -p 3000 --seed 42 -n 4")
        assert doc is not None
        assert len(doc.layers) == 4

    def test_with_colorize(self):
        doc = vpype_cli.execute("penset warm clifford -p 3000 --seed 42 -n 4 colorize")
        assert doc is not None
        assert len(doc.layers) == 4
        for lid in doc.layers:
            assert doc[lid].property("vp_color") is not None


class TestDeJongCommand:
    def test_default_produces_output(self):
        doc = vpype_cli.execute("dejong -p 1000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0

    def test_custom_params(self):
        doc = vpype_cli.execute("dejong -a -2.7 -b -0.09 -c -0.86 -d -2.2 -p 1000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0


class TestGenericAttractorCommand:
    def test_clifford_preset(self):
        doc = vpype_cli.execute("attractor --preset butterfly -p 1000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0

    def test_dejong_preset(self):
        doc = vpype_cli.execute("attractor --preset wings -p 1000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0

    def test_lorenz_preset(self):
        doc = vpype_cli.execute("attractor --preset lorenz-classic -p 1000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0

    def test_multi_layer(self):
        doc = vpype_cli.execute("attractor --preset ribbon -p 1000 --seed 42 -n 4")
        assert doc is not None
        assert len(doc.layers) == 4


class TestLorenzCommand:
    def test_default_produces_output(self):
        doc = vpype_cli.execute("lorenz -p 5000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) > 0

    def test_custom_params(self):
        doc = vpype_cli.execute("lorenz --rho 15 -p 5000 --seed 42")
        assert doc is not None
        assert len(doc.layers) > 0

    def test_multi_layer(self):
        doc = vpype_cli.execute("lorenz -p 5000 --seed 42 -n 8")
        assert doc is not None
        assert len(doc.layers) == 8

    def test_single_layer_is_continuous(self):
        doc = vpype_cli.execute("lorenz -p 3000 --seed 42 -n 1")
        lc = doc.layers[list(doc.layers)[0]]
        assert len(lc) == 1
