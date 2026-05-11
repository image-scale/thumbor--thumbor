# Acceptance Criteria

## Task 1: Implement the image processing engine
(Completed - 14/14 criteria met)

## Task 2: Add focal point support for smart cropping

### Acceptance Criteria
- [ ] FocalPoint can be created with x, y coordinates and optional width, height, weight
- [ ] FocalPoint can compute center coordinates from a bounding box (from_square)
- [ ] FocalPoint can compute coordinates from alignment strings like "left", "center", "right" for horizontal and "top", "middle", "bottom" for vertical
- [ ] FocalPoint can serialize to a dictionary with all properties
- [ ] FocalPoint can deserialize from a dictionary
- [ ] Calculate center of mass from multiple weighted focal points
- [ ] Given a list of focal points and target dimensions, calculate optimal crop coordinates that preserve focal areas
- [ ] Support default alignment-based focal point when no explicit points are provided
- [ ] FocalPoint has a string representation for debugging
