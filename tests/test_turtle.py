"""Tests for the turtle graphics interpreter."""

from vpype_fractal.engines.turtle import turtle_to_lines


class TestTurtleBasics:
    def test_single_forward_produces_one_line(self):
        lc = turtle_to_lines("F", angle=90.0)
        assert len(lc) == 1
        assert len(lc[0]) == 2

    def test_forward_moves_right_by_default(self):
        lc = turtle_to_lines("F", angle=90.0, step=10.0)
        line = lc[0]
        # Start at origin, move right
        assert abs(line[0] - (0 + 0j)) < 1e-10
        assert abs(line[1] - (10 + 0j)) < 1e-10

    def test_two_forwards_extend_path(self):
        lc = turtle_to_lines("FF", angle=90.0, step=5.0)
        assert len(lc) == 1
        assert len(lc[0]) == 3

    def test_turn_left_then_forward(self):
        lc = turtle_to_lines("F+F", angle=90.0, step=10.0)
        assert len(lc) == 1
        line = lc[0]
        # After turning left 90 degrees, second segment goes up
        assert abs(line[2].real - 10.0) < 1e-10
        assert abs(line[2].imag - 10.0) < 1e-10

    def test_turn_right_then_forward(self):
        lc = turtle_to_lines("F-F", angle=90.0, step=10.0)
        assert len(lc) == 1
        line = lc[0]
        # After turning right 90 degrees, second segment goes down
        assert abs(line[2].real - 10.0) < 1e-10
        assert abs(line[2].imag - (-10.0)) < 1e-10


class TestTurtleBranching:
    def test_push_pop_restores_position(self):
        lc = turtle_to_lines("F[+F]F", angle=90.0, step=10.0)
        # Should produce 2 paths: F...F (main) and the branch +F
        assert len(lc) >= 2

    def test_empty_string_produces_no_lines(self):
        lc = turtle_to_lines("", angle=90.0)
        assert len(lc) == 0

    def test_pen_up_move_creates_new_path(self):
        lc = turtle_to_lines("FfF", angle=90.0, step=10.0)
        assert len(lc) == 2


class TestTurtleDrawChars:
    def test_a_and_b_draw(self):
        lc = turtle_to_lines("AB", angle=60.0, step=1.0)
        assert len(lc) == 1
        assert len(lc[0]) == 3

    def test_custom_heading(self):
        lc = turtle_to_lines("F", angle=90.0, step=10.0, heading=90.0)
        line = lc[0]
        # heading=90 means moving up (positive y)
        assert abs(line[1].real - 0.0) < 1e-10
        assert abs(line[1].imag - 10.0) < 1e-10


class TestTurtleKoch:
    def test_koch_iteration_0_produces_triangle(self):
        """Koch axiom F--F--F at depth 0 should produce an equilateral triangle."""
        lc = turtle_to_lines("F--F--F", angle=60.0, step=1.0)
        assert len(lc) == 1
        line = lc[0]
        assert len(line) == 4  # 3 segments + start = 4 points
        # Should approximately close (return near start)
        assert abs(line[-1] - line[0]) < 1e-10
