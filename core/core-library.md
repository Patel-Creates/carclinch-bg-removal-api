# Core Background Removal Library

This library provides a unified, type-safe interface for
removing image backgrounds using various AI models. It is
designed to be the "single source of truth" for both
production APIs and internal evaluation tools.

## Quick Start

### Basic Usage

```python
from core import processor

# Process an image file
output_img, mask = processor.process_image("input.jpg", model_name="u2net")

# Save the transparent result
output_img.save("result.png")
```

### Integration with FastAPI

```python
from fastapi import FastAPI, UploadFile
from core import processor
from PIL import Image
import io

app = FastAPI()

@app.post("/remove")
async def remove_bg(file: UploadFile):
    # Load upload into memory
    input_data = Image.open(io.BytesIO(await file.read()))
    
    # Process using the library
    result_img, _ = processor.process_image(input_data, model_name="isnet-general-use")
    
    # ... return response ...
```

## Key Function

`process_image(...)`

The primary method for background removal.

| Argument | Type | Description |
| --------------- | --------------- | --------------- |
| `input_data` | `str \| Path \| Image` | The source image (path or PIL object). |
| `model_name` | `str` | The ID of the model to use (e.g., `u2net`, `sam`). |
| `max_size` | `str` | (Optional) Max dimensions `(W, H)`. Defaults to `(1024, 1024)`. |

*Returns:* `(PIL.Image, np.ndarray)` containing the RGBA image and a boolean mask.
