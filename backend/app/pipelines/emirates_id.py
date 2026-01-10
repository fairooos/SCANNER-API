"""
Emirates ID processing pipeline.
Uses YOLO for field detection + EasyOCR for text extraction.
"""
from typing import Dict, Any
from PIL import Image
import easyocr
from ultralytics import YOLO
from pathlib import Path
from fastapi import HTTPException, status

from app.pipelines.base import BasePipeline
from app.utils.normalization import (
    normalize_text, normalize_name, normalize_date,
    normalize_emirates_id, normalize_sex, normalize_nationality
)
from app.utils.validation import (
    validate_emirates_id_number, validate_date_consistency, validate_sex
)
from app.utils.image import preprocess_for_ocr


class EmiratesIDPipeline(BasePipeline):
    """
    Pipeline for processing Emirates ID cards.
    
    Architecture:
    1. YOLO detects field bounding boxes
    2. EasyOCR extracts text from each detected region
    3. Text is normalized and validated
    4. Structured response is returned
    """
    
    def __init__(self):
        super().__init__()
        self._load_models()
    
    def _load_models(self):
        """Load YOLO and EasyOCR models. Called once at initialization."""
        try:
            # Load YOLO model
            # Hardcoded path as per fixed format requirement
            model_path = Path("models/best.pt")
            if not model_path.exists():
                raise RuntimeError(f"YOLO model not found at {model_path}")
            
            self.yolo_model = YOLO(str(model_path))
            
            # Load EasyOCR reader
            # Hardcoded settings as per fixed format requirement
            self.ocr_reader = easyocr.Reader(
                ['en'],
                gpu=False
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to load models: {str(e)}")
    
    def process(self, image: Image.Image) -> Dict[str, Any]:
        """
        Process Emirates ID image.
        
        Args:
            image: PIL Image of Emirates ID
        
        Returns:
            Dictionary of extracted fields with confidence scores
        """
        # Step 1: Run YOLO detection
        detections = self._detect_fields(image)
        try:
            if not detections:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No Emirates ID fields detected. Please ensure the image is clear and contains an Emirates ID."
                )
            
            # Step 2: Extract text from each detected region
            fields = self._extract_text_from_detections(image, detections)
            
            # Step 3: Normalize extracted text
            fields = self._normalize_fields(fields)
            
            # Step 4: Validate fields
            self._validate_fields(fields)
            
            return fields
        except HTTPException:
            raise
        except Exception as e:
            # log the real error
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during Emirates ID processing"
            ) from e
    
    def _detect_fields(self, image: Image.Image) -> Dict[str, Dict[str, Any]]:
        """
        Run YOLO inference to detect field bounding boxes.
        
        Returns:
            Dict mapping field names to {bbox, confidence}
        """
        # Run inference
        # Hardcoded confidence threshold
        MIN_DETECTION_CONFIDENCE = 0.3
        
        results = self.yolo_model.predict(
            image,
            conf=MIN_DETECTION_CONFIDENCE,
            verbose=False
        )
        
        detections = {}
        
        # Parse results (first result since we process one image)
        if len(results) > 0:
            result = results[0]
            
            # Extract boxes and classes
            boxes = result.boxes
            
            for i in range(len(boxes)):
                # Get class name
                class_id = int(boxes.cls[i])
                class_name = result.names[class_id]
                
                # Get bounding box (xyxy format)
                bbox = boxes.xyxy[i].cpu().numpy().tolist()
                
                # Get confidence
                confidence = float(boxes.conf[i])
                
                # Store detection (only keep highest confidence if duplicate)
                if class_name not in detections or confidence > detections[class_name]['confidence']:
                    detections[class_name] = {
                        'bbox': bbox,
                        'confidence': confidence
                    }
        
        return detections
    
    def _extract_text_from_detections(
        self,
        image: Image.Image,
        detections: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run OCR on each detected field region.
        
        Returns:
            Dict of field names to extraction results
        """
        fields = {}
        
        for field_name, detection in detections.items():
            bbox = detection['bbox']
            detection_conf = detection['confidence']
            
            # Preprocess region for OCR
            region = preprocess_for_ocr(image, bbox)
            
            # Run OCR
            ocr_results = self.ocr_reader.readtext(region)
            
            # Combine OCR results (concatenate all detected text)
            if ocr_results:
                # Sort by vertical position (top to bottom)
                ocr_results.sort(key=lambda x: x[0][0][1])
                
                # Extract text and average confidence
                texts = [result[1] for result in ocr_results]
                confidences = [result[2] for result in ocr_results]
                
                combined_text = ' '.join(texts)
                avg_confidence = sum(confidences) / len(confidences)
                
                # Combine detection and OCR confidence
                # Using geometric mean to penalize low confidence in either stage
                final_confidence = (detection_conf * avg_confidence) ** 0.5
                
                # Check if confidence is acceptable
                # Hardcoded OCR confidence threshold
                MIN_OCR_CONFIDENCE = 0.5
                
                if final_confidence < MIN_OCR_CONFIDENCE:
                    self.add_warning(
                        f"Low confidence ({final_confidence:.2f}) for field: {field_name}"
                    )
                
                fields[field_name] = self._create_field_dict(
                    value=combined_text,
                    confidence=final_confidence,
                    bbox=bbox
                )
            else:
                # No text detected in region
                self.add_warning(f"No text detected in field: {field_name}")
                fields[field_name] = self._create_field_dict(
                    value="",
                    confidence=0.0,
                    bbox=bbox
                )
        
        return fields
    
    def _normalize_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field-specific normalization."""
        normalization_map = {
            'id_number': normalize_emirates_id,
            'full_name': normalize_name,
            'date_of_birth': normalize_date,
            'nationality': normalize_nationality,
            'sex': normalize_sex,
            'issue_date': normalize_date,
            'expiry_date': normalize_date
        }
        
        for field_name, field_data in fields.items():
            if field_name in normalization_map and field_data['value']:
                normalizer = normalization_map[field_name]
                normalized_value = normalizer(field_data['value'])
                
                # Update value if normalization succeeded
                if normalized_value:
                    field_data['value'] = normalized_value
        
        return fields
    
    def _validate_fields(self, fields: Dict[str, Any]) -> None:
        """
        Validate extracted fields.
        Adds warnings for validation failures (non-blocking).
        """
        # Validate Emirates ID format
        if 'id_number' in fields and fields['id_number']['value']:
            is_valid, error = validate_emirates_id_number(fields['id_number']['value'])
            if not is_valid:
                self.add_warning(f"ID validation: {error}")
        
        # Validate date consistency
        issue_date = fields.get('issue_date', {}).get('value')
        expiry_date = fields.get('expiry_date', {}).get('value')
        
        if issue_date and expiry_date:
            is_valid, error = validate_date_consistency(issue_date, expiry_date)
            if not is_valid:
                self.add_warning(f"Date validation: {error}")
        
        # Validate sex
        if 'sex' in fields and fields['sex']['value']:
            is_valid, error = validate_sex(fields['sex']['value'])
            if not is_valid:
                self.add_warning(f"Sex validation: {error}")
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Return pipeline-specific metadata."""
        return {
            "model": "YOLO + EasyOCR",
            "yolo_model_path": "models/best.pt"
        }