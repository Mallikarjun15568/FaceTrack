from datetime import datetime
import csv, os
from db_utils import get_db

def get_employee_id(username):
    """Fetch employee_id using username."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.id 
        FROM employees e
        JOIN users u ON e.user_id = u.id
        WHERE u.username = %s
    """, (username,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return result[0] if result else None


def log_attendance(username):
    timestamp = datetime.now()
    date_today = timestamp.date()
    time_now = timestamp.time()

    employee_id = get_employee_id(username)
    if not employee_id:
        print(" Error: employee_id not found for", username)
        return

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO attendance (employee_id, date, time, entry_time)
        VALUES (%s, %s, %s, %s)
    """, (employee_id, date_today, time_now, time_now))

    conn.commit()
    cursor.close()
    conn.close()

    # Optional CSV
    if username.lower() != "admin":
        os.makedirs('logs', exist_ok=True)
        with open('logs/attendance.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([username, timestamp.strftime('%Y-%m-%d %H:%M:%S')])


def log_logout(username):
    timestamp = datetime.now()
    time_now = timestamp.time()

    employee_id = get_employee_id(username)
    if not employee_id:
        print(" Error: employee_id not found for", username)
        return

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE attendance
        SET exit_time = %s
        WHERE employee_id = %s
        AND exit_time IS NULL
        ORDER BY entry_time DESC
        LIMIT 1
    """, (time_now, employee_id))

    conn.commit()
    cursor.close()
    conn.close()

    # Optional CSV
    if username.lower() != "admin":
        os.makedirs('logs', exist_ok=True)
        with open('logs/logout.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([username, timestamp.strftime('%Y-%m-%d %H:%M:%S')])
