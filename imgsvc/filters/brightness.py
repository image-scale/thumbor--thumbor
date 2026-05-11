"""Brightness filter."""

from PIL import ImageEnhance

from imgsvc.filters import BaseFilter, filter_method, ParamTypes


class BrightnessFilter(BaseFilter):
    """Adjust image brightness."""

    @filter_method(ParamTypes.Number)
    def brightness(self, value):
        """
        Adjust brightness.

        Args:
            value: Brightness adjustment (-100 to 100)
                   0 = no change, negative = darker, positive = brighter
        """
        if self.engine and self.engine.image:
            factor = 1.0 + (value / 100.0)
            factor = max(0, factor)

            if self.engine.image.mode not in ("RGB", "RGBA"):
                self.engine.image = self.engine.image.convert("RGB")

            enhancer = ImageEnhance.Brightness(self.engine.image)
            self.engine.image = enhancer.enhance(factor)
