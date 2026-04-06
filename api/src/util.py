from pathlib import Path

from fastapi import HTTPException, UploadFile

from src.constants import ALLOWED_EXTENSIONS
from core import processor


def validate_uploaded_image(file: UploadFile) -> Path:
    if not (file.content_type and file.content_type.startswith("image/")):
        raise HTTPException(
            status_code=400,
            detail=f"File {file.filename} is not a valid image."
        )

    filename = Path(file.filename or "upload")
    if filename.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension for {filename.name}."
        )

    return filename


def process_model_replacement(
    model_name: str,
    fg_path: Path,
    bg_path: Path,
    output_dir: Path,
    car_size_decimal: float,
    smart_placement: bool,
):
    output_name = f"{fg_path.stem}_{model_name}_replaced.png"
    output_path = output_dir / output_name

    result_img = processor.replace_background(
        foreground_input=str(fg_path),
        background_input=str(bg_path),
        model_name=model_name,
        normalize=True,
        target_car_ratio=car_size_decimal,
        smart_placement=smart_placement,
    )
    result_img.save(output_path, format="PNG")

    return {
        "model": model_name,
        "status": "success",
        "output_filename": output_path.name,
        "output_path": str(output_path),
        "output_url": f"/output/{output_path.name}",
    }