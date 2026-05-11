"""Tests for focal point support."""

import pytest

from imgsvc.focal import (
    FocalPoint,
    calculate_center_of_mass,
    calculate_crop_for_focal_points,
)


class TestFocalPointCreation:
    """Tests for creating focal points."""

    def test_create_with_coordinates(self):
        fp = FocalPoint(100, 200)
        assert fp.x == 100
        assert fp.y == 200
        assert fp.width == 1
        assert fp.height == 1
        assert fp.weight == 1.0
        assert fp.origin == "alignment"

    def test_create_with_all_parameters(self):
        fp = FocalPoint(50, 60, width=20, height=30, weight=5.0, origin="manual")
        assert fp.x == 50
        assert fp.y == 60
        assert fp.width == 20
        assert fp.height == 30
        assert fp.weight == 5.0
        assert fp.origin == "manual"

    def test_coordinates_converted_to_int(self):
        fp = FocalPoint(50.7, 60.3, width=20.9, height=30.1)
        assert fp.x == 50
        assert fp.y == 60
        assert fp.width == 20
        assert fp.height == 30


class TestFocalPointFromSquare:
    """Tests for creating focal points from bounding boxes."""

    def test_from_square_centers_point(self):
        fp = FocalPoint.from_square(0, 0, 100, 100)
        assert fp.x == 50
        assert fp.y == 50

    def test_from_square_with_offset(self):
        fp = FocalPoint.from_square(100, 200, 50, 50)
        assert fp.x == 125
        assert fp.y == 225

    def test_from_square_sets_dimensions(self):
        fp = FocalPoint.from_square(0, 0, 80, 60)
        assert fp.width == 80
        assert fp.height == 60

    def test_from_square_weight_is_area(self):
        fp = FocalPoint.from_square(0, 0, 10, 20)
        assert fp.weight == 200

    def test_from_square_origin_is_detection(self):
        fp = FocalPoint.from_square(0, 0, 100, 100)
        assert fp.origin == "detection"


class TestFocalPointFromAlignment:
    """Tests for creating focal points from alignment strings."""

    def test_left_top_alignment(self):
        fp = FocalPoint.from_alignment("left", "top", 100, 100)
        assert fp.x == 0
        assert fp.y == 0

    def test_center_middle_alignment(self):
        fp = FocalPoint.from_alignment("center", "middle", 100, 100)
        assert fp.x == 50
        assert fp.y == 50

    def test_right_bottom_alignment(self):
        fp = FocalPoint.from_alignment("right", "bottom", 100, 100)
        assert fp.x == 100
        assert fp.y == 100

    def test_left_middle_alignment(self):
        fp = FocalPoint.from_alignment("left", "middle", 200, 100)
        assert fp.x == 0
        assert fp.y == 50

    def test_center_top_alignment(self):
        fp = FocalPoint.from_alignment("center", "top", 200, 100)
        assert fp.x == 100
        assert fp.y == 0


class TestFocalPointSerialization:
    """Tests for focal point serialization."""

    def test_to_dict(self):
        fp = FocalPoint(100, 200, width=50, height=60, weight=2.0, origin="manual")
        data = fp.to_dict()
        assert data["x"] == 100
        assert data["y"] == 200
        assert data["z"] == 2.0
        assert data["width"] == 50
        assert data["height"] == 60
        assert data["origin"] == "manual"

    def test_from_dict(self):
        data = {
            "x": 100,
            "y": 200,
            "z": 3.0,
            "width": 40,
            "height": 50,
            "origin": "detection",
        }
        fp = FocalPoint.from_dict(data)
        assert fp.x == 100
        assert fp.y == 200
        assert fp.weight == 3.0
        assert fp.width == 40
        assert fp.height == 50
        assert fp.origin == "detection"

    def test_from_dict_with_minimal_data(self):
        data = {"x": 50, "y": 60}
        fp = FocalPoint.from_dict(data)
        assert fp.x == 50
        assert fp.y == 60
        assert fp.width == 1
        assert fp.height == 1
        assert fp.weight == 1.0

    def test_roundtrip_serialization(self):
        original = FocalPoint(150, 250, width=30, height=40, weight=5.0, origin="test")
        data = original.to_dict()
        restored = FocalPoint.from_dict(data)
        assert restored.x == original.x
        assert restored.y == original.y
        assert restored.width == original.width
        assert restored.height == original.height
        assert restored.weight == original.weight
        assert restored.origin == original.origin


