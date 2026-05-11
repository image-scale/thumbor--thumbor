# Goal

## Project
imgsvc — a Python image processing HTTP server

## Description
An on-demand image processing service that provides cropping, resizing, transformations, and filters through URL parameters. Users make HTTP requests with image URLs and transformation parameters, and the service returns processed images. Key features include smart cropping based on focal points, various image filters (blur, brightness, contrast, grayscale, etc.), support for multiple output formats, caching via storage backends, and a pluggable architecture for engines, loaders, and filters.

## Scope
- ~20 production source files to implement
- ~15 test files to write
- Core features: HTTP server, image engine, URL parsing, filters, loaders, storages, configuration
