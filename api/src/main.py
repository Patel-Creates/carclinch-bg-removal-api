import os
import shutil
from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import sys

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from core import processor

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def get_dirs() -> tuple[Path, Path, Path]:
    """
    Default behavior: saves under ./images.
    Tests can override with IMAGE_BASE_DIR.
    """
    base_dir = Path(os.environ.get("IMAGE_BASE_DIR") or "images")
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    return base_dir, input_dir, output_dir


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/upload-image")
def upload_image(image: UploadFile = File(...)):
    if not (image.content_type and image.content_type.startswith("image/")):
        raise HTTPException(status_code=400, detail="File is not an image.")

    original_name = Path(image.filename or "upload")
    ext = original_name.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension.")

    _, input_dir, output_dir = get_dirs()

    input_path = input_dir / original_name.name
    output_name = f"{original_name.stem}_processed.png"
    output_path = output_dir / output_name

    try:
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    finally:
        image.file.close()

    output_img, _ = processor.process_image(
        str(input_path), model_name="isnet-general-use"
    )
    output_img.save(output_path, format="PNG")

    return {
        "input_filename": input_path.name,
        "input_path": str(input_path),
        "output_filename": output_path.name,
        "output_path": str(output_path),
        "message": "Image uploaded and processed successfully",
    }


@app.post("/replace-background")
def replace_background_endpoint(
    image: UploadFile = File(..., description="Car image (foreground)"),
    background: UploadFile = File(..., description="New background image"),
    car_size: float = Form(60, description="Car size as percentage (1-100). Examples: 50=smaller, 60=standard, 80=larger", ge=1, le=100),
    smart_placement: bool = Form(True, description="Enable intelligent ground plane detection"),
):
    """
    Replace the background of a car image with a new background.
    
    This endpoint performs AI-powered background removal on the car image,
    then intelligently composites it onto a new background with proper scaling
    and ground plane detection.
    """
    # Convert percentage to decimal (60 -> 0.6)
    car_size_decimal = car_size / 100.0
    
    # Content Type Validation
    for file in [image, background]:
        if not (file.content_type and file.content_type.startswith("image/")):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} is not a valid image."
            )

    # Type-Safe Filename Handling
    fg_filename_str = image.filename or "foreground_upload"
    bg_filename_str = background.filename or "background_upload"

    # Directory and Path Setup
    _, input_dir, output_dir = get_dirs()

    # Create safe Path objects
    fg_path = input_dir / f"fg_{fg_filename_str}"
    bg_path = input_dir / f"bg_{bg_filename_str}"

    # Generate output filename
    output_name = f"replaced_{Path(fg_filename_str).stem}.png"
    output_path = output_dir / output_name

    try:
        # Save uploaded files to the input directory
        with fg_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        with bg_path.open("wb") as buffer:
            shutil.copyfileobj(background.file, buffer)

        # Call the core library processing function with smart placement
        result_img = processor.replace_background(
            foreground_input=str(fg_path),
            background_input=str(bg_path),
            model_name="isnet-general-use",
            normalize=True,
            target_car_ratio=car_size_decimal,
            smart_placement=smart_placement,
        )

        # Save the final composited image
        result_img.save(output_path, format="PNG")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )
    finally:
        image.file.close()
        background.file.close()

    return {
        "input_foreground": fg_path.name,
        "input_background": bg_path.name,
        "output_filename": output_path.name,
        "output_path": str(output_path),
        "car_size_percentage": f"{car_size}%",
        "smart_placement_enabled": smart_placement,
        "message": "Background replaced successfully with intelligent scaling and positioning",
    }


@app.get("/output/{filename}")
def get_output(filename: str):
    """Serve processed output images"""
    _, _, output_dir = get_dirs()
    file_path = output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="image/png")