import re
from rest_framework.exceptions import ValidationError

def validate_password_strength(passowrd:str) -> str:
    if len(passowrd)<8:
        raise ValidationError("Password must be at least 8 character long !")
    if not re.search(r'[A-Z]',passowrd):
        raise ValidationError("Password must contain at least an uppercase letter")
    if not re.search(r'\d',passowrd):
        raise ValidationError("Password must contain at least one digit")
    if not re.search(r'[!@#$%^&*(),.?"{}|<>]'):
        raise ValidationError("Password must contain at least one special character")
    return passowrd
