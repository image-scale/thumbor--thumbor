# Todo

## Plan
Build the image service from user-facing features down. Start with basic image operations through the PIL engine, then URL parsing for request parameters, HTTP server integration, storage/loading, filters, and finally smart cropping. Each task delivers testable functionality.

## Tasks
- [x] Task 1: Implement the image processing engine that can load images from bytes, resize, crop, flip, rotate, and output to various formats (JPEG, PNG, WebP, GIF). Users should be able to load an image buffer, perform transformations, and get the result as bytes.
- [x] Task 2: Add focal point support for smart cropping. Users can define focal points with coordinates, dimensions, and weights. When cropping, the engine should calculate the center of mass from focal points and crop to preserve important areas.
- [>] Task 3: Add request parameter handling that parses image transformation options including width, height, crop coordinates, fit-in mode, flip options, alignment, quality, filters, and smart mode settings.
- [ ] Task 4: Add URL parsing to extract transformation parameters from URL paths. URLs follow a pattern like /unsafe/300x200/smart/filters:blur(5)/http://example.com/image.jpg where dimensions, options, filters, and image URL are parsed from the path.
- [ ] Task 5: Add the image transformation coordinator that takes request parameters and applies operations to an image engine in the correct order: manual crop first, then calculate dimensions, adjust focal points, auto-crop if needed, resize, and flip.
- [ ] Task 6: Add the filter system with base filter class and decorator. Filters accept parameters from URLs (like blur(5) or brightness(-20)) and modify image data. Include blur, brightness, contrast, grayscale, quality, rotate, and format filters.
- [ ] Task 7: Add the file loader to load images from the local filesystem. Given a path, it should return the image bytes or an error if the file doesn't exist or is outside allowed paths.
- [ ] Task 8: Add the HTTP loader to fetch images from remote URLs. It should validate source URLs against allowed domains, handle timeouts and errors, and return image bytes with metadata.
- [ ] Task 9: Add file-based storage for caching source images and transformation results. Storage should put/get images by path, support expiration, and handle detector data for smart cropping results.
- [ ] Task 10: Add configuration management to define and load settings from config files. Settings include image limits, quality defaults, loader/storage/engine class paths, security key, allowed sources, and filter lists.
- [ ] Task 11: Add the module importer that dynamically loads engines, loaders, storages, filters, and detectors based on configuration. It validates required modules are present and creates instances.
- [ ] Task 12: Add the server context that holds configuration, imported modules, server parameters, and per-request state. The context is the central object passed to handlers and engines during request processing.
- [ ] Task 13: Add the HTTP handler that receives image requests, validates security signatures or unsafe mode, loads images via loader, applies transformations, and returns processed images with appropriate content types and caching headers.
- [ ] Task 14: Add the Tornado HTTP server that starts the application, configures routing, handles signals, and serves image requests. Include the main entry point and basic URL routing.
- [ ] Task 15: Add URL signing and validation using HMAC signatures. Signed URLs prevent abuse by requiring a valid signature computed from the security key and URL path. Add both signing and verification.
