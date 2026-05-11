"""Focal point support for smart cropping."""


class FocalPoint:
    """
    Represents a point of interest in an image for smart cropping.

    Focal points have coordinates (x, y), dimensions (width, height),
    a weight for calculating center of mass, and an origin indicating
    how the point was determined.
    """

    ALIGNMENT_PERCENTAGES = {
        "left": 0.0,
        "center": 0.5,
        "right": 1.0,
        "top": 0.0,
        "middle": 0.5,
        "bottom": 1.0,
    }

    def __init__(self, x, y, width=1, height=1, weight=1.0, origin="alignment"):
        """
        Create a focal point.

        Args:
            x: X coordinate (center of the focal area)
            y: Y coordinate (center of the focal area)
            width: Width of the focal area
            height: Height of the focal area
            weight: Weight for center of mass calculation
            origin: How this point was determined (alignment, detection, manual)
        """
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)
        self.weight = float(weight)
        self.origin = origin

    @classmethod
    def from_square(cls, x, y, width, height, origin="detection"):
        """
        Create a focal point from a bounding box.

        The focal point will be centered in the box, with weight
        proportional to the box area.

        Args:
            x: Left edge of the box
            y: Top edge of the box
            width: Width of the box
            height: Height of the box
            origin: How this point was determined
        """
        center_x = x + width // 2
        center_y = y + height // 2
        weight = width * height
        return cls(center_x, center_y, width=width, height=height,
                   weight=weight, origin=origin)

    @classmethod
    def from_alignment(cls, halign, valign, image_width, image_height):
        """
        Create a focal point from alignment strings.

        Args:
            halign: Horizontal alignment (left, center, right)
            valign: Vertical alignment (top, middle, bottom)
            image_width: Width of the image
            image_height: Height of the image
        """
        x_pct = cls.ALIGNMENT_PERCENTAGES.get(halign, 0.5)
        y_pct = cls.ALIGNMENT_PERCENTAGES.get(valign, 0.5)

        x = int(image_width * x_pct)
        y = int(image_height * y_pct)

        return cls(x, y)

    def to_dict(self):
        """Serialize focal point to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "z": self.weight,
            "width": self.width,
            "height": self.height,
            "origin": self.origin,
        }

    @classmethod
    def from_dict(cls, data):
        """Deserialize focal point from dictionary."""
        return cls(
            x=int(data["x"]),
            y=int(data["y"]),
            width=int(data.get("width", 1)),
            height=int(data.get("height", 1)),
            weight=float(data.get("z", 1.0)),
            origin=data.get("origin", "alignment"),
        )

    def __repr__(self):
        return (
            f"FocalPoint(x={self.x}, y={self.y}, width={self.width}, "
            f"height={self.height}, weight={self.weight:.0f}, origin={self.origin})"
        )


def calculate_center_of_mass(focal_points):
    """
    Calculate the center of mass from weighted focal points.

    Args:
        focal_points: List of FocalPoint instances

    Returns:
        Tuple (x, y) representing the weighted center
    """
    if not focal_points:
        return (0, 0)

    total_weight = 0.0
    total_x = 0.0
    total_y = 0.0

    for point in focal_points:
        total_weight += point.weight
        total_x += point.x * point.weight
        total_y += point.y * point.weight

    if total_weight == 0:
        return (0, 0)

    avg_x = total_x / total_weight
    avg_y = total_y / total_weight

    return (int(avg_x), int(avg_y))


def calculate_crop_for_focal_points(
    focal_points, source_width, source_height, target_width, target_height
):
    """
    Calculate optimal crop coordinates to preserve focal points.

    Given focal points and target dimensions, calculate crop coordinates
    that best preserve the areas of interest while achieving the target
    aspect ratio.

    Args:
        focal_points: List of FocalPoint instances
        source_width: Width of source image
        source_height: Height of source image
        target_width: Desired width after cropping
        target_height: Desired height after cropping

    Returns:
        Tuple (left, top, right, bottom) for crop coordinates
    """
    if not focal_points:
        focal_x, focal_y = source_width // 2, source_height // 2
    else:
        focal_x, focal_y = calculate_center_of_mass(focal_points)

    source_ratio = source_width / source_height if source_height > 0 else 1
    target_ratio = target_width / target_height if target_height > 0 else 1

    if abs(source_ratio - target_ratio) < 0.01:
        return (0, 0, source_width, source_height)

    if target_width / source_width > target_height / source_height:
        crop_width = source_width
        crop_height = int(round(source_width * target_height / target_width))
    else:
        crop_width = int(round(target_width * source_height / target_height))
        crop_height = source_height

    crop_left = int(round(
        min(
            max(focal_x - crop_width / 2, 0),
            source_width - crop_width
        )
    ))
    crop_left = max(0, min(crop_left, source_width - crop_width))
    crop_right = min(crop_left + crop_width, source_width)

    crop_top = int(round(
        min(
            max(focal_y - crop_height / 2, 0),
            source_height - crop_height
        )
    ))
    crop_top = max(0, min(crop_top, source_height - crop_height))
    crop_bottom = min(crop_top + crop_height, source_height)

    return (crop_left, crop_top, crop_right, crop_bottom)
