"""
Abstract base pipeline for document processing.
Defines common interface for all document pipelines.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from PIL import Image
import time


class BasePipeline(ABC):
    """
    Abstract base class for document processing pipelines.
    All document-specific pipelines must inherit from this.
    """
    
    def __init__(self):
        """Initialize pipeline. Override to load models."""
        self.warnings: List[str] = []
    
    @abstractmethod
    def process(self, image: Image.Image) -> Dict[str, Any]:
        """
        Process document image and extract structured data.
        
        Args:
            image: PIL Image object
        
        Returns:
            Dictionary with extracted fields
        
        Raises:
            Should raise appropriate exceptions (e.g., HTTPException)
        """
        pass
    
    def run(self, image: Image.Image) -> Dict[str, Any]:
        """
        Main pipeline execution with timing and error handling.
        
        Args:
            image: PIL Image object
        
        Returns:
            Complete response with fields, timing, and warnings
        """
        start_time = time.time()
        self.warnings = []  # Reset warnings
        
        try:
            # Run document-specific processing
            fields = self.process(image)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            return {
                "fields": fields,
                "processing_time_ms": round(processing_time_ms, 2),
                "warnings": self.warnings,
                "metadata": self._get_metadata()
            }
        
        except Exception:
            # Let exceptions propagate - they'll be handled by FastAPI
            raise
    
    def add_warning(self, message: str) -> None:
        """Add a non-critical warning to pipeline results."""
        self.warnings.append(message)
    
    def _get_metadata(self) -> Dict[str, Any]:
        """
        Get pipeline-specific metadata.
        Override in subclasses to add custom metadata.
        """
        return {}
    
    @staticmethod
    def _create_field_dict(value: str, confidence: float, bbox: List[float] = None) -> Dict[str, Any]:
        """
        Helper to create standardized field dictionary.
        
        Args:
            value: Extracted text value
            confidence: Confidence score (0-1)
            bbox: Optional bounding box [x1, y1, x2, y2]
        
        Returns:
            Standardized field dictionary
        """
        field = {
            "value": value,
            "confidence": round(confidence, 3)
        }
        
        if bbox:
            field["bbox"] = [round(coord, 2) for coord in bbox]
        
        return field