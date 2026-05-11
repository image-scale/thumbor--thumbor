"""Rotate filter."""

from imgsvc.filters import BaseFilter, filter_method, ParamTypes


class RotateFilter(BaseFilter):
    """Rotate the image."""

    @filter_method(ParamTypes.Number)
    def rotate(self, degrees):
        """
        Rotate the image counter-clockwise.

        Args:
            degrees: Rotation angle in degrees
        """
        if self.engine:
            self.engine.rotate(degrees)
