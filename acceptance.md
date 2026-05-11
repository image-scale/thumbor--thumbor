# Acceptance Criteria

## Task 1-3: (Completed)

## Task 4: Add URL parsing to extract transformation parameters

### Acceptance Criteria
- [ ] Parse URL path /unsafe/300x200/http://example.com/image.jpg to extract dimensions and image URL
- [ ] Parse fit-in mode from URL /unsafe/fit-in/300x200/image.jpg
- [ ] Parse smart mode from URL /unsafe/300x200/smart/image.jpg
- [ ] Parse crop coordinates from URL /unsafe/10x20:90x80/300x200/image.jpg
- [ ] Parse horizontal flip from -300x200 (negative width)
- [ ] Parse vertical flip from 300x-200 (negative height)
- [ ] Parse alignment from URL /unsafe/300x200/left/top/image.jpg
- [ ] Parse filters from URL /unsafe/filters:blur(5):grayscale()/image.jpg
- [ ] Parse hash signature from URL /HASH/300x200/image.jpg
- [ ] Handle URL-encoded image URLs
- [ ] Build regex pattern that matches valid image processing URLs
- [ ] Return RequestParams object with all extracted values
