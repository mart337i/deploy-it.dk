import secrets
import string

def _generate_password(self, length: int = 12) -> str:
    """
    Generate a secure random password.
    
    Args:
        length: Length of the password
        
    Returns:
        Secure random password
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))