"""HTTP request handlers for the image service."""

import tornado.web

from imgsvc.url_parser import parse_url
from imgsvc.context import RequestContext
from imgsvc.transformer import ImageTransformer
from imgsvc.signer import verify_signature


class ImageHandler(tornado.web.RequestHandler):
    """Handler for image transformation requests."""

    def initialize(self, context):
        """
        Initialize the handler with server context.

        Args:
            context: ServerContext instance
        """
        self.context = context

    async def get(self, path):
        """
        Handle GET request for image transformation.

        Args:
            path: URL path containing transformation parameters
        """
        try:
            url_path = "/" + path
            request_params = await self._parse_and_validate(url_path)

            if request_params is None:
                return

            image_data = await self._load_image(request_params.image_url)
            if image_data is None:
                return

            result = await self._process_image(image_data, request_params)
            if result is None:
                return

            self._send_response(result)

        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})

    async def _parse_and_validate(self, url_path):
        """Parse URL and validate signature if required."""
        config = self.context.config

        if url_path.startswith("/unsafe/"):
            if not config.ALLOW_UNSAFE_URL:
                self.set_status(403)
                self.write({"error": "Unsafe URLs not allowed"})
                return None
            return parse_url(url_path)

        if config.SECURITY_KEY:
            is_valid, unsigned_path = verify_signature(
                url_path, config.SECURITY_KEY
            )
            if not is_valid:
                self.set_status(403)
                self.write({"error": "Invalid signature"})
                return None
            return parse_url(unsigned_path)

        if config.ALLOW_UNSAFE_URL:
            return parse_url(url_path)

        self.set_status(403)
        self.write({"error": "Signature required"})
        return None

    async def _load_image(self, image_url):
        """Load the source image."""
        try:
            loader = self.context.loader
            return await loader.load(image_url)
        except Exception as e:
            error_type = type(e).__name__
            if "NotFound" in error_type:
                self.set_status(404)
                self.write({"error": "Image not found"})
            elif "Security" in error_type:
                self.set_status(403)
                self.write({"error": "Source not allowed"})
            else:
                self.set_status(502)
                self.write({"error": f"Failed to load image: {e}"})
            return None

    async def _process_image(self, image_data, request_params):
        """Transform the image according to parameters."""
        try:
            req_ctx = RequestContext(self.context, request_params)
            engine = req_ctx.create_engine()
            engine.load(image_data)

            transformer = ImageTransformer(engine, request_params)
            transformer.transform()

            if request_params.filters:
                filter_runner = self.context.filter_factory.create_instances(
                    request_params.filters, req_ctx
                )
                results = filter_runner.run(engine)
                if "quality" in results:
                    req_ctx.quality = results["quality"]
                if "format" in results:
                    req_ctx.format = results["format"]

            output_format = self._determine_format(req_ctx, request_params)
            output_data = engine.read(
                extension="." + output_format,
                quality=req_ctx.quality
            )

            return {
                "data": output_data,
                "format": output_format,
            }

        except Exception as e:
            self.set_status(500)
            self.write({"error": f"Failed to process image: {e}"})
            return None

    def _determine_format(self, req_ctx, request_params):
        """Determine output format from context or Accept header."""
        if req_ctx.format:
            return req_ctx.format.lstrip(".")

        if self.context.config.AUTO_WEBP:
            accept = self.request.headers.get("Accept", "")
            if "image/webp" in accept:
                return "webp"

        if hasattr(request_params, "image_url"):
            url = request_params.image_url.lower()
            for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                if url.endswith(ext):
                    return ext.lstrip(".")

        return "jpeg"

    def _send_response(self, result):
        """Send the processed image response."""
        format_map = {
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
        }

        content_type = format_map.get(result["format"], "image/jpeg")
        self.set_header("Content-Type", content_type)
        self.set_header("Cache-Control", "public, max-age=31536000")
        self.write(result["data"])


class HealthHandler(tornado.web.RequestHandler):
    """Health check endpoint."""

    async def get(self):
        """Return health status."""
        self.write({"status": "ok"})
