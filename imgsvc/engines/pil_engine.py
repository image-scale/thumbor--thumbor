"""PIL-based image processing engine."""

from io import BytesIO

from PIL import Image

from imgsvc.engines import (
    BaseImageEngine,
    ImageLoadError,
    MIME_TO_EXTENSION,
    EXTENSION_TO_FORMAT,
)


class PilEngine(BaseImageEngine):
    """Image processing engine using Pillow."""

    def __init__(self):
        super().__init__()
        self.original_mode = None

    @property
    def size(self):
        """Return (width, height) of current image."""
        if self.image is None:
            return (0, 0)
        return self.image.size

    def load(self, buffer, extension=None):
        """Load image from bytes buffer."""
        if not buffer:
            raise ImageLoadError("Empty buffer provided")

        self.extension = extension
        if extension is None:
            mimetype = self.get_mimetype(buffer)
            if mimetype:
                self.extension = MIME_TO_EXTENSION.get(mimetype, ".jpg")
            else:
                self.extension = ".jpg"

        try:
            self.image = Image.open(BytesIO(buffer))
            self.image.load()
        except Exception as e:
            raise ImageLoadError(f"Failed to load image: {e}")

        self.original_mode = self.image.mode
        self.source_width = self.image.width
        self.source_height = self.image.height

    def resize(self, width, height):
        """Resize image to specified dimensions."""
        if self.image is None:
            return

        width = int(width)
        height = int(height)

        if width <= 0 or height <= 0:
            return

        if self.image.mode in ["1", "P"]:
            if self.image.mode == "1":
                self.image = self.image.convert("RGB")
            else:
                self.image = self.image.convert()

        self.image = self.image.resize(
            (width, height), Image.Resampling.LANCZOS
        )

    def crop(self, left, top, right, bottom):
        """Crop image to specified box coordinates."""
        if self.image is None:
            return

        left = int(left)
        top = int(top)
        right = int(right)
        bottom = int(bottom)

        self.image = self.image.crop((left, top, right, bottom))

    def flip_horizontally(self):
        """Flip image left-to-right."""
        if self.image is None:
            return
        self.image = self.image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    def flip_vertically(self):
        """Flip image top-to-bottom."""
        if self.image is None:
            return
        self.image = self.image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    def rotate(self, degrees):
        """Rotate image counter-clockwise by specified degrees."""
        if self.image is None:
            return

        degrees = int(degrees)

        if degrees == 90:
            self.image = self.image.transpose(Image.Transpose.ROTATE_90)
        elif degrees == 180:
            self.image = self.image.transpose(Image.Transpose.ROTATE_180)
        elif degrees == 270:
            self.image = self.image.transpose(Image.Transpose.ROTATE_270)
        elif degrees != 0:
            self.image = self.image.rotate(degrees, expand=True)

    def read(self, extension=None, quality=80):
        """Output image as bytes in specified format."""
        if self.image is None:
            return b""

        output_ext = extension or self.extension or ".jpg"
        img_format = EXTENSION_TO_FORMAT.get(output_ext, "JPEG")

        output = BytesIO()
        img = self.image

        save_options = {}

        if img_format == "JPEG":
            save_options["quality"] = quality
            save_options["optimize"] = True
            if img.mode not in ["RGB", "L"]:
                img = img.convert("RGB")
        elif img_format == "PNG":
            if img.mode == "CMYK":
                img = img.convert("RGBA")
        elif img_format == "WEBP":
            save_options["quality"] = quality
            if img.mode not in ["RGB", "RGBA"]:
                if img.mode == "P":
                    img = img.convert("RGBA")
                elif "A" in img.mode:
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
        elif img_format == "GIF":
            if img.mode == "CMYK":
                img = img.convert("RGB")

        img.save(output, format=img_format, **save_options)
        return output.getvalue()

    def convert_to_rgb(self):
        """Convert image to RGB mode."""
        if self.image is None:
            return
        if self.image.mode not in ["RGB", "RGBA"]:
            if "A" in self.image.mode:
                self.image = self.image.convert("RGBA")
            elif self.image.mode == "P":
                self.image = self.image.convert()
            else:
                self.image = self.image.convert("RGB")

    def enable_alpha(self):
        """Enable alpha channel on image."""
        if self.image is None:
            return
        if self.image.mode != "RGBA":
            self.image = self.image.convert("RGBA")

    def has_transparency(self):
        """Check if image has transparent pixels."""
        if self.image is None:
            return False

        has_alpha = "A" in self.image.mode or "transparency" in self.image.info

        if has_alpha:
            rgba = self.image.convert("RGBA")
            alpha_channel = rgba.getchannel("A")
            min_alpha = alpha_channel.getextrema()[0]
            return min_alpha < 255

        return False

    def image_data_as_rgb(self):
        """Return image mode and raw RGB/RGBA bytes."""
        if self.image is None:
            return None, None

        img = self.image
        if img.mode not in ["RGB", "RGBA"]:
            if "A" in img.mode:
                img = img.convert("RGBA")
            elif img.mode == "P":
                img = img.convert()
            else:
                img = img.convert("RGB")
            self.image = img

        return img.mode, img.tobytes()

    def set_image_data(self, data):
        """Set raw image data from bytes."""
        if self.image is None:
            return
        self.image.frombytes(data)

    def draw_rectangle(self, x, y, width, height):
        """Draw a rectangle outline on the image."""
        if self.image is None:
            return
        from PIL import ImageDraw
        draw = ImageDraw.Draw(self.image)
        draw.rectangle([x, y, x + width, y + height], outline="red")
