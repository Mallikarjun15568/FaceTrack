from . import bp
from flask import render_template, request, redirect, url_for, session, flash, jsonify, send_file, current_app
from utils.db import get_db
from werkzeug.security import check_password_hash, generate_password_hash
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime, date, timedelta
import calendar
import os
from werkzeug.utils import secure_filename
import base64
from blueprints.kiosk import utils as kiosk_utils
from utils.helpers import generate_unique_filename, ensure_folder
from utils.email_service import EmailService
from flask_wtf.csrf import CSRFProtect
from blueprints.auth.utils import login_required
csrf = CSRFProtect()

# ================================
# EMPLOYEE DASHBOARD
# ================================
@bp.route('/dashboard')
def dashboard():
    db = get_db()
    cur = db.cursor(dictionary=True)
    employee_id = session.get('employee_id')
    user_name = session.get('full_name', 'Employee')

    # Today's attendance
    cur.execute("""
        SELECT check_in_time, check_out_time, status
        FROM attendance
        WHERE employee_id = %s AND DATE(check_in_time) = CURDATE()
        ORDER BY check_in_time DESC LIMIT 1
    """, (employee_id,))
    today_attendance = cur.fetchone()

    # Recent attendance (last 5) including duration when checked out
    cur.execute("""
        SELECT DATE(check_in_time) as date,
               TIME_FORMAT(TIME(check_in_time), '%H:%i') as check_in,
               TIME_FORMAT(TIME(check_out_time), '%H:%i') as check_out,
               status,
               CASE
                   WHEN check_out_time IS NOT NULL THEN
                       TIME_FORMAT(TIMEDIFF(check_out_time, check_in_time), '%H:%i')
                   ELSE NULL
               END as duration
        FROM attendance
        WHERE employee_id = %s AND check_in_time IS NOT NULL
        ORDER BY check_in_time DESC LIMIT 5
    """, (employee_id,))
    recent_attendance = cur.fetchall()

    # Leave balance (from leave_balance table)
    try:
        cur.execute("SELECT casual_leave, sick_leave, personal_leave, emergency_leave FROM leave_balance WHERE employee_id = %s", (employee_id,))
        balance_data = cur.fetchone()
        if balance_data:
            leave_balance = (balance_data['casual_leave'] or 0) + (balance_data['sick_leave'] or 0) + (balance_data['personal_leave'] or 0) + (balance_data['emergency_leave'] or 0)
            total_possible = 12 + 6 + 10 + 5  # Assuming defaults: 12 casual, 6 sick, 10 vacation, 5 emergency
            leave_balance_percentage = min((leave_balance / total_possible) * 100, 100)
        else:
            leave_balance = 0
            leave_balance_percentage = 0
    except:
        leave_balance = 0
        leave_balance_percentage = 0

    # Face request data
    cur.execute("SELECT id FROM face_data WHERE emp_id = %s", (employee_id,))
    has_face = cur.fetchone() is not None

    cur.execute("SELECT id, request_type, status, requested_at, rejection_reason FROM pending_face_requests WHERE emp_id = %s ORDER BY requested_at DESC LIMIT 1", (employee_id,))
    pending_request = cur.fetchone()

    return render_template('employee/dashboard.html',
                         user_name=user_name,
                         today_attendance=today_attendance,
                         recent_attendance=recent_attendance,
                         leave_balance=leave_balance,
                         leave_balance_percentage=leave_balance_percentage,
                         has_face=has_face,
                         pending_request=pending_request)

