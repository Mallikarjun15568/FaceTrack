import re
from flask import jsonify
from functools import wraps
from utils.logger import logger

def validate_employee_id(emp_id):
    """Validate employee ID format"""
    if not emp_id or not isinstance(emp_id, str):
        return False, "Employee ID is required"

    if not re.match(r'^[A-Za-z0-9]{3,20}$', emp_id):
        return False, "Employee ID must be 3-20 alphanumeric characters"

    return True, None


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
    valid_departments = ['IT', 'HR', 'Sales', 'Marketing', 'Finance', 'Admin']
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
