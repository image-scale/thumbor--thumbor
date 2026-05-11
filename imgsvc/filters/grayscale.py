"""Grayscale filter."""

from imgsvc.filters import BaseFilter, filter_method


class GrayscaleFilter(BaseFilter):
    """Convert image to grayscale."""

    @filter_method()
    def grayscale(self):
        """Convert the image to grayscale."""
        if self.engine and self.engine.image:
            if "A" in self.engine.image.mode:
                self.engine.image = self.engine.image.convert("LA")
            else:
                self.engine.image = self.engine.image.convert("L")
