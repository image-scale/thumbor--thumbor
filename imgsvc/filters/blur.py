"""Blur filter."""

from PIL import ImageFilter

from imgsvc.filters import BaseFilter, filter_method, ParamTypes


class BlurFilter(BaseFilter):
    """Apply Gaussian blur to the image."""

    @filter_method(ParamTypes.PositiveNonZeroNumber, ParamTypes.DecimalNumber)
    def blur(self, radius, sigma=None):
        """
        Apply blur filter.

        Args:
            radius: Blur radius in pixels
            sigma: Optional sigma value (defaults to radius)
        """
        if sigma is None or sigma == 0:
            sigma = radius

        if self.engine and self.engine.image:
            self.engine.image = self.engine.image.filter(
                ImageFilter.GaussianBlur(radius=radius)
            )
