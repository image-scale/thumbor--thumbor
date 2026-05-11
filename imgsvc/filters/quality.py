"""Quality filter."""

from imgsvc.filters import BaseFilter, filter_method, ParamTypes


class QualityFilter(BaseFilter):
    """Set output quality for JPEG/WebP formats."""

    @filter_method(ParamTypes.PositiveNumber)
    def quality(self, value):
        """
        Set output quality.

        Args:
            value: Quality level (1-100)

        Returns:
            dict with quality setting to be used by output
        """
        quality = max(1, min(100, int(value)))
        if self.context:
            if hasattr(self.context, "request"):
                self.context.request.quality = quality
            elif hasattr(self.context, "quality"):
                self.context.quality = quality
        return {"quality": quality}
