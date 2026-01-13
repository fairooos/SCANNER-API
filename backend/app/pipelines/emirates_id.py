from typing import Dict, Any
from PIL import Image
import easyocr
import traceback
from ultralytics import YOLO
from pathlib import Path
from fastapi import HTTPException, status

from app.pipelines.base import BasePipeline
from app.utils.normalization import (
    normalize_text, normalize_name, normalize_date,
    normalize_emirates_id, normalize_sex, normalize_nationality
)
from app.utils.validation import (
    validate_emirates_id_number, validate_date_consistency, validate_sex, 
)
from app.utils.image import preprocess_for_ocr


class EmiratesIDPipeline(BasePipeline):
   
    
    def __init__(self):
        super().__init__()
        self._load_models()
    
    def _load_models(self):
        
        try:
            
            model_path = Path("models/best.pt")
            if not model_path.exists():
                raise RuntimeError(f"YOLO model not found at {model_path}")
            
            self.yolo_model = YOLO(str(model_path))
            
            
            self.ocr_reader = easyocr.Reader(
                ['en'],
                gpu=False
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to load models: {str(e)}")
    
    def process(self, image: Image.Image) -> Dict[str, Any]:
        
        
        detections = self._detect_fields(image)
        try:
            if not detections:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No Emirates ID fields detected. Please ensure the image is clear and contains an Emirates ID."
                )
            
            
            fields = self._extract_text_from_detections(image, detections)
            
        
            fields = self._normalize_fields(fields)
            
        
            self._validate_fields(fields)
            
            return fields
        except HTTPException:
            raise
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    
    def _detect_fields(self, image: Image.Image) -> Dict[str, Dict[str, Any]]:
        
       
        MIN_DETECTION_CONFIDENCE = 0.3
        
        results = self.yolo_model.predict(
            image,
            conf=MIN_DETECTION_CONFIDENCE,
            verbose=False
        )
        
        detections = {}
        
        
        if len(results) > 0:
            result = results[0]
            boxes = result.boxes
            
            for i in range(len(boxes)):
               
                class_id = int(boxes.cls[i])
                class_name = result.names[class_id]
             
                bbox = boxes.xyxy[i].cpu().numpy().tolist()
                
                confidence = float(boxes.conf[i])
                
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
       
        fields = {}
        
        for field_name, detection in detections.items():
            bbox = detection['bbox']
            detection_conf = detection['confidence']
            
            
            region = preprocess_for_ocr(image, bbox)
            
            
            ocr_results = self.ocr_reader.readtext(region)
            
            
            if ocr_results:
                
                ocr_results.sort(key=lambda x: x[0][0][1])
                
           
                texts = [result[1] for result in ocr_results]
                confidences = [result[2] for result in ocr_results]
                
                combined_text = ' '.join(texts)
                avg_confidence = sum(confidences) / len(confidences)
                

                final_confidence = (detection_conf * avg_confidence) ** 0.5
                
                
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
                
                self.add_warning(f"No text detected in field: {field_name}")
                fields[field_name] = self._create_field_dict(
                    value="",
                    confidence=0.0,
                    bbox=bbox
                )
        
        return fields
    
    def _normalize_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
       
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
                
              
                if normalized_value:
                    field_data['value'] = normalized_value
        
        return fields
    
    def _validate_fields(self, fields: Dict[str, Any]) -> None:
        
       
        if 'id_number' in fields and fields['id_number']['value']:
            is_valid, error = validate_emirates_id_number(fields['id_number']['value'])
            if not is_valid:
                self.add_warning(f"ID validation: {error}")
        
        
        issue_date = fields.get('issue_date', {}).get('value')
        expiry_date = fields.get('expiry_date', {}).get('value')
        
        if issue_date and expiry_date:
            is_valid, error = validate_date_consistency(issue_date, expiry_date)
            if not is_valid:
                self.add_warning(f"Date validation: {error}")

        if 'sex' in fields and fields['sex']['value']:
            is_valid, error = validate_sex(fields['sex']['value'])
            if not is_valid:
                self.add_warning(f"Sex validation: {error}")
    
    def _get_metadata(self) -> Dict[str, Any]:
        
        return {
            "model": "YOLO + EasyOCR",
            "yolo_model_path": "models/best.pt"
        }