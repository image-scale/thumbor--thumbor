"""Tests for URL parsing."""

import pytest

from imgsvc.url_parser import parse_url, build_url, get_url_regex


class TestUrlParsingBasic:
    """Tests for basic URL parsing."""

    def test_parse_simple_url(self):
        params = parse_url("/unsafe/300x200/http://example.com/image.jpg")
        assert params.width == 300
        assert params.height == 200
        assert params.image_url == "http://example.com/image.jpg"
        assert params.unsafe is True

    def test_parse_url_without_leading_slash(self):
        params = parse_url("unsafe/300x200/http://example.com/image.jpg")
        assert params.width == 300
        assert params.height == 200

    def test_parse_url_with_hash(self):
        params = parse_url("/abc123def/300x200/http://example.com/image.jpg")
        assert params.hash == "abc123def"
        assert params.unsafe is False

    def test_parse_url_orig_dimensions(self):
        params = parse_url("/unsafe/origxorig/http://example.com/image.jpg")
        assert params.width == "orig"
        assert params.height == "orig"


class TestUrlParsingDimensions:
    """Tests for dimension parsing."""

    def test_parse_width_only(self):
        params = parse_url("/unsafe/300x0/http://example.com/image.jpg")
        assert params.width == 300
        assert params.height == 0

    def test_parse_height_only(self):
        params = parse_url("/unsafe/0x200/http://example.com/image.jpg")
        assert params.width == 0
        assert params.height == 200


class TestUrlParsingFitIn:
    """Tests for fit-in mode parsing."""

    def test_parse_fit_in(self):
        params = parse_url("/unsafe/fit-in/300x200/http://example.com/image.jpg")
        assert params.fit_in is True
        assert params.width == 300
        assert params.height == 200

    def test_parse_adaptive_fit_in(self):
        params = parse_url("/unsafe/adaptive-fit-in/300x200/http://example.com/image.jpg")
        assert params.fit_in is True
        assert params.adaptive is True

    def test_parse_full_fit_in(self):
        params = parse_url("/unsafe/full-fit-in/300x200/http://example.com/image.jpg")
        assert params.fit_in is True
        assert params.full is True


class TestUrlParsingSmart:
    """Tests for smart mode parsing."""

    def test_parse_smart(self):
        params = parse_url("/unsafe/300x200/smart/http://example.com/image.jpg")
        assert params.smart is True

    def test_parse_no_smart(self):
        params = parse_url("/unsafe/300x200/http://example.com/image.jpg")
        assert params.smart is False


class TestUrlParsingCrop:
    """Tests for crop coordinate parsing."""

    def test_parse_crop_coordinates(self):
        params = parse_url("/unsafe/10x20:90x80/300x200/http://example.com/image.jpg")
        assert params.crop["left"] == 10
        assert params.crop["top"] == 20
        assert params.crop["right"] == 90
        assert params.crop["bottom"] == 80
        assert params.should_crop is True

    def test_parse_no_crop(self):
        params = parse_url("/unsafe/300x200/http://example.com/image.jpg")
        assert params.should_crop is False


class TestUrlParsingFlip:
    """Tests for flip parsing."""

    def test_parse_horizontal_flip(self):
        params = parse_url("/unsafe/-300x200/http://example.com/image.jpg")
        assert params.horizontal_flip is True
        assert params.width == 300

    def test_parse_vertical_flip(self):
        params = parse_url("/unsafe/300x-200/http://example.com/image.jpg")
        assert params.vertical_flip is True
        assert params.height == 200

    def test_parse_both_flips(self):
        params = parse_url("/unsafe/-300x-200/http://example.com/image.jpg")
        assert params.horizontal_flip is True
        assert params.vertical_flip is True


class TestUrlParsingAlignment:
    """Tests for alignment parsing."""

    def test_parse_left_alignment(self):
        params = parse_url("/unsafe/300x200/left/http://example.com/image.jpg")
        assert params.halign == "left"

    def test_parse_right_alignment(self):
        params = parse_url("/unsafe/300x200/right/http://example.com/image.jpg")
        assert params.halign == "right"

    def test_parse_top_alignment(self):
        params = parse_url("/unsafe/300x200/top/http://example.com/image.jpg")
        assert params.valign == "top"

    def test_parse_bottom_alignment(self):
        params = parse_url("/unsafe/300x200/bottom/http://example.com/image.jpg")
        assert params.valign == "bottom"

    def test_parse_combined_alignment(self):
        params = parse_url("/unsafe/300x200/left/top/http://example.com/image.jpg")
        assert params.halign == "left"
        assert params.valign == "top"

    def test_default_alignment(self):
        params = parse_url("/unsafe/300x200/http://example.com/image.jpg")
        assert params.halign == "center"
        assert params.valign == "middle"


