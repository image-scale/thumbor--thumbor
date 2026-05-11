"""Format filter."""

from imgsvc.filters import BaseFilter, filter_method, ParamTypes


FORMAT_MAP = {
    "jpeg": ".jpg",
    "jpg": ".jpg",
    "png": ".png",
    "gif": ".gif",
    "webp": ".webp",
}


class FormatFilter(BaseFilter):
    """Set output format."""

    @filter_method(ParamTypes.String)
    def format(self, fmt):
        """
        Set the output format.

        Args:
            fmt: Format name (jpeg, png, gif, webp)

        Returns:
            dict with format setting
        """
        fmt_lower = fmt.lower().strip()
        extension = FORMAT_MAP.get(fmt_lower, f".{fmt_lower}")

        if self.context:
            if hasattr(self.context, "request"):
                self.context.request.format = extension
            elif hasattr(self.context, "format"):
                self.context.format = extension

        return {"format": extension}
