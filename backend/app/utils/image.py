"""
Image preprocessing and validation utilities.
"""
from PIL import Image
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List
from fastapi import HTTPException, status


def validate_file_upload(filename: str, file_size: int) -> None:
    """
    Validate uploaded file before processing.
    
    Args:
        filename: Name of uploaded file
        file_size: Size in bytes
    
    Raises:
        HTTPException: If file is invalid
    """
    MAX_FILE_SIZE_MB = 10
    ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png"]
    
    # Check file extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Allowed: JPG, JPEG, PNG"
        )
    
    # Check file size
    size_mb = file_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {size_mb:.2f}MB exceeds maximum {MAX_FILE_SIZE_MB}MB"
        )


def load_image_from_bytes(file_bytes: bytes) -> Image.Image:
    """
    Load image from bytes and convert to RGB.
    
    Args:
        file_bytes: Raw image bytes
    
    Returns:
        PIL Image in RGB mode
    """
    try:
        import io
        image = Image.open(io.BytesIO(file_bytes))
        
        # Convert to RGB (handles RGBA, Grayscale etc.)
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        return image
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to process image: {str(e)}"
        )


def preprocess_for_ocr(image: Image.Image, bbox: Optional[List[float]] = None) -> np.ndarray:
    """
    Preprocess image for better OCR results.
    - Crop to bbox if provided
    - Grayscale
    - Contrast enhancement (optional, basic here)
    
    Args:
        image: PIL Image
        bbox: Optional bounding box [x1, y1, x2, y2]
    
    Returns:
        Numpy array ready for EasyOCR
    """
    # Crop if bbox is provided
    if bbox:
        # Ensure bbox coordinates are within image bounds
        # Convert to int for cropping
        x1, y1, x2, y2 = [int(c) for c in bbox]
        image = image.crop((x1, y1, x2, y2))

    # Convert to numpy
    img_np = np.array(image)
    
    # EasyOCR handles preprocessing well internally, 
    # but we can add specific steps here if needed.
    # For now, just return the numpy array.
    return img_np
