# Acceptance Criteria

## Tasks 1-4: (Completed)

## Task 5: Add the image transformation coordinator

### Acceptance Criteria
- [ ] Transformer takes an engine and request parameters
- [ ] Apply manual crop first if coordinates are provided
- [ ] Calculate target dimensions based on request width/height or original
- [ ] Adjust focal points relative to crop region if manual crop was applied
- [ ] Create default focal point from alignment if no explicit focal points
- [ ] Auto-crop to achieve target aspect ratio while preserving focal points
- [ ] Resize image to target dimensions after cropping
- [ ] Apply horizontal and vertical flips if requested
- [ ] Support fit-in mode that scales to fit within box without cropping
- [ ] Support full-fit-in mode that scales to fill the box
- [ ] Handle "orig" dimensions to preserve original size on that axis
