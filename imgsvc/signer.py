"""URL signing for secure image requests."""

import hashlib
import hmac
import base64


class Signer:
    """Generate and verify HMAC signatures for URLs."""

    def __init__(self, security_key):
        """
        Initialize the signer.

        Args:
            security_key: Secret key for signing
        """
        if isinstance(security_key, str):
            security_key = security_key.encode("utf-8")
        self.security_key = security_key

    def signature(self, url_path):
        """
        Generate a signature for a URL path.

        Args:
            url_path: The URL path to sign (without leading /)

        Returns:
            str: Base64url-encoded signature
        """
        if url_path.startswith("/"):
            url_path = url_path[1:]

        if isinstance(url_path, str):
            url_path = url_path.encode("utf-8")

        digest = hmac.new(
            self.security_key,
            url_path,
            hashlib.sha1
        ).digest()

        return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    def validate(self, signature, url_path):
        """
        Validate a signature against a URL path.

        Args:
            signature: Signature to validate
            url_path: URL path that was signed

        Returns:
            bool: True if signature is valid
        """
        expected = self.signature(url_path)
        return hmac.compare_digest(signature, expected)


def sign_url(url_path, security_key):
    """
    Sign a URL path and return the signed URL.

    Args:
        url_path: URL path to sign
        security_key: Secret key

    Returns:
        str: Signed URL with signature prefix
    """
    signer = Signer(security_key)

    if url_path.startswith("/"):
        url_path = url_path[1:]

    sig = signer.signature(url_path)
    return f"/{sig}/{url_path}"


def verify_signature(url_path, security_key):
    """
    Verify that a URL has a valid signature.

    Args:
        url_path: Full URL path including signature
        security_key: Secret key

    Returns:
        tuple: (is_valid, unsigned_path)
    """
    if url_path.startswith("/"):
        url_path = url_path[1:]

    parts = url_path.split("/", 1)
    if len(parts) < 2:
        return False, None

    signature, rest = parts
    signer = Signer(security_key)

    if signer.validate(signature, rest):
        return True, "/" + rest

    return False, None
