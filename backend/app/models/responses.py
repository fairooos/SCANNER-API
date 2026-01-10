"""
Pydantic response models for API endpoints.
Ensures type safety and automatic OpenAPI documentation.
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any
from datetime import datetime


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current server time")
    version: str = Field(..., description="API version")


class FieldExtraction(BaseModel):
    """Individual field extraction result"""
    value: Optional[str] = Field(None, description="Extracted value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [x1, y1, x2, y2]")


class EmiratesIDFields(BaseModel):
    """Structured Emirates ID fields"""
    id_number: Optional[FieldExtraction] = None
    full_name: Optional[FieldExtraction] = None
    date_of_birth: Optional[FieldExtraction] = None
    nationality: Optional[FieldExtraction] = None
    sex: Optional[FieldExtraction] = None
    issue_date: Optional[FieldExtraction] = None
    expiry_date: Optional[FieldExtraction] = None


class PassportFields(BaseModel):
    """Structured Passport fields"""
    full_name: Optional[FieldExtraction] = None
    passport_number: Optional[FieldExtraction] = None
    nationality: Optional[FieldExtraction] = None
    date_of_birth: Optional[FieldExtraction] = None
    sex: Optional[FieldExtraction] = None
    expiry_date: Optional[FieldExtraction] = None


class ScanResponse(BaseModel):
    """Unified scan response for both document types"""
    document_type: str = Field(..., description="Type of document: 'emirates_id' or 'passport'")
    fields: Dict[str, Any] = Field(..., description="Extracted fields with confidence scores")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "emirates_id",
                "fields": {
                    "id_number": {
                        "value": "784-1234-1234567-1",
                        "confidence": 0.95,
                        "bbox": [100, 200, 300, 250]
                    }
                },
                "processing_time_ms": 1234.56,
                "warnings": [],
                "metadata": {}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Error type identifier")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())