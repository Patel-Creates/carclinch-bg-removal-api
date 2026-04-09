import os
import shutil
from pathlib import Path
import sys

from dotenv import load_dotenv

from util import process_model_replacement, validate_uploaded_image

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from blob_storage import upload_file_to_blob, download_blob_bytes
from constants import ALLOWED_EXTENSIONS, SUPPORTED_MODELS
from core import processor

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    car_size: float = Form(
        60,
        description="Car size as percentage (1-100). Examples: 50=smaller, 60=standard, 80=larger",
        ge=1,
        le=100,
    ),
    smart_placement: bool = Form(
        True,
        description="Enable intelligent ground plane detection",
    ),
):
    car_size_decimal = car_size / 100.0

    for file in [image, background]:
        if not (file.content_type and file.content_type.startswith("image/")):
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} is not a valid image.",
            )

    fg_filename_str = image.filename or "foreground_upload"
    bg_filename_str = background.filename or "background_upload"

    _, input_dir, output_dir = get_dirs()

    fg_path = input_dir / f"fg_{fg_filename_str}"
    bg_path = input_dir / f"bg_{bg_filename_str}"

    output_name = f"replaced_{Path(fg_filename_str).stem}.png"
    output_path = output_dir / output_name

    try:
        with fg_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        with bg_path.open("wb") as buffer:
            shutil.copyfileobj(background.file, buffer)

        result_img = processor.replace_background(
            foreground_input=str(fg_path),
            background_input=str(bg_path),
            model_name="birefnet-general",
            normalize=True,
            target_car_ratio=car_size_decimal,
            smart_placement=smart_placement,
        )

        result_img.save(output_path, format="PNG")
        blob_result = upload_file_to_blob(output_path)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}",
        )
    finally:
        image.file.close()
        background.file.close()

    image_url = f"/images/{blob_result['blob_name']}"

    return {
        "input_foreground": fg_path.name,
        "input_background": bg_path.name,
        "output_filename": output_path.name,
        "output_path": str(output_path),
        "blob_name": blob_result["blob_name"],
        "blob_container": blob_result["container_name"],
        "image_url": image_url,
        "car_size_percentage": f"{car_size}%",
        "smart_placement_enabled": smart_placement,
        "message": "Background replaced successfully and uploaded to blob storage",
    }

@app.post("/replace-background-all-models")
def replace_background_all_models(
    image: UploadFile = File(..., description="Car image (foreground)"),
    background: UploadFile = File(..., description="New background image"),
    car_size: float = Form(
        60,
        description="Car size as percentage (1-100)",
        ge=1,
        le=100,
    ),
    smart_placement: bool = Form(
        True,
        description="Enable intelligent ground plane detection",
    ),
):
    car_size_decimal = car_size / 100.0

    fg_filename = validate_uploaded_image(image)
    bg_filename = validate_uploaded_image(background)

    _, input_dir, output_dir = get_dirs()

    fg_path = input_dir / f"fg_{fg_filename.name}"
    bg_path = input_dir / f"bg_{bg_filename.name}"

    results = []

    try:
        with fg_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        with bg_path.open("wb") as buffer:
            shutil.copyfileobj(background.file, buffer)

        for model_name in SUPPORTED_MODELS:
            try:
                model_result = process_model_replacement(
                    model_name=model_name,
                    fg_path=fg_path,
                    bg_path=bg_path,
                    output_dir=output_dir,
                    car_size_decimal=car_size_decimal,
                    smart_placement=smart_placement,
                )

                blob_result = upload_file_to_blob(Path(model_result["output_path"]))

                results.append(
                    {
                        "model": model_name,
                        "status": "success",
                        "output_filename": model_result["output_filename"],
                        "blob_name": blob_result["blob_name"],
                        "blob_container": blob_result["container_name"],
                        "image_url": f"/images/{blob_result['blob_name']}",
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "model": model_name,
                        "status": "failed",
                        "error": str(e),
                    }
                )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}",
        )
    finally:
        image.file.close()
        background.file.close()

    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count

    return {
        "input_foreground": fg_path.name,
        "input_background": bg_path.name,
        "total_models": len(SUPPORTED_MODELS),
        "successful_models": success_count,
        "failed_models": failed_count,
        "car_size_percentage": f"{car_size}%",
        "smart_placement_enabled": smart_placement,
        "results": results,
        "message": "Multi-model background replacement completed",
    }


@app.get("/images/{blob_name}")
def get_private_image(blob_name: str):
    try:
        blob_data, content_type = download_blob_bytes(blob_name)
        return Response(content=blob_data, media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Image not found: {str(e)}")


@app.get("/output/{filename}")
def get_output(filename: str):
    """Serve processed output images"""
    _, _, output_dir = get_dirs()
    file_path = output_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="image/png")