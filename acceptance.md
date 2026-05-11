# Acceptance Criteria

## Task 1: Implement the image processing engine
(Completed - 14/14 criteria met)

## Task 2: Add focal point support for smart cropping
(Completed - 9/9 criteria met)

## Task 3: Add request parameter handling

### Acceptance Criteria
- [ ] RequestParams stores image width and height (int or "orig" for original)
- [ ] RequestParams stores crop coordinates (left, top, right, bottom)
- [ ] RequestParams stores fit_in mode for fit-within-box resizing
- [ ] RequestParams stores horizontal_flip and vertical_flip booleans
- [ ] RequestParams stores halign ("left", "center", "right") and valign ("top", "middle", "bottom")
- [ ] RequestParams stores smart mode boolean for AI-based cropping
- [ ] RequestParams stores quality setting (1-100)
- [ ] RequestParams stores filter string (e.g., "blur(5):brightness(-10)")
- [ ] RequestParams stores image_url for the source image
- [ ] RequestParams computes should_crop boolean based on crop coordinates
- [ ] RequestParams stores focal_points list
- [ ] RequestParams supports "unsafe" mode flag
- [ ] RequestParams handles adaptive mode that swaps dimensions based on image orientation