# ================================
# EMPLOYEE FACE REQUEST PAGE
# ================================
# ================================
# EMPLOYEE PROFILE
# ================================
@bp.route('/profile', methods=['GET', 'POST'])
def profile():
    db = get_db()
    cur = db.cursor(dictionary=True)
    employee_id = session.get('employee_id')
    user_id = session.get('user_id')

    if request.method == 'POST':
        # Handle remove photo action
        if request.form.get('action') == 'remove_photo':
            # Remove the photo file if it exists
            cur.execute("SELECT photo FROM employees WHERE id = %s", (employee_id,))
            current_photo = cur.fetchone()
            if current_photo and current_photo['photo']:
                # Delete the file
                try:
                    file_path = os.path.join(current_app.root_path, current_photo['photo'].lstrip('/'))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass  # Ignore if file doesn't exist or can't be deleted

            # Update database to remove photo reference
            cur.execute("""
                UPDATE employees
                SET photo = NULL
                WHERE id = %s
            """, (employee_id,))
            db.commit()

            flash('Profile photo removed successfully', 'success')
            return redirect(url_for('employee.profile'))

        # Handle profile photo upload
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename:
                # Validate file type
                allowed_extensions = {'jpg', 'jpeg', 'png'}
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    # Validate file size (2MB max)
                    if len(file.read()) > 2 * 1024 * 1024:  # 2MB
                        flash('File size must be less than 2MB', 'error')
                        return redirect(url_for('employee.profile'))
                    file.seek(0)  # Reset file pointer

                    # Create upload directory if it doesn't exist
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_photos')
                    os.makedirs(upload_dir, exist_ok=True)

                    # Generate filename
                    filename = f'user_{user_id}.jpg'
                    file_path = os.path.join(upload_dir, filename)

                    # Save file (convert to JPG if needed)
                    from PIL import Image
                    try:
                        image = Image.open(file)
                        # Convert to RGB if necessary (for PNG with transparency)
                        if image.mode in ("RGBA", "P"):
                            image = image.convert("RGB")
                        image.save(file_path, 'JPEG', quality=85)

                        # Update database
                        photo_path = f'/static/uploads/profile_photos/{filename}'
                        cur.execute("""
                            UPDATE employees
                            SET photo = %s
                            WHERE id = %s
                        """, (photo_path, employee_id))
                        db.commit()

                        flash('Profile photo updated successfully', 'success')
                    except Exception as e:
                        flash('Error processing image. Please try again.', 'error')
                else:
                    flash('Only JPG and PNG files are allowed', 'error')
                return redirect(url_for('employee.profile'))

        # Handle profile update
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        if full_name and email:
            # Update employee
            cur.execute("""
                UPDATE employees
                SET full_name = %s, email = %s, phone = %s
                WHERE id = %s
            """, (full_name, email, phone, employee_id))

            # Update user email
            cur.execute("""
                UPDATE users
                SET email = %s
                WHERE id = %s
            """, (email, user_id))

            db.commit()
            flash('Profile updated successfully', 'success')
            session['full_name'] = full_name
        else:
            flash('Full name and email are required', 'error')

        return redirect(url_for('employee.profile'))

    # Get current data
    cur.execute("""
        SELECT e.id, e.full_name, e.email, e.phone, e.created_at, e.profile_photo, d.name as department_name
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        WHERE e.id = %s
    """, (employee_id,))
    profile_data = cur.fetchone()

    return render_template('employee/profile.html', profile=profile_data)

# ================================
# EMPLOYEE ATTENDANCE
# ================================
@bp.route('/attendance')
def attendance():
    db = get_db()
    cur = db.cursor(dictionary=True)
    employee_id = session.get('employee_id')

    # Get attendance records for the last 30 days and include absent days
    today_date = date.today()
    start_date = today_date - timedelta(days=29)

    cur.execute("""
        SELECT DATE(check_in_time) as date,
               DATE_FORMAT(check_in_time, '%H:%i') as check_in,
               DATE_FORMAT(check_out_time, '%H:%i') as check_out,
               status,
               CASE
                   WHEN check_out_time IS NOT NULL THEN
                       TIME_FORMAT(TIMEDIFF(check_out_time, check_in_time), '%H:%i')
                   ELSE NULL
               END as duration
        FROM attendance
        WHERE employee_id = %s
          AND DATE(check_in_time) BETWEEN %s AND %s
        ORDER BY check_in_time DESC
    """, (employee_id, start_date, today_date))
    rows = cur.fetchall()

    # Map DB rows by date for quick lookup
    rows_by_date = { (r['date'] if hasattr(r['date'], 'isoformat') else r['date']): r for r in rows }

    attendance_records = []
    for i in range(0, 30):
        d = start_date + timedelta(days=i)
        db_row = rows_by_date.get(d)
        if db_row:
            attendance_records.append(db_row)
        else:
            attendance_records.append({
                'date': d,
                'check_in': None,
                'check_out': None,
                'status': 'absent',
                'duration': None
            })

    # Get late time setting
    late_time = current_app.config.get('LATE_TIME', '09:00')

    # Process attendance records to determine proper status
    for record in attendance_records:
        if record['check_in']:
            check_in_time = record['check_in']
            if check_in_time <= late_time:
                record['status'] = 'present'
            else:
                record['status'] = 'late'
        else:
            record['status'] = 'absent'

    return render_template('employee/attendance.html', attendance_records=attendance_records)

