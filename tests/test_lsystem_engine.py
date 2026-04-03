"""Tests for the L-system expansion engine."""

import pytest

from vpype_fractal.engines.lsystem import expand


class TestExpand:
    def test_zero_iterations_returns_axiom(self):
        assert expand("F", {"F": "F+F"}, 0) == "F"

    def test_single_iteration(self):
        result = expand("F", {"F": "F+F"}, 1)
        assert result == "F+F"

    def test_two_iterations(self):
        result = expand("F", {"F": "F+F"}, 2)
        assert result == "F+F+F+F"

    def test_characters_without_rules_preserved(self):
        result = expand("F+G", {"F": "FF"}, 1)
        assert result == "FF+G"

    def test_multiple_rules(self):
        result = expand("AB", {"A": "AB", "B": "A"}, 1)
        assert result == "ABA"

    def test_multiple_rules_two_iterations(self):
        result = expand("AB", {"A": "AB", "B": "A"}, 2)
        assert result == "ABAAB"

    def test_koch_first_iteration(self):
        result = expand("F", {"F": "F+F--F+F"}, 1)
        assert result == "F+F--F+F"

    def test_empty_axiom(self):
        assert expand("", {"F": "FF"}, 5) == ""

    def test_no_matching_rules(self):
        assert expand("XYZ", {"A": "B"}, 3) == "XYZ"


class TestExpandSafetyLimit:
    def test_exceeds_limit_raises(self):
        """Exponential growth should be caught before OOM."""
        with pytest.raises(ValueError, match="exceeded"):
            # F -> 10 Fs means 10^7 = 10M chars at depth 7
            expand("F", {"F": "FFFFFFFFFF"}, 8)

    def test_moderate_depth_ok(self):
        """Normal usage should not trigger the limit."""
        result = expand("F", {"F": "F+F--F+F"}, 4)
        assert len(result) > 0
