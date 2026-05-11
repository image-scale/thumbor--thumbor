"""Request parameter handling for image transformations."""

from typing import List, Optional, Dict, Any

from imgsvc.focal import FocalPoint


class RequestParams:
    """
    Contains all parameters for an image transformation request.

    Stores dimensions, crop coordinates, transformation options,
    filters, and other settings extracted from the request URL.
    """

    def __init__(
        self,
        width: Any = 0,
        height: Any = 0,
        crop_left: int = None,
        crop_top: int = None,
        crop_right: int = None,
        crop_bottom: int = None,
        crop: Dict[str, int] = None,
        fit_in: bool = False,
        full: bool = False,
        adaptive: bool = False,
        horizontal_flip: bool = False,
        vertical_flip: bool = False,
        halign: str = "center",
        valign: str = "middle",
        smart: bool = False,
        quality: int = 80,
        filters: str = None,
        image_url: str = None,
        focal_points: List[FocalPoint] = None,
        unsafe: bool = False,
        hash: str = None,
        meta: bool = False,
        trim: str = None,
        stretch: bool = False,
        debug: bool = False,
    ):
        self.width = self._parse_dimension(width)
        self.height = self._parse_dimension(height)

        if crop is not None:
            self.crop = {k: self._int_or_0(v) for k, v in crop.items()}
        else:
            self.crop = {
                "left": self._int_or_0(crop_left),
                "top": self._int_or_0(crop_top),
                "right": self._int_or_0(crop_right),
                "bottom": self._int_or_0(crop_bottom),
            }

        self.should_crop = (
            self.crop["left"] > 0 or
            self.crop["top"] > 0 or
            self.crop["right"] > 0 or
            self.crop["bottom"] > 0
        )

        self.fit_in = bool(fit_in)
        self.full = bool(full)
        self.adaptive = bool(adaptive)
        self.horizontal_flip = bool(horizontal_flip)
        self.vertical_flip = bool(vertical_flip)
        self.halign = halign or "center"
        self.valign = valign or "middle"
        self.smart = bool(smart)
        self.quality = int(quality) if quality else 80
        self.filters = filters or ""
        self.image_url = image_url or ""
        self.focal_points = focal_points or []
        self.unsafe = unsafe == "unsafe" or unsafe is True
        self.hash = hash
        self.meta = bool(meta)
        self.trim = trim
        self.stretch = bool(stretch)
        self.debug = bool(debug)

        if self.trim:
            self._parse_trim()

        self.format = None
        self.max_bytes = None
        self.max_age = None
        self.prevent_result_storage = False
        self.detection_error = None

    def _parse_dimension(self, value):
        """Parse dimension value (int or 'orig')."""
        if value == "orig":
            return "orig"
        return self._int_or_0(value)

    @staticmethod
    def _int_or_0(value):
        """Convert value to int or return 0."""
        if value is None:
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    def _parse_trim(self):
        """Parse trim settings from trim string."""
        if not self.trim:
            return

        parts = self.trim.split(":")
        self.trim_pos = parts[1] if len(parts) > 1 else "top-left"
        self.trim_tolerance = int(parts[2]) if len(parts) > 2 else 0

    def add_focal_point(self, focal_point: FocalPoint):
        """Add a focal point to the list."""
        self.focal_points.append(focal_point)

    def get_filters_list(self) -> List[str]:
        """Split filter string into list of individual filters."""
        if not self.filters:
            return []

        filters = []
        current = ""
        paren_depth = 0

        for char in self.filters:
            if char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1
            elif char == ":" and paren_depth == 0:
                if current:
                    filters.append(current)
                current = ""
                continue
            current += char

        if current:
            filters.append(current)

        return filters

    def swap_dimensions_if_adaptive(self, image_width: int, image_height: int):
        """
        Swap target dimensions if adaptive mode is on and orientations differ.

        This allows a portrait target to automatically become landscape
        if the source image is landscape, and vice versa.
        """
        if not self.adaptive:
            return

        if isinstance(self.width, str) or isinstance(self.height, str):
            return

        source_is_portrait = image_height > image_width
        target_is_portrait = self.height > self.width

        if source_is_portrait != target_is_portrait:
            self.width, self.height = self.height, self.width

    def __repr__(self):
        return (
            f"RequestParams(width={self.width}, height={self.height}, "
            f"fit_in={self.fit_in}, smart={self.smart}, "
            f"image_url={self.image_url!r})"
        )
