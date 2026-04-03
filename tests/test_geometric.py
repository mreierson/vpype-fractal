"""Tests for the geometric fractal engines."""

import math

from vpype_fractal.engines.geometric import build_carpet, build_sierpinski_triangle, build_tree


class TestBuildTree:
    def test_depth_zero_returns_empty(self):
        lines = build_tree(depth=0, branch_angle=math.radians(25))
        assert lines == []

    def test_depth_one_returns_single_segment(self):
        lines = build_tree(depth=1, branch_angle=math.radians(25))
        assert len(lines) == 1
        assert len(lines[0]) == 2

    def test_depth_two_returns_trunk_plus_two_branches(self):
        lines = build_tree(depth=2, branch_angle=math.radians(25))
        # depth=2: 1 trunk + 2 branches = 3 segments
        assert len(lines) == 3

    def test_segment_count_grows_with_depth(self):
        lines_3 = build_tree(depth=3, branch_angle=math.radians(25))
        lines_5 = build_tree(depth=5, branch_angle=math.radians(25))
        assert len(lines_5) > len(lines_3)

    def test_custom_shrink(self):
        lines = build_tree(depth=3, branch_angle=math.radians(30), shrink=0.5)
        assert len(lines) > 0


class TestBuildCarpet:
    def test_depth_zero_returns_single_square(self):
        lines = build_carpet(depth=0)
        assert len(lines) == 1
        assert len(lines[0]) == 5  # closed square

    def test_depth_one_returns_eight_squares(self):
        lines = build_carpet(depth=1)
        # 3x3 grid minus center = 8 squares
        assert len(lines) == 8

    def test_depth_two_count(self):
        lines = build_carpet(depth=2)
        # 8 sub-squares each with 8 = 64
        assert len(lines) == 64

    def test_squares_are_closed(self):
        lines = build_carpet(depth=1)
        for line in lines:
            assert abs(line[0] - line[-1]) < 1e-10


class TestBuildSierpinskiTriangle:
    def test_depth_zero_returns_single_triangle(self):
        lines = build_sierpinski_triangle(depth=0)
        assert len(lines) == 1
        assert len(lines[0]) == 4  # closed triangle

    def test_depth_one_returns_three_triangles(self):
        lines = build_sierpinski_triangle(depth=1)
        assert len(lines) == 3

    def test_depth_two_count(self):
        lines = build_sierpinski_triangle(depth=2)
        # 3^2 = 9
        assert len(lines) == 9

    def test_triangles_are_closed(self):
        lines = build_sierpinski_triangle(depth=1)
        for line in lines:
            assert abs(line[0] - line[-1]) < 1e-10