@bp.route('/export-attendance-pdf')
def export_attendance_pdf():
    db = get_db()
    cur = db.cursor(dictionary=True)
    employee_id = session.get('employee_id')
    user_name = session.get('full_name', 'Employee')

    # Get custom date range from request
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if from_date and to_date:
        start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        if start_date > end_date:
            flash("From date cannot be later than to date", "error")
            return redirect(url_for('employee.attendance'))
    else:
        end_date = date.today()
        start_date = end_date - timedelta(days=29)

    # Get company settings
    try:
        cur.execute("SELECT setting_key, setting_value FROM settings WHERE setting_key IN ('company_name', 'company_logo')")
        rows = cur.fetchall()
        company_settings = {row['setting_key']: row['setting_value'] for row in rows}
        company_name = company_settings.get('company_name', 'FaceTrack Pro')
    except:
        company_name = 'FaceTrack Pro'

    # Get all attendance records for the employee within date range
    cur.execute("""
        SELECT DATE(check_in_time) as date,
               DATE_FORMAT(check_in_time, '%H:%i') as check_in,
               DATE_FORMAT(check_out_time, '%H:%i') as check_out,
               status,
               TIME_FORMAT(TIMEDIFF(check_out_time, check_in_time), '%H:%i') as duration
        FROM attendance
        WHERE employee_id = %s
          AND DATE(check_in_time) BETWEEN %s AND %s
        ORDER BY check_in_time ASC
    """, (employee_id, start_date, end_date))
    attendance_records = cur.fetchall()

    # Get late time setting
    late_time = current_app.config.get('LATE_TIME', '09:00')

    # Process attendance records to determine proper status
    for record in attendance_records:
        if record['check_in']:
            check_in_time = record['check_in']
            if check_in_time <= late_time:
                record['status'] = 'present'
            else:
                record['status'] = 'late'
        else:
            record['status'] = 'absent'

    # Create PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Company Header
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 40, company_name)
    
    # Horizontal line
    c.setStrokeColorRGB(0.2, 0.4, 0.7)
    c.setLineWidth(2)
    c.line(50, height - 50, width - 50, height - 50)

    # Report Title
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 75, "Attendance Report")

    # Employee info and date range
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 105, f"Employee: {user_name}")
    c.drawString(50, height - 125, f"Report Period: {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}")
    c.drawString(50, height - 145, f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
    c.drawString(50, height - 165, f"Total Records: {len(attendance_records)}")

    # Table headers
    c.setFont("Helvetica-Bold", 10)
    y_position = height - 195
    c.drawString(50, y_position, "Date")
    c.drawString(130, y_position, "Check-in")
    c.drawString(200, y_position, "Check-out")
    c.drawString(280, y_position, "Duration")
    c.drawString(360, y_position, "Status")

    # Draw line under headers
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.line(50, y_position - 5, 500, y_position - 5)

    # Table data
    c.setFont("Helvetica", 9)
    y_position -= 20

    for record in attendance_records:
        if y_position < 50:  # New page if needed
            c.showPage()
            c.setFont("Helvetica", 9)
            y_position = height - 50

        date_str = record['date'].strftime('%d %b %Y') if record['date'] else 'N/A'
        check_in = record['check_in'] or '-'
        check_out = record['check_out'] or '-'
        duration = str(record['duration']) if record['duration'] else '-'
        status = record['status'].title() if record['status'] else '-'

        c.drawString(50, y_position, date_str)
        c.drawString(130, y_position, check_in)
        c.drawString(200, y_position, check_out)
        c.drawString(280, y_position, duration)
        c.drawString(360, y_position, status)

        y_position -= 15

    c.save()
    buffer.seek(0)

    # Return PDF file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'attendance_report_{user_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.pdf',
        mimetype='application/pdf'
    )