class TestUrlParsingFilters:
    """Tests for filter parsing."""

    def test_parse_single_filter(self):
        params = parse_url("/unsafe/filters:blur(5)/http://example.com/image.jpg")
        assert params.filters == "blur(5)"

    def test_parse_multiple_filters(self):
        params = parse_url("/unsafe/filters:blur(5):grayscale()/http://example.com/image.jpg")
        assert params.filters == "blur(5):grayscale()"

    def test_parse_filters_with_dimensions(self):
        params = parse_url("/unsafe/300x200/filters:quality(80)/http://example.com/image.jpg")
        assert params.width == 300
        assert params.height == 200
        assert params.filters == "quality(80)"


class TestUrlParsingImageUrl:
    """Tests for image URL parsing."""

    def test_parse_http_url(self):
        params = parse_url("/unsafe/http://example.com/image.jpg")
        assert params.image_url == "http://example.com/image.jpg"

    def test_parse_https_url(self):
        params = parse_url("/unsafe/https://example.com/image.jpg")
        assert params.image_url == "https://example.com/image.jpg"

    def test_parse_url_with_query_string(self):
        params = parse_url("/unsafe/http://example.com/image.jpg?v=123")
        assert params.image_url == "http://example.com/image.jpg?v=123"

    def test_parse_encoded_url(self):
        params = parse_url("/unsafe/http%3A%2F%2Fexample.com%2Fimage.jpg")
        assert params.image_url == "http://example.com/image.jpg"


class TestUrlParsingMeta:
    """Tests for meta flag parsing."""

    def test_parse_meta(self):
        params = parse_url("/unsafe/meta/300x200/http://example.com/image.jpg")
        assert params.meta is True


class TestUrlParsingTrim:
    """Tests for trim parsing."""

    def test_parse_trim(self):
        params = parse_url("/unsafe/trim/300x200/http://example.com/image.jpg")
        assert params.trim == "trim"

    def test_parse_trim_with_position(self):
        params = parse_url("/unsafe/trim:bottom-right/300x200/http://example.com/image.jpg")
        assert "bottom-right" in params.trim


class TestUrlParsingComplex:
    """Tests for complex URL combinations."""

    def test_parse_complex_url(self):
        url = "/unsafe/10x20:90x80/fit-in/300x200/left/top/smart/filters:blur(5)/http://example.com/image.jpg"
        params = parse_url(url)
        assert params.crop["left"] == 10
        assert params.crop["top"] == 20
        assert params.fit_in is True
        assert params.width == 300
        assert params.height == 200
        assert params.halign == "left"
        assert params.valign == "top"
        assert params.smart is True
        assert params.filters == "blur(5)"
        assert params.image_url == "http://example.com/image.jpg"


class TestUrlParsingInvalid:
    """Tests for invalid URL handling."""

    def test_parse_empty_path_raises_error(self):
        with pytest.raises(ValueError):
            parse_url("")

    def test_parse_root_only_raises_error(self):
        with pytest.raises(ValueError):
            parse_url("/")


class TestBuildUrl:
    """Tests for URL building."""

    def test_build_simple_url(self):
        url = build_url("http://example.com/image.jpg", width=300, height=200)
        assert "unsafe" in url
        assert "300x200" in url
        assert "http://example.com/image.jpg" in url

    def test_build_url_with_smart(self):
        url = build_url("http://example.com/image.jpg", width=300, height=200, smart=True)
        assert "smart" in url

    def test_build_url_with_fit_in(self):
        url = build_url("http://example.com/image.jpg", width=300, height=200, fit_in=True)
        assert "fit-in" in url

    def test_build_url_with_filters(self):
        url = build_url("http://example.com/image.jpg", filters="blur(5):grayscale()")
        assert "filters:blur(5):grayscale()" in url

    def test_build_url_with_alignment(self):
        url = build_url("http://example.com/image.jpg", halign="left", valign="top")
        assert "left" in url
        assert "top" in url

    def test_build_url_with_crop(self):
        url = build_url("http://example.com/image.jpg", crop=(10, 20, 90, 80))
        assert "10x20:90x80" in url

    def test_build_url_with_flips(self):
        url = build_url(
            "http://example.com/image.jpg",
            width=300, height=200,
            horizontal_flip=True, vertical_flip=True
        )
        assert "-300x-200" in url


class TestGetUrlRegex:
    """Tests for regex retrieval."""

    def test_get_url_regex_returns_compiled(self):
        regex = get_url_regex()
        assert hasattr(regex, "match")
        assert hasattr(regex, "pattern")
