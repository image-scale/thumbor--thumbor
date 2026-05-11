"""Contrast filter."""

from PIL import ImageEnhance

from imgsvc.filters import BaseFilter, filter_method, ParamTypes


class ContrastFilter(BaseFilter):
    """Adjust image contrast."""

    @filter_method(ParamTypes.Number)
    def contrast(self, value):
        """
        Adjust contrast.

        Args:
            value: Contrast adjustment (-100 to 100)
                   0 = no change, negative = less contrast, positive = more contrast
        """
        if self.engine and self.engine.image:
            factor = 1.0 + (value / 100.0)
            factor = max(0, factor)

            if self.engine.image.mode not in ("RGB", "RGBA"):
                self.engine.image = self.engine.image.convert("RGB")

            enhancer = ImageEnhance.Contrast(self.engine.image)
            self.engine.image = enhancer.enhance(factor)
