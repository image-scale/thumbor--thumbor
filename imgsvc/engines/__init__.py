"""Image processing engines."""

import re

MIME_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}

EXTENSION_TO_FORMAT = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".gif": "GIF",
    ".webp": "WEBP",
}


class ImageLoadError(Exception):
    """Raised when an image cannot be loaded."""
    pass


class EngineResult:
    """Result from loading an image."""

    def __init__(self, buffer=None, successful=True, error=None):
        self.buffer = buffer
        self.successful = successful
        self.error = error


class BaseImageEngine:
    """Base class for image processing engines."""

    def __init__(self):
        self.image = None
        self.extension = None
        self.source_width = None
        self.source_height = None

    @property
    def size(self):
        """Return (width, height) of current image."""
        raise NotImplementedError()

    def load(self, buffer, extension=None):
        """Load image from bytes buffer."""
        raise NotImplementedError()

    def resize(self, width, height):
        """Resize image to specified dimensions."""
        raise NotImplementedError()

    def crop(self, left, top, right, bottom):
        """Crop image to specified box."""
        raise NotImplementedError()

    def flip_horizontally(self):
        """Flip image left-to-right."""
        raise NotImplementedError()

    def flip_vertically(self):
        """Flip image top-to-bottom."""
        raise NotImplementedError()

    def rotate(self, degrees):
        """Rotate image counter-clockwise by specified degrees."""
        raise NotImplementedError()

    def read(self, extension=None, quality=80):
        """Output image as bytes in specified format."""
        raise NotImplementedError()

    def get_mimetype(self, buffer):
        """Detect image mimetype from buffer header bytes."""
        if buffer.startswith(b"GIF8"):
            return "image/gif"
        elif buffer.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif buffer.startswith(b"\xff\xd8"):
            return "image/jpeg"
        elif len(buffer) > 12 and buffer[8:12] == b"WEBP":
            return "image/webp"
        return None

    def get_proportional_width(self, new_height):
        """Calculate proportional width for given height."""
        width, height = self.size
        if height == 0:
            return 0
        return round(float(new_height) * width / height)

    def get_proportional_height(self, new_width):
        """Calculate proportional height for given width."""
        width, height = self.size
        if width == 0:
            return 0
        return round(float(new_width) * height / width)
