"""Image transformation coordinator."""

from imgsvc.focal import FocalPoint, calculate_center_of_mass


class ImageTransformer:
    """
    Coordinates image transformation operations.

    Applies transformations in the correct order:
    1. Manual crop (if specified)
    2. Calculate target dimensions
    3. Adjust focal points
    4. Auto-crop to achieve aspect ratio
    5. Resize
    6. Flip
    """

    def __init__(self, engine, params):
        """
        Initialize the transformer.

        Args:
            engine: Image processing engine with loaded image
            params: RequestParams with transformation settings
        """
        self.engine = engine
        self.params = params
        self.focal_points = list(params.focal_points)
        self.target_width = None
        self.target_height = None

    def transform(self):
        """Apply all transformations to the image."""
        self._manual_crop()
        self._calculate_target_dimensions()
        self._adjust_focal_points()

        if self.params.fit_in:
            self._fit_in_resize()
        else:
            if not self.params.stretch:
                self._auto_crop()
            self._resize()

        self._flip()

    def _manual_crop(self):
        """Apply manual crop if coordinates are specified."""
        if not self.params.should_crop:
            return

        source_width, source_height = self.engine.size
        crop = self.params.crop

        left = max(0, min(crop["left"], source_width))
        top = max(0, min(crop["top"], source_height))
        right = max(0, min(crop["right"], source_width))
        bottom = max(0, min(crop["bottom"], source_height))

        if left >= right or top >= bottom:
            self.params.should_crop = False
            return

        self.engine.crop(left, top, right, bottom)

    def _calculate_target_dimensions(self):
        """Calculate target dimensions from request parameters."""
        source_width, source_height = self.engine.size

        width = self.params.width
        height = self.params.height

        if not width and not height:
            self.target_width = source_width
            self.target_height = source_height
            return

        if width == "orig":
            self.target_width = source_width
        elif width:
            self.target_width = int(width)
        else:
            self.target_width = self.engine.get_proportional_width(height)

        if height == "orig":
            self.target_height = source_height
        elif height:
            self.target_height = int(height)
        else:
            self.target_height = self.engine.get_proportional_height(width)

    def _adjust_focal_points(self):
        """Adjust focal points after manual crop and create defaults."""
        source_width, source_height = self.engine.size

        if self.focal_points and self.params.should_crop:
            crop = self.params.crop
            adjusted = []
            for point in self.focal_points:
                if (point.x < crop["left"] or point.x > crop["right"] or
                    point.y < crop["top"] or point.y > crop["bottom"]):
                    continue
                adjusted_point = FocalPoint(
                    x=point.x - crop["left"],
                    y=point.y - crop["top"],
                    width=point.width,
                    height=point.height,
                    weight=point.weight,
                    origin=point.origin
                )
                adjusted.append(adjusted_point)
            self.focal_points = adjusted

        if not self.focal_points:
            self.focal_points = [
                FocalPoint.from_alignment(
                    self.params.halign,
                    self.params.valign,
                    source_width,
                    source_height
                )
            ]

    def _auto_crop(self):
        """Auto-crop to achieve target aspect ratio while preserving focal points."""
        source_width, source_height = self.engine.size

        if self.target_width is None or self.target_height is None:
            return

        target_width = self.target_width or 1
        target_height = self.target_height or 1

        source_ratio = round(source_width / source_height, 2)
        target_ratio = round(target_width / target_height, 2)

        if source_ratio == target_ratio:
            return

        focal_x, focal_y = calculate_center_of_mass(self.focal_points)

        if target_width / source_width > target_height / source_height:
            crop_width = source_width
            crop_height = int(round(source_width * target_height / target_width))
        else:
            crop_width = int(round(target_width * source_height / target_height))
            crop_height = source_height

        crop_left = int(round(
            min(max(focal_x - crop_width / 2, 0), source_width - crop_width)
        ))
        crop_right = min(crop_left + crop_width, source_width)

        crop_top = int(round(
            min(max(focal_y - crop_height / 2, 0), source_height - crop_height)
        ))
        crop_bottom = min(crop_top + crop_height, source_height)

        self.engine.crop(crop_left, crop_top, crop_right, crop_bottom)

    def _resize(self):
        """Resize image to target dimensions."""
        if self.target_width is None or self.target_height is None:
            return

        source_width, source_height = self.engine.size
        if source_width == self.target_width and source_height == self.target_height:
            return

        width = max(1, self.target_width)
        height = max(1, self.target_height)
        self.engine.resize(width, height)

    def _fit_in_resize(self):
        """Resize to fit within target box without cropping."""
        source_width, source_height = self.engine.size

        if self.target_width is None or self.target_height is None:
            return

        target_width = self.target_width
        target_height = self.target_height

        if self.params.adaptive:
            source_is_portrait = source_height > source_width
            target_is_portrait = target_height > target_width
            if source_is_portrait != target_is_portrait:
                target_width, target_height = target_height, target_width
                self.target_width = target_width
                self.target_height = target_height

        sign = -1 if self.params.full else 1

        if sign == 1 and target_width >= source_width and target_height >= source_height:
            return

        width_ratio = source_width / target_width
        height_ratio = source_height / target_height

        if width_ratio * sign >= height_ratio * sign:
            resize_width = target_width
            resize_height = round(source_height * target_width / source_width)
        else:
            resize_height = target_height
            resize_width = round(source_width * target_height / source_height)

        self.engine.resize(max(1, resize_width), max(1, resize_height))

    def _flip(self):
        """Apply flip transformations."""
        if self.params.horizontal_flip:
            self.engine.flip_horizontally()
        if self.params.vertical_flip:
            self.engine.flip_vertically()

    def get_target_dimensions(self):
        """Return the calculated target dimensions."""
        if self.target_width is None:
            self._calculate_target_dimensions()
        return (self.target_width, self.target_height)
