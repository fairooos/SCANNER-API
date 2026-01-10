"""
Emirates ID scanning endpoint.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.responses import ScanResponse, ErrorResponse
from app.pipelines.emirates_id import EmiratesIDPipeline
from app.utils.image import validate_file_upload, load_image_from_bytes

router = APIRouter()

# Singleton pipeline instance (loaded once, reused across requests)
# This is efficient because model loading is expensive
_pipeline = None


def get_pipeline() -> EmiratesIDPipeline:
    """Get or create pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = EmiratesIDPipeline()
    return _pipeline


@router.post(
    "/scan",
    response_model=ScanResponse,
    summary="Scan Emirates ID",
    description="Extract structured information from Emirates ID card image",
    responses={
        200: {"model": ScanResponse},
        400: {"model": ErrorResponse, "description": "Invalid file type or format"},
        413: {"model": ErrorResponse, "description": "File too large"},
        422: {"model": ErrorResponse, "description": "Processing error"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def scan_emirates_id(
    file: UploadFile = File(..., description="Emirates ID image (JPG, PNG)")
):
    """
    Scan Emirates ID and extract fields.
    
    This endpoint:
    1. Validates the uploaded file
    2. Detects fields using YOLO
    3. Extracts text using EasyOCR
    4. Normalizes and validates data
    5. Returns structured response
    """
    try:
        # Read file
        file_content = await file.read()
        
        # Validate file
        validate_file_upload(file.filename, len(file_content))
        
        # Load image
        image = load_image_from_bytes(file_content)
        
        # Get pipeline and process
        pipeline = get_pipeline()
        result = pipeline.run(image)
        
        # Return response
        return ScanResponse(
            document_type="emirates_id",
            fields=result["fields"],
            processing_time_ms=result["processing_time_ms"],
            warnings=result["warnings"],
            metadata=result["metadata"]
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Catch-all for unexpected errors
        # In production, log this with proper logging framework
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during Emirates ID processing"
        )