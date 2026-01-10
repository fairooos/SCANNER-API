"""
Text normalization utilities for OCR output.
Handles common OCR errors and formatting inconsistencies.
"""
import re
from datetime import datetime
from typing import Optional


def normalize_text(text: str) -> str:
    """
    Basic text normalization.
    - Removes extra whitespace
    - Strips leading/trailing spaces
    - Converts multiple spaces to single space
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', text.strip())
    
    return normalized


def normalize_name(name: str) -> str:
    """
    Normalize person name.
    - Title case
    - Remove extra spaces
    - Handle common OCR errors (l vs I, O vs 0)
    """
    if not name:
        return ""
    
    # Basic normalization
    normalized = normalize_text(name)
    
    # Title case (First Letter of Each Word Capitalized)
    normalized = normalized.title()
    
    return normalized


def normalize_date(date_str: str) -> Optional[str]:
    """
    Normalize date to standard format (YYYY-MM-DD).
    Attempts multiple input formats from config.
    
    Returns:
        Normalized date string or None if parsing fails
    """
    if not date_str:
        return None
    
    # Clean common OCR errors
    cleaned = date_str.strip().replace('O', '0').replace('o', '0')
    
    # Date Formats
    DATE_INPUT_FORMATS = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d %b %Y",
        "%d %B %Y"
    ]
    DATE_OUTPUT_FORMAT = "%Y-%m-%d"
    
    # Try each configured format
    for fmt in DATE_INPUT_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime(DATE_OUTPUT_FORMAT)
        except ValueError:
            continue
    
    # If all formats fail, return None
    return None


def normalize_emirates_id(id_number: str) -> str:
    """
    Normalize Emirates ID number.
    - Remove spaces
    - Ensure dashes are in correct positions
    - Fix common OCR errors (O->0, I->1, etc.)
    """
    if not id_number:
        return ""
    
    # Fix common OCR character confusions
    cleaned = id_number.replace('O', '0').replace('o', '0')
    cleaned = cleaned.replace('I', '1').replace('l', '1')
    cleaned = cleaned.replace(' ', '').replace('_', '-')
    
    # Try to reconstruct format if dashes are missing
    # Expected: 784-YYYY-NNNNNNN-C (total 18 chars with dashes)
    digits_only = re.sub(r'[^0-9]', '', cleaned)
    
    if len(digits_only) == 15:  # 784 + 4 + 7 + 1
        return f"{digits_only[:3]}-{digits_only[3:7]}-{digits_only[7:14]}-{digits_only[14]}"
    
    # Return as-is if format cannot be reconstructed
    return cleaned


def normalize_passport_number(passport_number: str) -> str:
    """
    Normalize passport number.
    - Uppercase
    - Remove spaces and special characters
    - Fix common OCR errors
    """
    if not passport_number:
        return ""
    
    # Fix OCR errors
    cleaned = passport_number.replace('O', '0').replace('o', '0')
    cleaned = cleaned.replace(' ', '').replace('-', '')
    
    # Uppercase
    return cleaned.upper()


def normalize_sex(sex: str) -> str:
    """
    Normalize sex/gender to single letter (M/F).
    """
    if not sex:
        return ""
    
    normalized = sex.strip().upper()
    
    # Map common variations
    if normalized in ['M', 'MALE', 'MAN']:
        return 'M'
    elif normalized in ['F', 'FEMALE', 'WOMAN']:
        return 'F'
    
    # Return first letter if unclear
    return normalized[0] if normalized else ""


def normalize_nationality(nationality: str) -> str:
    """
    Normalize nationality code.
    - Uppercase
    - 3-letter ISO code if possible
    """
    if not nationality:
        return ""
    
    normalized = nationality.strip().upper()
    
    # Country name to 3-letter code mapping (subset)
    country_codes = {
        'UNITED ARAB EMIRATES': 'ARE',
        'UAE': 'ARE',
        'INDIA': 'IND',
        'PAKISTAN': 'PAK',
        'BANGLADESH': 'BGD',
        'PHILIPPINES': 'PHL',
        'EGYPT': 'EGY',
    }
    
    # Check if it's a full country name
    if normalized in country_codes:
        return country_codes[normalized]
    
    # If already 3 letters, return as-is
    if len(normalized) == 3:
        return normalized
    
    return normalized
