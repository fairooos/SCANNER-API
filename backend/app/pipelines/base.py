
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from PIL import Image
import time


class BasePipeline(ABC):
    
    
    def __init__(self):
       
        self.warnings: List[str] = []
    
    @abstractmethod
    def process(self, image: Image.Image) -> Dict[str, Any]:
        
        pass
    
    def run(self, image: Image.Image) -> Dict[str, Any]:
        
        start_time = time.time()
        self.warnings = []  
        
        try:
            
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
            
            raise
    
    def add_warning(self, message: str) -> None:
        """Add a non-critical warning to pipeline results."""
        self.warnings.append(message)
    
    def _get_metadata(self) -> Dict[str, Any]:
        return {}
    
    @staticmethod
    def _create_field_dict(value: str, confidence: float, bbox: List[float] = None) -> Dict[str, Any]:
        
        field = {
            "value": value,
            "confidence": round(confidence, 3)
        }
        
        if bbox:
            field["bbox"] = [round(coord, 2) for coord in bbox]
        
        return field