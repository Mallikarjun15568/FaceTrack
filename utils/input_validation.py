"""
Input validation decorators and utilities for FaceTrack Pro
"""
from functools import wraps
from flask import request, jsonify
import re
from utils.logger import logger

def validate_json_request(required_fields=None):
    """
    Decorator to validate JSON request data
    
    Args:
        required_fields: List of required field names
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                logger.warning(f"Non-JSON request to {request.endpoint}")
                return jsonify({"error": "Content-Type must be application/json"}), 400
            
            data = request.get_json()
            if data is None:
                return jsonify({"error": "Invalid JSON data"}), 400
            
            if required_fields:
                missing = [field for field in required_fields if field not in data]
                if missing:
                    logger.warning(f"Missing fields in {request.endpoint}: {missing}")
                    return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_base64_image(max_size_mb=5):
    """
    Decorator to validate base64 image data
    
    Args:
        max_size_mb: Maximum allowed image size in megabytes
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            if not data or 'image' not in data and 'frame' not in data:
                return jsonify({"error": "No image data provided"}), 400
            
            image_data = data.get('image') or data.get('frame')
            
            # Validate base64 format
            if not image_data or not isinstance(image_data, str):
                return jsonify({"error": "Invalid image format"}), 400
            
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            
            # Check size (base64 adds ~33% overhead)
            estimated_size_mb = len(image_data) * 0.75 / (1024 * 1024)
            if estimated_size_mb > max_size_mb:
                logger.warning(f"Image too large: {estimated_size_mb:.2f}MB")
                return jsonify({"error": f"Image too large. Max size: {max_size_mb}MB"}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_employee_id():
    """Decorator to validate employee_id parameter"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            emp_id = kwargs.get('emp_id') or kwargs.get('employee_id')
            if emp_id is not None:
                try:
                    emp_id_int = int(emp_id)
                    if emp_id_int <= 0:
                        return jsonify({"error": "Invalid employee ID"}), 400
                except (ValueError, TypeError):
                    return jsonify({"error": "Employee ID must be a number"}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_date_range():
    """Decorator to validate date range parameters"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from_date = request.args.get('from_date') or request.args.get('from')
            to_date = request.args.get('to_date') or request.args.get('to')
            
            date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
            
            if from_date and not date_pattern.match(from_date):
                return jsonify({"error": "Invalid from_date format. Use YYYY-MM-DD"}), 400
            
            if to_date and not date_pattern.match(to_date):
                return jsonify({"error": "Invalid to_date format. Use YYYY-MM-DD"}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def sanitize_input(text, max_length=255):
    """
    Sanitize text input
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text string
    """
    if not text:
        return ""
    
    # Convert to string and strip whitespace
    text = str(text).strip()
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove any null bytes
    text = text.replace('\x00', '')
    
    return text


def validate_email(email):
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid email format
    """
    if not email:
        return False
    
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(pattern.match(email))


def validate_phone(phone):
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if valid phone format
    """
    if not phone:
        return False
    
    # Remove common separators
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check if it contains only digits and is reasonable length
    return phone.isdigit() and 10 <= len(phone) <= 15
