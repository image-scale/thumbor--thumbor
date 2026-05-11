# Progress

(Updated after each feature commit.)

## Round 1
**Task**: Task 1 — Implement the image processing engine
**Files created**: imgsvc/__init__.py, imgsvc/engines/__init__.py, imgsvc/engines/pil_engine.py, tests/test_engine.py, pyproject.toml
**Commit**: Add an image processing engine that loads images from bytes, performs transformations, and outputs to various formats.
**Acceptance**: 14/14 criteria met
**Verification**: tests FAIL on previous state (import error), PASS on current state

## Round 2
**Task**: Task 2 — Add focal point support for smart cropping
**Files created**: imgsvc/focal.py, tests/test_focal.py
**Commit**: Add focal point support for smart cropping
**Acceptance**: 9/9 criteria met
**Verification**: tests FAIL on previous state (ModuleNotFoundError), PASS on current state

## Round 3
**Task**: Task 3 — Add request parameter handling
**Files created**: imgsvc/request_params.py, tests/test_request_params.py
**Commit**: Add request parameter handling for image transformations
**Acceptance**: 13/13 criteria met
**Verification**: tests FAIL on previous state (ModuleNotFoundError), PASS on current state

## Round 4
**Task**: Task 4 — Add URL parsing
**Files created**: imgsvc/url_parser.py, tests/test_url_parser.py
**Commit**: Add URL parsing to extract transformation parameters from request paths
**Acceptance**: 12/12 criteria met
**Verification**: tests FAIL on previous state (ModuleNotFoundError), PASS on current state
