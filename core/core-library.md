# Core Background Removal Library

This library provides a unified, type-safe interface for
removing image backgrounds using [rembg](https://github.com/danielgatis/rembg).
Provides session management, image processing, and background replacement
utilities.

## Requirements

- Python 3.8+
- `rembg`
- `Pillow`
- `numpy`

## Overview

The library is built around two main responsibilities:

1. **Session management** — loading and caching rembg models efficiently to
   avoid redundant VRAM/RAM usage.
2. **Image processing** — removing backgrounds from images and compositing them
   onto new ones.

## API Reference

### `get_session(model_name: str)`

Loads and caches a rembg model session Uses an LRU cache with `maxsize=1`, so
loading a new model automatically evicts the previous one to free resources.
This can be changed to allow multiple models to be cached at the same time but
would require more resources.

```python
session = get_session("u2net")
```

**Parameters**

| Name | Type | Description |
| -------------- | --------------- | --------------- |
| `model_name` | `str` | The rembg model to load (e.g. `"u2net"`, `"isnet-general-use"`) |

**Returns** — a rembg session object.

---

### `process_image(input_data, model_name, max_size=(1024, 1024))`

The primary entry point for background removal. Accepts a file path or a PIL
Image, optionally resizes it, removes the background, and returns both the
result image and a foreground mask.

```python
from PIL import Image
output_img, mask = process_image("car.jpg", "u2net")

# Or pass a PIL Image directly
img = Image.open("car.jpg")
output_img, mask = process_image(img, "u2net", max_size=(800, 800))
```

**Parameters**

| Name | Type | Default | Description |
| -------------- | --------------- | --------------- | --------------- |
| `input_data` | `str \| Path \| Image.Image` | — | Input image (path or PIL Image) |
| `model_name` | `str` | — | rembg model to use |
| `max_size` | `tuple[int, int] \| None` | `(1024, 1024)` | If set, downscales images exceeding these dimensions before processing. Set to `None` to disable. |

**Returns** — a tuple of `(Image.Image, np.ndarray)`:

- `Image.Image` — RGBA image with the background removed.
- `np.ndarray` — Boolean mask where `True` indicates foreground pixels.

---

### `replace_background(foreground_input, background_input, model_name)`

High-level convenience function. Removes the background from a foreground image
and composites it onto a new background in one call.

```python
result = replace_background(
    foreground_input="car.jpg",
    background_input="studio.jpg",
    model_name="u2net",
)
result.save("output.jpg")
```

**Parameters**

| Name | Type | Default | Description |
| -------------- | --------------- | --------------- | --------------- |
| `foreground_input` | `str \| Path \| Image.Image` | — | The subject image to extract |
| `background_input` | `str \| Path \| Image.Image` | — | The new background image |
| `model_name` | `str` | — | rembg model to use |
| `max_size` | `tuple[int, int] \| None` | `(1024, 1024)` | Max dimensions for background removal processing |
| `normalize` | `bool` | `True` | If `True`, scales and positions the subject intelligently on the background |
| `target_car_ratio` | `float` | `0.6` | Target proportion of the frame the subject should occupy (0.0–1.0) |
| `smart_placement` | `bool` | `True` | If `True`, uses ground-plane detection for scene-aware positioning. Only applies when `normalize=True`. |

**Returns** — an RGB `Image.Image` with the new background applied.

---

### `clear_sessions()`

Explicitly clears the model cache to release VRAM/RAM. Useful when switching
models or shutting down.

```python
clear_sessions()
```

---

## Notes

**Model caching** — `get_session` was originally designed to be able to cache
multiple models at a time. Due to current resource constraints only one model
is held in memory at a time. Calling it with a different `model_name` than the
currently cached one will evict the old model before loading the new one.

**`max_size` and quality** — Reducing `max_size` speeds up processing but may
reduce mask quality on fine details (e.g. hair, thin edges). For best results
on high-resolution inputs, increase or disable the limit.

**`normalize=False`** — Disables all scaling and placement logic. The
background is resized to match the foreground image dimensions and the
two are alpha-composited directly.
