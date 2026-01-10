"""
Passport scanning endpoint.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.responses import ScanResponse, ErrorResponse
from app.pipelines.passport import PassportPipeline
from app.utils.image import validate_file_upload, load_image_from_bytes

router = APIRouter()

# Singleton pipeline instance
_pipeline = None


def get_pipeline() -> PassportPipeline:
    """Get or create pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = PassportPipeline()
    return _pipeline


@router.post(
    "/scan",
    response_model=ScanResponse,
    summary="Scan Passport",
    description="Extract structured information from passport image (MRZ-based)",
    responses={
        200: {"model": ScanResponse},
        400: {"model": ErrorResponse, "description": "Invalid file type or format"},
        413: {"model": ErrorResponse, "description": "File too large"},
        422: {"model": ErrorResponse, "description": "Processing error (MRZ not found/parsed)"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def scan_passport(
    file: UploadFile = File(..., description="Passport image (JPG, PNG)")
):
    """
    Scan passport and extract MRZ fields.
    
    This endpoint:
    1. Validates the uploaded file
    2. Detects and reads MRZ using passporteye
    3. Parses MRZ according to ICAO 9303
    4. Validates checksums
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
            document_type="passport",
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
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during passport processing"
        )