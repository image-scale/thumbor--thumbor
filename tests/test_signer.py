"""Tests for URL signing."""

import pytest

from imgsvc.signer import Signer, sign_url, verify_signature


class TestSigner:
    """Tests for Signer class."""

    def test_signature_deterministic(self):
        signer = Signer("secret")
        sig1 = signer.signature("300x200/image.jpg")
        sig2 = signer.signature("300x200/image.jpg")
        assert sig1 == sig2

    def test_signature_differs_for_different_paths(self):
        signer = Signer("secret")
        sig1 = signer.signature("300x200/image.jpg")
        sig2 = signer.signature("400x300/image.jpg")
        assert sig1 != sig2

    def test_signature_differs_for_different_keys(self):
        sig1 = Signer("secret1").signature("image.jpg")
        sig2 = Signer("secret2").signature("image.jpg")
        assert sig1 != sig2

    def test_signature_strips_leading_slash(self):
        signer = Signer("secret")
        sig1 = signer.signature("image.jpg")
        sig2 = signer.signature("/image.jpg")
        assert sig1 == sig2

    def test_validate_correct_signature(self):
        signer = Signer("secret")
        sig = signer.signature("300x200/image.jpg")
        assert signer.validate(sig, "300x200/image.jpg") is True

    def test_validate_wrong_signature(self):
        signer = Signer("secret")
        assert signer.validate("invalid", "300x200/image.jpg") is False

    def test_validate_wrong_path(self):
        signer = Signer("secret")
        sig = signer.signature("300x200/image.jpg")
        assert signer.validate(sig, "400x300/other.jpg") is False

    def test_bytes_key(self):
        signer = Signer(b"secret")
        sig = signer.signature("image.jpg")
        assert len(sig) > 0


class TestSignUrl:
    """Tests for sign_url function."""

    def test_sign_url_format(self):
        signed = sign_url("300x200/image.jpg", "secret")
        assert signed.startswith("/")
        assert "/300x200/image.jpg" in signed

    def test_sign_url_with_leading_slash(self):
        signed1 = sign_url("image.jpg", "secret")
        signed2 = sign_url("/image.jpg", "secret")
        assert signed1 == signed2

    def test_signed_url_can_be_verified(self):
        signed = sign_url("300x200/smart/http://example.com/img.jpg", "secret")
        is_valid, path = verify_signature(signed, "secret")
        assert is_valid is True
        assert path == "/300x200/smart/http://example.com/img.jpg"


class TestVerifySignature:
    """Tests for verify_signature function."""

    def test_verify_valid_signature(self):
        signed = sign_url("300x200/image.jpg", "secret")
        is_valid, path = verify_signature(signed, "secret")
        assert is_valid is True
        assert path == "/300x200/image.jpg"

    def test_verify_invalid_signature(self):
        is_valid, path = verify_signature("/invalid/300x200/image.jpg", "secret")
        assert is_valid is False
        assert path is None

    def test_verify_wrong_key(self):
        signed = sign_url("300x200/image.jpg", "secret1")
        is_valid, path = verify_signature(signed, "secret2")
        assert is_valid is False

    def test_verify_missing_parts(self):
        is_valid, path = verify_signature("/onlyonepart", "secret")
        assert is_valid is False

    def test_verify_strips_leading_slash(self):
        signed = sign_url("300x200/image.jpg", "secret")
        is_valid1, _ = verify_signature(signed, "secret")
        is_valid2, _ = verify_signature(signed.lstrip("/"), "secret")
        assert is_valid1 is True
        assert is_valid2 is True
