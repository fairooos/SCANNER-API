
import re
from datetime import datetime
from typing import Optional


def validate_emirates_id_number(id_number: str) -> tuple[bool, Optional[str]]:
    
    if not id_number:
        return False, "ID number is empty"
    
   
    clean_id = id_number.strip().replace(" ", "")
    
    
    pattern = r'^784-\d{4}-\d{7}-\d{1}$'
    
    if not re.match(pattern, clean_id):
        return False, f"Invalid Emirates ID format. Expected: 784-YYYY-NNNNNNN-C, got: {id_number}"
    
    return True, None


def validate_date_consistency(issue_date: Optional[str], expiry_date: Optional[str]) -> tuple[bool, Optional[str]]:
   
    if not issue_date or not expiry_date:
        return True, None  # Skip validation if either date is missing
    
    try:
        issue = datetime.strptime(issue_date, "%Y-%m-%d")
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        
        if expiry <= issue:
            return False, f"Expiry date ({expiry_date}) must be after issue date ({issue_date})"
        
        return True, None
    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"


def validate_passport_number(passport_number: str, country_code: str = None) -> tuple[bool, Optional[str]]:
    
    if not passport_number:
        return False, "Passport number is empty"
    
    clean_number = passport_number.strip().replace(" ", "")
    
    
    if not re.match(r'^[A-Z0-9]{6,9}$', clean_number, re.IGNORECASE):
        return False, f"Invalid passport number format: {passport_number}"
    
    return True, None


def validate_sex(sex: str) -> tuple[bool, Optional[str]]:
    
    normalized = sex.strip().upper()
    
    valid_values = {'M', 'F', 'MALE', 'FEMALE'}
    
    if normalized not in valid_values:
        return False, f"Invalid sex value: {sex}. Expected M/F or Male/Female"
    
    return True, None


def validate_mrz_checksum(data: str, check_digit: str) -> bool:
    if not check_digit or check_digit == '<':
        return True  
    
    weights = [7, 3, 1]
    char_values = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<'
    
    total = 0
    for i, char in enumerate(data):
        if char in char_values:
            value = char_values.index(char)
            total += value * weights[i % 3]
    
    calculated_check = total % 10
    
    try:
        return calculated_check == int(check_digit)
    except ValueError:
        return False