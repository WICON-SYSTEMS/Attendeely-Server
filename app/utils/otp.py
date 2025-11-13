import random
import string


def generate_otp(length: int = 6) -> str:
    """
    Generate a random numeric OTP code
    
    Args:
        length: Length of OTP (default 6)
        
    Returns:
        str: Generated OTP code
    """
    return ''.join(random.choices(string.digits, k=length))