@bp.route('/export-summary-pdf')
def export_summary_pdf():
    db = get_db()
    cur = db.cursor(dictionary=True)
    employee_id = session.get('employee_id')
    user_name = session.get('full_name', 'Employee')

    # Get company name from settings
    try:
        cur.execute("SELECT setting_value FROM settings WHERE setting_key = 'company_name'")
        company_result = cur.fetchone()
        company_name = company_result['setting_value'] if company_result else 'FaceTrack Pro'
    except:
        company_name = 'FaceTrack Pro'

    # Get monthly summary data (same as summary route)
    cur.execute("""
        SELECT MONTH(check_in_time) as month,
               COUNT(DISTINCT DATE(check_in_time)) as present_days
        FROM attendance
        WHERE employee_id = %s AND YEAR(check_in_time) = YEAR(CURDATE())
              AND (status = 'check-in' OR status = 'check-out')
        GROUP BY MONTH(check_in_time)
        ORDER BY month
    """, (employee_id,))
    monthly_data = cur.fetchall()

    # Fill missing months and calculate totals
    summary = []
    total_present = 0
    for month in range(1, 13):
        data = next((item for item in monthly_data if item['month'] == month), None)
        if data:
            present_days = data['present_days']
            summary.append({
                'month': calendar.month_name[month],
                'present': present_days
            })
            total_present += present_days
        else:
            summary.append({
                'month': calendar.month_name[month],
                'present': 0
            })

    # Create PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title with company name
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"{company_name} - Monthly Attendance Summary")

    # Employee info
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Employee: {user_name}")
    c.drawString(50, height - 100, f"Report Year: {datetime.now().year}")
    c.drawString(50, height - 120, f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
    c.drawString(50, height - 140, f"Total Present Days: {total_present}")

    # Table headers
    c.setFont("Helvetica-Bold", 10)
    y_position = height - 170
    c.drawString(50, y_position, "Month")
    c.drawString(200, y_position, "Present Days")

    # Draw line under headers
    c.line(50, y_position - 5, 300, y_position - 5)

    # Table data
    c.setFont("Helvetica", 9)
    y_position -= 20

    for record in summary:
        if y_position < 50:  # New page if needed
            c.showPage()
            c.setFont("Helvetica", 9)
            y_position = height - 50

        month_name = record['month']
        present_days = record['present']

        c.drawString(50, y_position, month_name)
        c.drawString(200, y_position, str(present_days))

        y_position -= 15

    c.save()
    buffer.seek(0)

    # Return PDF file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'attendance_summary_{user_name.replace(" ", "_")}_{datetime.now().strftime("%Y%m%d")}.pdf',
        mimetype='application/pdf'
    )

# ================================
# EMPLOYEE LEAVE MANAGEMENT
# ================================
@bp.route('/leave', methods=['GET', 'POST'])
def leave():
    db = get_db()
    cur = db.cursor(dictionary=True)
    employee_id = session.get('employee_id')

    if request.method == 'POST':
        leave_type = request.form.get('leave_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason', '').strip()

        if leave_type and start_date and end_date and reason:
            # Calculate total days
            from datetime import datetime
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            total_days = (end - start).days + 1
            
            if total_days <= 0:
                flash('End date must be after start date', 'error')
                return redirect(url_for('employee.leave'))
            
            # Insert leave request
            cur.execute("""
                INSERT INTO leaves (employee_id, leave_type, start_date, end_date, total_days, reason, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'pending')
            """, (employee_id, leave_type, start_date, end_date, total_days, reason))
            db.commit()
            flash('Leave request submitted successfully', 'success')
        else:
            flash('All fields required', 'error')

        return redirect(url_for('employee.leave'))

    # Get leave history
    cur.execute("""
        SELECT id, leave_type, start_date, end_date, reason, status, applied_date as created_at
        FROM leaves
        WHERE employee_id = %s
        ORDER BY applied_date DESC
    """, (employee_id,))
    leave_history = cur.fetchall()

    # Leave balance - get detailed balance from leave_balance table
    cur.execute("""
        SELECT * FROM leave_balance WHERE employee_id = %s
    """, (employee_id,))
    balance = cur.fetchone()

    # If no balance record exists, create one with default values
    if not balance:
        cur.execute("""
            INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, personal_leave, emergency_leave)
            VALUES (%s, 12, 12, 15, 10)
        """, (employee_id,))
        db.commit()
        cur.execute("""
            SELECT * FROM leave_balance WHERE employee_id = %s
        """, (employee_id,))
        balance = cur.fetchone()

    # Ensure balance is not None
    if not balance:
        balance = {
            'casual_leave': 12,
            'sick_leave': 12,
            'personal_leave': 15,
            'emergency_leave': 10
        }

    return render_template('employee/leave.html',
                         leave_history=leave_history,
                         balance=balance)