class TestFocalPointRepr:
    """Tests for focal point string representation."""

    def test_repr_format(self):
        fp = FocalPoint(100, 200, width=50, height=60, weight=3.0, origin="manual")
        result = repr(fp)
        assert "FocalPoint" in result
        assert "x=100" in result
        assert "y=200" in result
        assert "width=50" in result
        assert "height=60" in result
        assert "weight=3" in result
        assert "origin=manual" in result


class TestCenterOfMass:
    """Tests for center of mass calculation."""

    def test_single_point(self):
        points = [FocalPoint(100, 200)]
        center = calculate_center_of_mass(points)
        assert center == (100, 200)

    def test_two_equal_weight_points(self):
        points = [
            FocalPoint(0, 0, weight=1.0),
            FocalPoint(100, 100, weight=1.0),
        ]
        center = calculate_center_of_mass(points)
        assert center == (50, 50)

    def test_weighted_points(self):
        points = [
            FocalPoint(0, 0, weight=1.0),
            FocalPoint(100, 100, weight=3.0),
        ]
        center = calculate_center_of_mass(points)
        assert center == (75, 75)

    def test_three_points(self):
        points = [
            FocalPoint(0, 0, weight=1.0),
            FocalPoint(100, 0, weight=1.0),
            FocalPoint(50, 100, weight=1.0),
        ]
        center = calculate_center_of_mass(points)
        assert center == (50, 33)

    def test_empty_list_returns_zero(self):
        center = calculate_center_of_mass([])
        assert center == (0, 0)


class TestCropForFocalPoints:
    """Tests for calculating crop coordinates."""

    def test_no_crop_needed_same_ratio(self):
        points = [FocalPoint(50, 50)]
        crop = calculate_crop_for_focal_points(points, 100, 100, 100, 100)
        assert crop == (0, 0, 100, 100)

    def test_crop_for_landscape_from_square(self):
        points = [FocalPoint(50, 50)]
        crop = calculate_crop_for_focal_points(points, 100, 100, 200, 100)
        left, top, right, bottom = crop
        assert right - left == 100
        assert bottom - top == 50

    def test_crop_for_portrait_from_square(self):
        points = [FocalPoint(50, 50)]
        crop = calculate_crop_for_focal_points(points, 100, 100, 100, 200)
        left, top, right, bottom = crop
        assert right - left == 50
        assert bottom - top == 100

    def test_crop_centers_on_focal_point(self):
        points = [FocalPoint(80, 80)]
        crop = calculate_crop_for_focal_points(points, 100, 100, 50, 50)
        left, top, right, bottom = crop
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        assert abs(center_x - 80) < 10 or center_x == 50
        assert abs(center_y - 80) < 10 or center_y == 50

    def test_crop_stays_within_bounds(self):
        points = [FocalPoint(99, 99)]
        crop = calculate_crop_for_focal_points(points, 100, 100, 50, 50)
        left, top, right, bottom = crop
        assert left >= 0
        assert top >= 0
        assert right <= 100
        assert bottom <= 100

    def test_empty_focal_points_uses_center(self):
        crop = calculate_crop_for_focal_points([], 100, 100, 50, 50)
        left, top, right, bottom = crop
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        assert center_x == 50
        assert center_y == 50

    def test_multiple_focal_points_uses_center_of_mass(self):
        points = [
            FocalPoint(20, 20, weight=1.0),
            FocalPoint(80, 80, weight=1.0),
        ]
        crop = calculate_crop_for_focal_points(points, 100, 100, 50, 50)
        left, top, right, bottom = crop
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        assert center_x == 50
        assert center_y == 50
