"""URL parsing for image transformation requests."""

import re
from urllib.parse import unquote

from imgsvc.request_params import RequestParams


HALIGN_VALUES = ("left", "center", "right")
VALIGN_VALUES = ("top", "middle", "bottom")


def _build_url_regex():
    """Build the regex pattern for parsing image URLs."""
    parts = []

    unsafe_or_hash = r"/(?:(?P<unsafe>unsafe)|(?P<hash>[^/]+))"
    parts.append(unsafe_or_hash)

    meta = r"(?:/(?P<meta>meta))?"
    parts.append(meta)

    trim = r"(?:/(?P<trim>trim(?::[^/]+)?))?"
    parts.append(trim)

    crop = r"(?:/(?P<crop_left>\d+)x(?P<crop_top>\d+):(?P<crop_right>\d+)x(?P<crop_bottom>\d+))?"
    parts.append(crop)

    fit_in = r"(?:/(?P<adaptive>adaptive-)?(?P<full>full-)?(?P<fit_in>fit-in))?"
    parts.append(fit_in)

    dimensions = r"(?:/(?P<horizontal_flip>-)?(?P<width>(?:\d+|orig))x(?P<vertical_flip>-)?(?P<height>(?:\d+|orig)))?"
    parts.append(dimensions)

    halign = r"(?:/(?P<halign>left|center|right))?"
    parts.append(halign)

    valign = r"(?:/(?P<valign>top|middle|bottom))?"
    parts.append(valign)

    smart = r"(?:/(?P<smart>smart))?"
    parts.append(smart)

    filters = r"(?:/filters:(?P<filters>[^/]+))?"
    parts.append(filters)

    image = r"/(?P<image>.+)"
    parts.append(image)

    pattern = "^" + "".join(parts) + "$"
    return re.compile(pattern)


URL_REGEX = _build_url_regex()


def parse_url(url_path: str) -> RequestParams:
    """
    Parse a URL path and extract transformation parameters.

    Args:
        url_path: The URL path like /unsafe/300x200/smart/http://example.com/img.jpg

    Returns:
        RequestParams object with all extracted parameters

    Raises:
        ValueError: If the URL path doesn't match the expected format
    """
    if not url_path.startswith("/"):
        url_path = "/" + url_path

    match = URL_REGEX.match(url_path)
    if not match:
        raise ValueError(f"Invalid URL format: {url_path}")

    groups = match.groupdict()

    width = 0
    height = 0
    horizontal_flip = False
    vertical_flip = False

    if groups.get("width"):
        width = groups["width"]
        if groups.get("horizontal_flip"):
            horizontal_flip = True

    if groups.get("height"):
        height = groups["height"]
        if groups.get("vertical_flip"):
            vertical_flip = True

    crop_left = int(groups.get("crop_left") or 0)
    crop_top = int(groups.get("crop_top") or 0)
    crop_right = int(groups.get("crop_right") or 0)
    crop_bottom = int(groups.get("crop_bottom") or 0)

    image_url = groups.get("image", "")
    image_url = unquote(image_url)

    return RequestParams(
        width=width,
        height=height,
        crop_left=crop_left,
        crop_top=crop_top,
        crop_right=crop_right,
        crop_bottom=crop_bottom,
        fit_in=bool(groups.get("fit_in")),
        full=bool(groups.get("full")),
        adaptive=bool(groups.get("adaptive")),
        horizontal_flip=horizontal_flip,
        vertical_flip=vertical_flip,
        halign=groups.get("halign") or "center",
        valign=groups.get("valign") or "middle",
        smart=bool(groups.get("smart")),
        filters=groups.get("filters") or "",
        image_url=image_url,
        unsafe=groups.get("unsafe"),
        hash=groups.get("hash"),
        meta=bool(groups.get("meta")),
        trim=groups.get("trim"),
    )


def get_url_regex():
    """Return the compiled URL regex pattern."""
    return URL_REGEX


def build_url(
    image_url: str,
    width: int = 0,
    height: int = 0,
    smart: bool = False,
    fit_in: bool = False,
    filters: str = None,
    halign: str = None,
    valign: str = None,
    crop: tuple = None,
    horizontal_flip: bool = False,
    vertical_flip: bool = False,
    unsafe: bool = True,
) -> str:
    """
    Build a URL path from transformation parameters.

    Args:
        image_url: The source image URL
        width: Target width (0 for original)
        height: Target height (0 for original)
        smart: Enable smart cropping
        fit_in: Enable fit-in mode
        filters: Filter string like "blur(5):grayscale()"
        halign: Horizontal alignment (left, center, right)
        valign: Vertical alignment (top, middle, bottom)
        crop: Tuple of (left, top, right, bottom) crop coordinates
        horizontal_flip: Flip horizontally
        vertical_flip: Flip vertically
        unsafe: Use unsafe mode (no signature)

    Returns:
        URL path string
    """
    parts = []

    if unsafe:
        parts.append("unsafe")
    else:
        parts.append("HASH_PLACEHOLDER")

    if crop and any(crop):
        parts.append(f"{crop[0]}x{crop[1]}:{crop[2]}x{crop[3]}")

    if fit_in:
        parts.append("fit-in")

    if width or height:
        w_str = f"{'-' if horizontal_flip else ''}{width or 0}"
        h_str = f"{'-' if vertical_flip else ''}{height or 0}"
        parts.append(f"{w_str}x{h_str}")

    if halign and halign != "center":
        parts.append(halign)

    if valign and valign != "middle":
        parts.append(valign)

    if smart:
        parts.append("smart")

    if filters:
        parts.append(f"filters:{filters}")

    parts.append(image_url)

    return "/" + "/".join(parts)
