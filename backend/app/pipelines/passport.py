"""
Passport processing pipeline.
Uses passporteye library for MRZ extraction and parsing.
"""
from typing import Dict, Any, Optional
from PIL import Image
from passporteye import read_mrz
import io
from fastapi import HTTPException, status

from app.pipelines.base import BasePipeline
from app.utils.normalization import normalize_name, normalize_date, normalize_sex
from app.utils.validation import validate_passport_number, validate_mrz_checksum


class PassportPipeline(BasePipeline):
    """
    Pipeline for processing passport documents.
    
    Architecture:
    1. Use passporteye to detect and read MRZ
    2. Parse MRZ fields according to ICAO 9303 standard
    3. Validate MRZ checksums
    4. Normalize and structure data
    """
    
    def __init__(self):
        super().__init__()
    
    def process(self, image: Image.Image) -> Dict[str, Any]:
        """
        Process passport image.
        
        Args:
            image: PIL Image of passport
        
        Returns:
            Dictionary of extracted fields with confidence scores
        """
        # Step 1: Extract MRZ
        mrz_data = self._extract_mrz(image)
        
        # Step 2: Parse MRZ into structured fields
        fields = self._parse_mrz_fields(mrz_data)
        
        # Step 3: Normalize fields
        fields = self._normalize_fields(fields)
        
        # Step 4: Validate fields
        self._validate_fields(fields, mrz_data)
        
        return fields
    
    def _extract_mrz(self, image: Image.Image) -> Any:
        """
        Extract MRZ from passport image using passporteye.
        
        Returns:
            MRZ object from passporteye
        
        Raises:
            HTTPException: If MRZ cannot be detected or parsed
        """
        try:
            # Convert PIL Image to bytes for passporteye
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Read MRZ
            mrz = read_mrz(img_byte_arr)
            
            if mrz is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="No MRZ detected in image. Ensure passport MRZ is visible and clear."
                )
            
            # Check if MRZ was successfully parsed
            if not mrz.mrz_type:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="MRZ detected but could not be parsed"
                )
            
            return mrz
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"MRZ extraction failed: {str(e)}"
            )
    
    def _parse_mrz_fields(self, mrz_data) -> Dict[str, Any]:
        """
        Parse MRZ data into structured fields.
        
        passporteye returns fields like:
        - names: surname + given names
        - number: passport number
        - nationality: 3-letter country code
        - date_of_birth: YYMMDD format
        - sex: M/F
        - expiration_date: YYMMDD format
        
        Returns:
            Dictionary of field extractions
        """
        fields = {}
        
        # Confidence is high for MRZ since it's machine-readable
        # We use 0.95 as baseline (not perfect due to potential image quality issues)
        base_confidence = 0.95
        
        # Full name (surname + given names)
        if mrz_data.names:
            full_name = mrz_data.names.replace('<', ' ').strip()
            fields['full_name'] = self._create_field_dict(
                value=full_name,
                confidence=base_confidence
            )
        
        # Passport number (remove < filler characters)
        if mrz_data.number:
            # MRZ uses '<' as filler character - remove it from passport number
            clean_passport_number = mrz_data.number.replace('<', '')
            fields['passport_number'] = self._create_field_dict(
                value=clean_passport_number,
                confidence=base_confidence
            )
        
        # Nationality
        if mrz_data.nationality:
            fields['nationality'] = self._create_field_dict(
                value=mrz_data.nationality,
                confidence=base_confidence
            )
        
        # Date of birth
        if mrz_data.date_of_birth:
            dob = self._parse_mrz_date(mrz_data.date_of_birth)
            if dob:
                fields['date_of_birth'] = self._create_field_dict(
                    value=dob,
                    confidence=base_confidence
                )
        
        # Sex
        if mrz_data.sex:
            fields['sex'] = self._create_field_dict(
                value=mrz_data.sex,
                confidence=base_confidence
            )
        
        # Expiry date
        if mrz_data.expiration_date:
            expiry = self._parse_mrz_date(mrz_data.expiration_date)
            if expiry:
                fields['expiry_date'] = self._create_field_dict(
                    value=expiry,
                    confidence=base_confidence
                )
        
        return fields
    
    def _parse_mrz_date(self, mrz_date: str) -> Optional[str]:
        """
        Parse MRZ date (YYMMDD) to standard format (YYYY-MM-DD).
        
        MRZ dates are in YYMMDD format.
        We need to determine the century (19XX or 20XX).
        Rule: If YY > 50, assume 19YY, else 20YY
        """
        if not mrz_date or len(mrz_date) != 6:
            return None
        
        try:
            year = int(mrz_date[:2])
            month = int(mrz_date[2:4])
            day = int(mrz_date[4:6])
            
            # Determine century
            # This is a reasonable heuristic for passports
            if year > 50:
                full_year = 1900 + year
            else:
                full_year = 2000 + year
            
            return f"{full_year:04d}-{month:02d}-{day:02d}"
        
        except ValueError:
            return None
    
    def _normalize_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field-specific normalization."""
        # Full name
        if 'full_name' in fields and fields['full_name']['value']:
            normalized = normalize_name(fields['full_name']['value'])
            if normalized:
                fields['full_name']['value'] = normalized
        
        # Sex
        if 'sex' in fields and fields['sex']['value']:
            normalized = normalize_sex(fields['sex']['value'])
            if normalized:
                fields['sex']['value'] = normalized
        
        # Dates are already normalized during parsing
        
        return fields
    
    def _validate_fields(self, fields: Dict[str, Any], mrz_data) -> None:
        """
        Validate MRZ fields and checksums.
        Adds warnings for validation failures.
        """
        # Validate passport number format
        if 'passport_number' in fields and fields['passport_number']['value']:
            passport_num = fields['passport_number']['value']
            is_valid, error = validate_passport_number(
                passport_num,
                fields.get('nationality', {}).get('value')
            )
            if not is_valid:
                self.add_warning(f"Passport number validation: {error}")
        
        # Validate MRZ checksums (ICAO 9303)
        # passporteye provides check digits, we validate them
        if hasattr(mrz_data, 'check_number') and mrz_data.check_number:
            if not self._validate_check_digit(
                mrz_data.number,
                mrz_data.check_number
            ):
                self.add_warning("Passport number check digit validation failed")
        
        if hasattr(mrz_data, 'check_date_of_birth') and mrz_data.check_date_of_birth:
            if not self._validate_check_digit(
                mrz_data.date_of_birth,
                mrz_data.check_date_of_birth
            ):
                self.add_warning("Date of birth check digit validation failed")
        
        if hasattr(mrz_data, 'check_expiration_date') and mrz_data.check_expiration_date:
            if not self._validate_check_digit(
                mrz_data.expiration_date,
                mrz_data.check_expiration_date
            ):
                self.add_warning("Expiration date check digit validation failed")
    
    def _validate_check_digit(self, data: str, check_digit: str) -> bool:
        """Validate MRZ check digit using ICAO algorithm."""
        return validate_mrz_checksum(data, check_digit)
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Return pipeline-specific metadata."""
        return {
            "model": "passporteye (MRZ)",
            "standard": "ICAO 9303"
        }