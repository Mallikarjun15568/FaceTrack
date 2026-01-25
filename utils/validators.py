import re
import imghdr
from flask import jsonify
from functools import wraps
from utils.logger import logger

# File upload configuration
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_image_upload(file_storage):
    """Validate uploaded image file for security
    
    Args:
        file_storage: Flask FileStorage object
        
    Returns:
        (is_valid: bool, error_message: str or None)
    """
    if not file_storage or not file_storage.filename:
        return False, "No file provided"
    
    filename = file_storage.filename.lower()
    
    # Check file extension
    if '.' not in filename:
        return False, "File has no extension"
    
    ext = filename.rsplit('.', 1)[1]
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
    
    # Check file size (seek to end to get size)
    file_storage.seek(0, 2)  # Seek to end
    size = file_storage.tell()
    file_storage.seek(0)  # Reset to beginning
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if size == 0:
        return False, "File is empty"
    
    # Verify actual file type using magic bytes
    try:
        file_type = imghdr.what(file_storage)
        file_storage.seek(0)  # Reset after reading
        
        if file_type not in ['png', 'jpeg', 'gif', 'webp']:
            return False, "File content does not match image format"
    except Exception:
        file_storage.seek(0)
        return False, "Could not verify file type"
    
    return True, None

def validate_employee_id(emp_id):
    """Validate employee ID format"""
    if not emp_id or not isinstance(emp_id, str):
        return False, "Employee ID is required"

    if not re.match(r'^[A-Za-z0-9]{3,20}$', emp_id):
        return False, "Employee ID must be 3-20 alphanumeric characters"

    return True, None


"""
Input validation and sanitization utilities for FaceTrack
Prevents XSS, injection attacks, and ensures data quality
"""
import re
from markupsafe import escape


def sanitize_text(text, max_length=255):
    """
    Sanitize text input - removes HTML, trims whitespace
    
    Args:
        text: Raw text input
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text string
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove leading/trailing whitespace
    cleaned = text.strip()
    
    # Escape HTML special characters to prevent XSS
    cleaned = escape(cleaned)
    
    # Truncate to max length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return str(cleaned)  # Convert Markup back to str


def sanitize_email(email):
    """
    Validate and sanitize email address
    
    Args:
        email: Email string
        
    Returns:
        Sanitized email or None if invalid
    """
    if not email or not isinstance(email, str):
        return None
    
    email = email.strip().lower()
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return None
    
    if len(email) > 255:
        return None
    
    return email


def sanitize_username(username):
    """
    Sanitize username - alphanumeric, underscore, hyphen only
    
    Args:
        username: Username string
        
    Returns:
        Sanitized username or None if invalid
    """
    if not username or not isinstance(username, str):
        return None
    
    username = username.strip().lower()
    
    # Only allow alphanumeric, underscore, hyphen
    if not re.match(r'^[a-z0-9_-]{3,50}$', username):
        return None
    
    return username


def validate_password(password):
    """
    Validate password strength
    
    Requirements:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    
    Args:
        password: Password string
        
    Returns:
        (is_valid: bool, message: str)
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if len(password) > 128:
        return False, "Password too long (max 128 characters)"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*...)"
    
    # Check against common passwords
    common_passwords = [
        'password', '12345678', 'qwerty', 'abc123', 'password123',
        'admin123', 'letmein', 'welcome', 'monkey', '1234567890'
    ]
    
    if password.lower() in common_passwords:
        return False, "Password is too common, please choose a stronger one"
    
    return True, "Password is strong"


def validate_email(email):
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False, "Email is required"

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"

    return True, None


def validate_name(name):
    """Validate name"""
    if not name or not isinstance(name, str):
        return False, "Name is required"

    if len(name) < 2 or len(name) > 100:
        return False, "Name must be 2-100 characters"

    if not re.match(r'^[a-zA-Z\s]+$', name):
        return False, "Name can only contain letters and spaces"

    return True, None


def validate_phone(phone):
    """Validate phone number"""
    if not phone:
        return True, None  # Optional field

    if not re.match(r'^[0-9]{10}$', phone):
        return False, "Phone must be 10 digits"

    return True, None


def validate_department(department):
    """Validate department"""
    valid_departments = ['IT', 'HR', 'Sales', 'Marketing', 'Finance']
    if department not in valid_departments:
        return False, f"Department must be one of: {', '.join(valid_departments)}"

    return True, None


def validate_file_upload(file):
    """Validate uploaded file"""
    if not file:
        return False, "No file uploaded"

    if file.filename == '':
        return False, "Empty filename"

    # Check extension
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return False, f"Only {', '.join(allowed_extensions)} files allowed"

    # Check file size (5MB max)
    file.seek(0, 2)  # Go to end
    size = file.tell()
    file.seek(0)  # Reset

    if size > 5 * 1024 * 1024:
        return False, "File size must be less than 5MB"

    return True, None


# Decorator for validating request data
def validate_request(validators):
    """
    Decorator to validate request data
    Usage:
        @validate_request({
            'emp_id': validate_employee_id,
            'email': validate_email
        })
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request

            # Get data from request
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form

            # Validate each field
            for field, validator in validators.items():
                value = data.get(field)
                is_valid, error_msg = validator(value)

                if not is_valid:
                    logger.warning(f"Validation failed for {field}: {error_msg}")
                    return jsonify({'error': error_msg}), 400

            return f(*args, **kwargs)
        return wrapper
    return decorator