# ================================
# CANCEL LEAVE REQUEST
# ================================
@bp.route('/cancel-leave/<int:leave_id>', methods=['POST'])
@login_required
def cancel_leave(leave_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    employee_id = session.get('employee_id')

    try:
        # Check if the leave belongs to the current employee and is pending
        cur.execute("""
            SELECT id, status FROM leaves
            WHERE id = %s AND employee_id = %s
        """, (leave_id, employee_id))
        leave = cur.fetchone()

        if not leave:
            return jsonify({'success': False, 'message': 'Leave request not found'}), 404

        if leave['status'] != 'pending':
            return jsonify({'success': False, 'message': 'Only pending leave requests can be cancelled'}), 400

        # Update status to cancelled
        cur.execute("""
            UPDATE leaves SET status = 'cancelled'
            WHERE id = %s AND employee_id = %s
        """, (leave_id, employee_id))
        db.commit()

        return jsonify({'success': True, 'message': 'Leave request cancelled successfully'})

    except Exception as e:
        db.rollback()
        from utils.logger import logger
        logger.error(f"Error cancelling leave: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while cancelling the leave'}), 500

# ================================
# EMPLOYEE SUMMARY
# ================================
@bp.route('/summary')
def summary():
    db = get_db()
    cur = db.cursor(dictionary=True)
    employee_id = session.get('employee_id')

    # Get total statistics for the year
    current_year = datetime.now().year

    # Total present days
    cur.execute("""
        SELECT COUNT(DISTINCT DATE(check_in_time)) as total_present
        FROM attendance
        WHERE employee_id = %s AND YEAR(check_in_time) = %s
              AND (status = 'check-in' OR status = 'check-out')
    """, (employee_id, current_year))
    total_present_result = cur.fetchone()
    total_present = total_present_result['total_present'] or 0

    # Total hours worked (approximate)
    cur.execute("""
        SELECT SUM(TIMESTAMPDIFF(HOUR, check_in_time, check_out_time)) as total_hours
        FROM attendance
        WHERE employee_id = %s AND YEAR(check_in_time) = %s
              AND check_out_time IS NOT NULL
    """, (employee_id, current_year))
    total_hours_result = cur.fetchone()
    total_hours_raw = total_hours_result['total_hours'] or 0
    total_hours = f"{total_hours_raw}h"

    # Late arrivals (assuming late after 9:30 AM)
    cur.execute("""
        SELECT COUNT(*) as total_late
        FROM attendance
        WHERE employee_id = %s AND YEAR(check_in_time) = %s
              AND TIME(check_in_time) > '09:30:00'
    """, (employee_id, current_year))
    total_late_result = cur.fetchone()
    total_late = total_late_result['total_late'] or 0

    # Absent days (rough calculation - days with no attendance in working days)
    # This is a simplified calculation
    total_absent = 0  # For now, we'll set this to 0 as it's complex to calculate accurately

    # Monthly summary for current year with late calculations
    cur.execute("""
        SELECT MONTH(check_in_time) as month,
               COUNT(DISTINCT DATE(check_in_time)) as present_days,
               COUNT(CASE WHEN TIME(check_in_time) > '09:30:00' THEN 1 END) as late_days
        FROM attendance
        WHERE employee_id = %s AND YEAR(check_in_time) = %s
              AND (status = 'check-in' OR status = 'check-out')
        GROUP BY MONTH(check_in_time)
        ORDER BY month
    """, (employee_id, current_year))
    monthly_data = cur.fetchall()

    # Fill missing months and calculate attendance rates
    summary = []
    for month in range(1, 13):
        data = next((item for item in monthly_data if item['month'] == month), None)
        if data:
            present_days = data['present_days']
            late_days = data['late_days'] or 0
            # Rough attendance rate calculation (assuming 22 working days per month)
            attendance_rate = min(int((present_days / 22) * 100), 100)
            summary.append({
                'month': calendar.month_name[month],
                'year': current_year,
                'present': present_days,
                'late': late_days,
                'absent': max(0, 22 - present_days),  # Rough calculation
                'attendance_rate': attendance_rate
            })
        else:
            summary.append({
                'month': calendar.month_name[month],
                'year': current_year,
                'present': 0,
                'late': 0,
                'absent': 22,  # Assuming 22 working days
                'attendance_rate': 0
            })

    return render_template('employee/summary.html',
                         summary=summary,
                         total_present=total_present,
                         total_hours=total_hours,
                         total_late=total_late,
                         total_absent=total_absent)

# ================================
# EMPLOYEE SETTINGS
# ================================
@bp.route('/settings', methods=['GET', 'POST'])
def settings():
    db = get_db()
    cur = db.cursor(dictionary=True)
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_password or not new_password or not confirm_password:
            flash('All fields required', 'error')
            return redirect(url_for('employee.settings'))

        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('employee.settings'))

        # Validate new password strength
        from utils.validators import validate_password
        is_strong, msg = validate_password(new_password)
        if not is_strong:
            flash(msg, 'error')
            return redirect(url_for('employee.settings'))

        # Verify current password
        cur.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()

        if not user or not check_password_hash(user['password'], current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('employee.settings'))

        # Update password
        hashed = generate_password_hash(new_password)
        cur.execute("UPDATE users SET password = %s WHERE id = %s", (hashed, user_id))
        db.commit()

        flash('Password changed successfully', 'success')
        return redirect(url_for('employee.settings'))

    # Get last login info (simplified - could be enhanced with proper session tracking)
    # For now, we'll just pass None since user_sessions table may not exist
    last_login = None

    return render_template('employee/settings.html', last_login=last_login)


# ================================
# FACE REQUEST (Enroll/Update)
# ================================
@bp.route('/face_request')
def face_request():
    db = get_db()
    cur = db.cursor(dictionary=True)
    employee_id = session.get('employee_id')

    # Check if already has face data
    cur.execute("SELECT id FROM face_data WHERE emp_id = %s", (employee_id,))
    has_face = cur.fetchone() is not None

    # Check pending requests
    cur.execute("SELECT id, request_type, status, requested_at, rejection_reason FROM pending_face_requests WHERE emp_id = %s ORDER BY requested_at DESC LIMIT 1", (employee_id,))
    pending_request = cur.fetchone()

    return render_template('employee/face_request.html', has_face=has_face, pending_request=pending_request)


@bp.route('/submit_face_request', methods=['POST'])
@login_required
def submit_face_request():
    try:
        # Require logged-in employee
        employee_id = session.get('employee_id')
        if not employee_id:
            return jsonify({'status': 'error', 'message': 'Authentication required'}), 401

        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({'status': 'error', 'message': 'Invalid JSON data'}), 400

        request_type = data.get('request_type')  # 'enroll' or 'update'
        image_base64 = data.get('image')

        if request_type not in ['enroll', 'update'] or not image_base64:
            return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

        db = get_db()
        cur = db.cursor(dictionary=True)

        # Check if already has pending request
        cur.execute("SELECT id FROM pending_face_requests WHERE emp_id = %s AND status = 'pending'", (employee_id,))
        if cur.fetchone():
            return jsonify({'status': 'error', 'message': 'You already have a pending request'}), 400

        # Decode image
        try:
            pil_img, frame = kiosk_utils.decode_frame(image_base64)
        except Exception:
            return jsonify({'status': 'error', 'message': 'Invalid image format'}), 400

        # --- YE WALA PART ADD KARO (PROPER CHECK) ---
        import cv2
        from utils.face_encoder import face_encoder # Ensure path is correct
        import numpy as np

        # A. Blur Check (Quality Control) - (COMMENTED OUT FOR DEMO)
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        # if variance < 80: # 80-100 is a good threshold
        #     return jsonify({'status': 'error', 'message': 'Photo is too blurry. Please take a clear photo.'}), 400

        # B. Face Detection (Presence Control)
        faces = face_encoder.app.get(frame)
        if len(faces) == 0:
            return jsonify({'status': 'error', 'message': 'No face detected in the photo.'}), 400
        if len(faces) > 1:
            return jsonify({'status': 'error', 'message': 'Multiple faces detected. Please ensure only one person is in the photo.'}), 400

        # C. Confidence Check (Quality Control)
        from flask import current_app
        min_confidence = float(current_app.config.get("MIN_CONFIDENCE", 85)) / 100.0
        faces = [f for f in faces if getattr(f, 'det_score', 1.0) >= min_confidence]
        
        if len(faces) == 0:
            return jsonify({"status": "low_confidence", "message": f"No face detected with sufficient confidence (min: {min_confidence:.0%})"})

        face = faces[0]
        embedding = face.normed_embedding.astype("float32")

        # D. Duplicate Check (Prevent same person multiple enrollments)
        DUPLICATE_FACE_THRESHOLD = 0.5  # Same as admin side
        
        # Check existing face data
        cur.execute("SELECT emp_id, embedding FROM face_data WHERE emp_id != %s", (employee_id,))
        existing_faces = cur.fetchall()
        
        for face_row in existing_faces:
            existing_emb = face_encoder._decode_embedding(face_row['embedding'])
            # Compute cosine similarity (both are normalized)
            sim = np.dot(embedding, existing_emb)
            if sim >= DUPLICATE_FACE_THRESHOLD:
                return jsonify({"status": "error", "message": f"Face already enrolled for employee ID {face_row['emp_id']}"}), 400
        
        # --- CHECK KHATAM, AB SAVE KARO ---

        # Save image to temp folder for pending
        pending_folder = os.path.join(current_app.root_path, 'static', 'pending_faces')
        ensure_folder(pending_folder)
        filename = generate_unique_filename('jpg')
        full_image_path = os.path.join(pending_folder, filename)
        pil_img.save(full_image_path, 'JPEG')
        image_path = os.path.join('pending_faces', filename).replace('\\', '/')  # Normalize to forward slashes

        # Insert into pending_face_requests
        cur.execute("""
            INSERT INTO pending_face_requests (emp_id, request_type, image_path, status)
            VALUES (%s, %s, %s, 'pending')
        """, (employee_id, request_type, image_path))

        db.commit()

        # Get employee email for notification
        cur.execute("SELECT full_name, email FROM employees WHERE id = %s", (employee_id,))
        employee = cur.fetchone()

        # Send confirmation email to employee (non-blocking)
        try:
            if employee and employee.get('email'):
                email_service = EmailService(current_app)
                subject = "Face Enrollment Request Submitted"
                body = f"""
Dear {employee['full_name']},

Your face {request_type} request has been submitted successfully.

Request Details:
- Type: {request_type.title()}
- Status: Pending Admin Approval

Your request will be reviewed by the administrator. You will be notified once a decision is made.

Best regards,
FaceTrack Team
"""
                email_service.send_email(employee['email'], subject, body)
        except Exception:
            # email failures shouldn't break the request
            pass

        return jsonify({'status': 'success', 'message': 'Request submitted successfully. Waiting for admin approval.'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@bp.route('/cancel_face_request', methods=['POST'])
@login_required
def cancel_face_request():
    try:
        # Check authentication
        employee_id = session.get('employee_id')
        if not employee_id:
            return jsonify({'status': 'error', 'message': 'Authentication required'}), 401

        db = get_db()
        cur = db.cursor(dictionary=True)

        # Check if there's a pending request
        cur.execute("SELECT id, image_path FROM pending_face_requests WHERE emp_id = %s AND status = 'pending'", (employee_id,))
        pending_request = cur.fetchone()

        if not pending_request:
            return jsonify({'status': 'error', 'message': 'No pending request found'}), 400

        # Delete the image file if it exists
        if pending_request['image_path'] and os.path.exists(pending_request['image_path']):
            try:
                os.remove(pending_request['image_path'])
            except Exception:
                pass  # Ignore file deletion errors

        # Delete the pending request
        cur.execute("DELETE FROM pending_face_requests WHERE id = %s", (pending_request['id'],))
        db.commit()

        return jsonify({'status': 'success', 'message': 'Face request cancelled successfully'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
