from pathlib import Path
from typing import Union, Optional, Tuple, cast
import numpy as np
from PIL import Image
from rembg import remove, new_session
from functools import lru_cache


@lru_cache(maxsize=1)
def get_session(model_name: str):
    """
    Maintains a single model session in memory.
    Uses LRU cache with maxsize=1 to ensure that when a new model is loaded,
    the previous one is evicted to free up VRAM/RAM.
    """
    return new_session(model_name)


def process_image(
    input_data: Union[str, Path, Image.Image],
    model_name: str,
    max_size: Optional[Tuple[int, int]] = (1024, 1024),
) -> Tuple[Image.Image, np.ndarray]:
    """
    The primary entry point for background removal.

    This function handles:
    1. Input normalization (Path/String to PIL Image).
    2. Optional resizing for performance consistency.
    3. Background removal via the rembg session.
    4. Type-safe conversion of results into a visual Image and a boolean Mask.

    Returns:
        - A PIL Image (RGBA) with the background removed.
        - A boolean numpy array (Mask) where True indicates foreground.
    """
    # Load image if a path is provided
    if isinstance(input_data, (str, Path)):
        img = Image.open(input_data).convert("RGBA")
    else:
        img = input_data.convert("RGBA")

    # Resize for consistency if max_size is provided
    if max_size:
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

    session = get_session(model_name)

    # rembg.remove returns Union[bytes, Image, ndarray].
    # Since we provide an Image, it returns an Image.
    result = remove(img, session=session)

    # Type Guard for the checker
    if not isinstance(result, Image.Image):
        if isinstance(result, np.ndarray):
            result = Image.fromarray(result)
        else:  # it's bytes
            import io

            result = Image.open(io.BytesIO(result)).convert("RGBA")

    output_img = cast(Image.Image, result)

    # Generate boolean mask from the alpha channel
    alpha = np.array(output_img)[:, :, 3]
    mask = alpha > 0

    return output_img, mask


def detect_ground_plane(background_image: Image.Image) -> Tuple[float, float]:
    """
    Detect where the ground/floor is in the background image.
    
    Returns:
        (vertical_position, scale_factor)
        - vertical_position: NOT USED in new logic (kept for compatibility)
        - scale_factor: how much to adjust car size based on perspective
    """
    # Convert to numpy for analysis
    img_array = np.array(background_image.convert('RGB'))
    height, width = img_array.shape[:2]
    
    # Analyze bottom section
    thirds = height // 3
    bottom_section = img_array[2*thirds:, :]
    bottom_variance = np.var(bottom_section)
    
    # Determine if there's a visible floor
    has_visible_floor = bottom_variance < 1000
    
    if has_visible_floor:
        # Showroom/floor - make car slightly smaller for perspective
        vertical_position = 0.92  # Not used, but kept for compatibility
        scale_factor = 0.9  # 90% of requested size
    else:
        # Outdoor/sky - normal size
        vertical_position = 0.92
        scale_factor = 1.0
    
    return vertical_position, scale_factor


def smart_composite(
    car_image: Image.Image,
    car_mask: np.ndarray,
    background_image: Image.Image,
    target_car_ratio: float = 0.6,
) -> Image.Image:
    """
    Intelligently composites car onto background with scene-aware positioning.
    
    CRITICAL: The car's wheels ALWAYS touch the ground at the same position,
    regardless of car_size. Only the car's scale changes, not its ground position.
    """
    # Detect where the ground is in the background
    ground_position, perspective_scale = detect_ground_plane(background_image)
    
    # Get car bounding box from original mask
    rows = np.any(car_mask, axis=1)
    cols = np.any(car_mask, axis=0)
    
    if not np.any(rows) or not np.any(cols):
        return background_image.convert("RGB")
    
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    
    car_width = x_max - x_min
    car_height = y_max - y_min
    
    target_width, target_height = background_image.size
    
    # Apply perspective scaling (smaller cars in showrooms)
    adjusted_car_ratio = target_car_ratio * perspective_scale
    
    # Calculate scaling factor
    scale_x = (target_width * adjusted_car_ratio) / car_width
    scale_y = (target_height * adjusted_car_ratio) / car_height
    scale_factor = min(scale_x, scale_y)
    
    # Scale the car
    new_car_width = int(car_image.width * scale_factor)
    new_car_height = int(car_image.height * scale_factor)
    
    car_scaled = car_image.resize(
        (new_car_width, new_car_height),
        Image.Resampling.LANCZOS
    )
    
    # Resize background
    bg_resized = background_image.resize(
        (target_width, target_height),
        Image.Resampling.LANCZOS
    ).convert("RGBA")
    
    # CRITICAL: Find where the wheels actually are in the SCALED car
    car_scaled_array = np.array(car_scaled)
    car_scaled_alpha = car_scaled_array[:, :, 3]
    car_scaled_mask = car_scaled_alpha > 0
    
    # Find the actual bottom row of car pixels (wheels)
    if np.any(car_scaled_mask):
        car_rows = np.any(car_scaled_mask, axis=1)
        # Get the last row that has car pixels
        car_bottom_relative = np.where(car_rows)[0][-1]
    else:
        car_bottom_relative = new_car_height - 1
    
    # Center horizontally
    paste_x = (target_width - new_car_width) // 2
    
    # GROUND POSITIONING LOGIC:
    # The ground is at a fixed position in the background (e.g., 92% down)
    # We want the car's wheels (bottom pixels) to sit exactly at that position
    # This should work for ANY car_size value
    
    # Where the ground line is in pixels
    ground_line_y = int(target_height * 0.92)  # 92% down the image
    
    # Position the car so its bottom (wheels) align with the ground line
    paste_y = ground_line_y - car_bottom_relative
    
    # Safety bounds
    paste_x = max(0, min(paste_x, target_width - new_car_width))
    paste_y = max(0, min(paste_y, target_height - new_car_height))
    
    # Composite
    bg_resized.paste(car_scaled, (paste_x, paste_y), car_scaled)
    
    return bg_resized.convert("RGB")


