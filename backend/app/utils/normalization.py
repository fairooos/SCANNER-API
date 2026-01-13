import re
from datetime import datetime
from typing import Optional


def normalize_text(text: str) -> str:
    
    if not text:
        return ""
    
    
    normalized = re.sub(r'\s+', ' ', text.strip())
    
    return normalized


def normalize_name(name: str) -> str:
    
    if not name:
        return ""
    
    
    normalized = normalize_text(name)
    
    
    normalized = normalized.title()
    
    return normalized


def normalize_date(date_str: str) -> Optional[str]:
    
    if not date_str:
        return None
    
    
    cleaned = date_str.strip().replace('O', '0').replace('o', '0')
    
   
    DATE_INPUT_FORMATS = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d %b %Y",
        "%d %B %Y"
    ]
    DATE_OUTPUT_FORMAT = "%Y-%m-%d"
    
    
    for fmt in DATE_INPUT_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime(DATE_OUTPUT_FORMAT)
        except ValueError:
            continue
    
    
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
    
   
    cleaned = id_number.replace('O', '0').replace('o', '0')
    cleaned = cleaned.replace('I', '1').replace('l', '1')
    cleaned = cleaned.replace(' ', '').replace('_', '-')
    
    
    digits_only = re.sub(r'[^0-9]', '', cleaned)
    
    if len(digits_only) == 15:  # 784 + 4 + 7 + 1
        return f"{digits_only[:3]}-{digits_only[3:7]}-{digits_only[7:14]}-{digits_only[14]}"
    
    
    return cleaned


def normalize_passport_number(passport_number: str) -> str:
    
    if not passport_number:
        return ""
    
    
    cleaned = passport_number.replace('O', '0').replace('o', '0')
    cleaned = cleaned.replace(' ', '').replace('-', '')
    
    
    return cleaned.upper()


def normalize_sex(sex: str) -> str:
    
    if not sex:
        return ""
    
    normalized = sex.strip().upper()
    
   
    if normalized in ['M', 'MALE', 'MAN']:
        return 'M'
    elif normalized in ['F', 'FEMALE', 'WOMAN']:
        return 'F'
    
    
    return normalized[0] if normalized else ""


def normalize_nationality(nationality: str) -> str:
   
    if not nationality:
        return ""
    
    normalized = nationality.strip().upper()
    
   
    country_codes = {
        'UNITED ARAB EMIRATES': 'ARE',
        'UAE': 'ARE',
        'INDIA': 'IND',
        'PAKISTAN': 'PAK',
        'BANGLADESH': 'BGD',
        'PHILIPPINES': 'PHL',
        'EGYPT': 'EGY',
    }
    
   
    if normalized in country_codes:
        return country_codes[normalized]
    
    
    if len(normalized) == 3:
        return normalized
    
    return normalized
