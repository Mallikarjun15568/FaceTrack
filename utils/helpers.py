import uuid
import os
import time
from datetime import date


def generate_unique_filename(extension="jpg"):
    return f"{uuid.uuid4().hex}.{extension}"


def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        

def ensure_folder(path):
    os.makedirs(path, exist_ok=True)


def generate_unique_filename(ext="jpg"):
    return f"{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"


# ============================================================
# ENTERPRISE ATTENDANCE HELPER
# ============================================================
def get_valid_date_range(join_date, from_date, to_date):
    """
    Calculate valid attendance date range based on business rules:
    - Cannot be before employee's join date
    - Cannot be after today (no future dates)
    
    Args:
        join_date: Employee's joining date (date object or None)
        from_date: Requested start date (date object)
        to_date: Requested end date (date object)
    
    Returns:
        tuple: (start_date, end_date) clamped to valid range
    """
    today = date.today()
    
    # Handle None join_date (use from_date as fallback)
    if join_date is None:
        join_date = from_date
    
    # Ensure date objects
    if hasattr(join_date, 'date'):
        join_date = join_date.date()
    if hasattr(from_date, 'date'):
        from_date = from_date.date()
    if hasattr(to_date, 'date'):
        to_date = to_date.date()
    
    # Clamp start_date: max of (from_date, join_date)
    start_date = max(from_date, join_date)
    
    # Clamp end_date: min of (to_date, today)
    end_date = min(to_date, today)
    
    # Safety check: if start > end, return empty range (start = end = today)
    if start_date > end_date:
        return today, today
    
    return start_date, end_date


def get_attendance_status_for_date(attendance_date, join_date, today=None):
    """
    Determine what status to show for a date with no attendance record.
    
    Args:
        attendance_date: The date being checked (date object)
        join_date: Employee's join date (date object or None)
        today: Override for today (date object, default: date.today())
    
    Returns:
        str: 'skip' if date should be excluded,
             'absent' if employee was absent,
             'wait' if it's today and employee hasn't checked in yet
    """
    if today is None:
        today = date.today()
    
    # Ensure date objects
    if hasattr(attendance_date, 'date'):
        attendance_date = attendance_date.date()
    if join_date and hasattr(join_date, 'date'):
        join_date = join_date.date()
    
    # Before join date - skip
    if join_date and attendance_date < join_date:
        return 'skip'
    
    # Future date - skip
    if attendance_date > today:
        return 'skip'
    
    # Today - show WAIT (not absent)
    if attendance_date == today:
        return 'wait'
    
    # Past date with no record - absent
    return 'absent'