def normalize_and_composite(
    car_image: Image.Image,
    car_mask: np.ndarray,
    background_image: Image.Image,
    target_car_ratio: float = 0.6,
) -> Image.Image:
    """
    Intelligently scales and composites the car onto a new background.
    
    Fixes the perspective/scaling issue by:
    1. Detecting the actual car bounding box from the mask
    2. Scaling the car to occupy a consistent portion of the frame
    3. Centering the car with a slight bottom bias for natural appearance
    
    Args:
        car_image: RGBA image of car with transparent background
        car_mask: Boolean mask of the car (True = car pixels)
        background_image: New background image
        target_car_ratio: How much of the frame the car should occupy (0.0-1.0)
                         Default 0.6 means car takes up 60% of the frame
    
    Returns:
        RGB image with car properly scaled and composited on new background
    """
    # Get car bounding box from mask to find actual car dimensions
    rows = np.any(car_mask, axis=1)
    cols = np.any(car_mask, axis=0)
    
    if not np.any(rows) or not np.any(cols):
        # No car detected in mask, return background as-is
        return background_image.convert("RGB")
    
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    
    car_width = x_max - x_min
    car_height = y_max - y_min
    
    # Use the background dimensions as the target canvas size
    target_width, target_height = background_image.size
    
    # Calculate scaling factor to make car occupy target_car_ratio of the frame
    # Scale based on the dimension that would result in the smaller final size
    # This ensures the car fits within the frame
    scale_x = (target_width * target_car_ratio) / car_width
    scale_y = (target_height * target_car_ratio) / car_height
    scale_factor = min(scale_x, scale_y)
    
    # Calculate new car dimensions
    new_car_width = int(car_image.width * scale_factor)
    new_car_height = int(car_image.height * scale_factor)
    
    # Scale the car image
    car_scaled = car_image.resize(
        (new_car_width, new_car_height),
        Image.Resampling.LANCZOS
    )
    
    # Resize background to target dimensions if needed
    bg_resized = background_image.resize(
        (target_width, target_height),
        Image.Resampling.LANCZOS
    ).convert("RGBA")
    
    # Calculates position to center the car horizontally
    # and position it slightly below center vertically (more natural for car photos)
    paste_x = (target_width - new_car_width) // 2
    paste_y = int((target_height - new_car_height) * 0.55)  # 55% down from top
    
    # Ensure we don't paste outside the canvas
    paste_x = max(0, min(paste_x, target_width - new_car_width))
    paste_y = max(0, min(paste_y, target_height - new_car_height))
    
    # Paste the scaled car onto the background using its alpha channel as mask
    bg_resized.paste(car_scaled, (paste_x, paste_y), car_scaled)
    
    return bg_resized.convert("RGB")


def replace_background(
    foreground_input: Union[str, Path, Image.Image],
    background_input: Union[str, Path, Image.Image],
    model_name: str,
    max_size: Optional[Tuple[int, int]] = (1024, 1024),
    normalize: bool = True,
    target_car_ratio: float = 0.6,
    smart_placement: bool = True,
) -> Image.Image:
    """
    Removes the background from the foreground image and replaces it with
    the provided background image.
    
    Args:
        foreground_input: Car image (path or PIL Image)
        background_input: New background image (path or PIL Image)
        model_name: Model to use for background removal
        max_size: Maximum dimensions for processing
        normalize: If True, intelligently scales car to fit background naturally
        target_car_ratio: How much of frame car should occupy (0.0-1.0)
        smart_placement: If True, detects ground plane and positions car accordingly
    
    Returns:
        RGB image with new background
    """
    # Remove background from car image
    foreground_img, mask = process_image(foreground_input, model_name, max_size)

    # Load background image
    if isinstance(background_input, (str, Path)):
        background_img = Image.open(background_input).convert("RGBA")
    else:
        background_img = background_input.convert("RGBA")

    # Use smart placement if enabled
    if normalize and smart_placement:
        return smart_composite(
            foreground_img,
            mask,
            background_img,
            target_car_ratio
        )
    elif normalize:
        return normalize_and_composite(
            foreground_img,
            mask,
            background_img,
            target_car_ratio
        )
    else:
        # Legacy method: just resize background to match foreground
        background_img = background_img.resize(
            foreground_img.size,
            Image.Resampling.LANCZOS
        )
        combined_img = Image.alpha_composite(background_img, foreground_img)
        return combined_img.convert("RGB")


def clear_sessions():
    """Explicitly clears the model cache to free resources."""
    get_session.cache_clear()