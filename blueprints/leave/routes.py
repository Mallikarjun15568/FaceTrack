from datetime import datetime, timedelta
from functools import wraps
from flask import session, flash, redirect, url_for, request, render_template, jsonify

from db_utils import fetchone, fetchall, execute
from utils.email_service import email_service

from . import bp as leave_bp

# ==================== DECORATORS ====================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') not in ['admin', 'hr']:
            flash('Access denied', 'error')
            return redirect(url_for('admin.dashboard.admin_dashboard'))
        return f(*args, **kwargs)
    return decorated

# ==================== EMPLOYEE ROUTES ====================


@leave_bp.route('/')
def index():
    leaves = fetchall("""
        SELECT l.*, e.full_name AS employee_name
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        ORDER BY l.applied_date DESC
    """)
    employees = fetchall("SELECT id, full_name FROM employees ORDER BY full_name ASC")

    # Get current user's leave balance if they have employee_id
    balance = None
    selected_employee = None
    employee_id = session.get('employee_id')
    
    # For admins, allow selecting which employee's balance to view
    if session.get('role') in ['admin', 'hr']:
        selected_emp_id = request.args.get('employee_id', type=int)
        if selected_emp_id:
            # Verify the selected employee exists
            selected_employee = fetchone("SELECT id, full_name FROM employees WHERE id = %s", (selected_emp_id,))
            if selected_employee:
                balance = fetchone("""
                    SELECT * FROM leave_balance WHERE employee_id = %s
                """, (selected_emp_id,))
        else:
            # For admins without selection, check if they have an employee record
            user_id = session.get('user_id')
            if user_id:
                emp = fetchone("SELECT id, full_name FROM employees WHERE user_id = %s", (user_id,))
                if emp:
                    balance = fetchone("""
                        SELECT * FROM leave_balance WHERE employee_id = %s
                    """, (emp['id'],))
                    selected_employee = emp
    else:
        # For regular employees, show their own balance
        if employee_id:
            balance = fetchone("""
                SELECT * FROM leave_balance WHERE employee_id = %s
            """, (employee_id,))
            selected_employee = fetchone("SELECT id, full_name FROM employees WHERE id = %s", (employee_id,))

    return render_template('leave/leave_list.html', leaves=leaves, employees=employees, balance=balance, selected_employee=selected_employee, employee_view=False, role=session.get('role'))


# ==================== ADMIN: LEAVE BALANCE ADJUSTMENT ====================
@leave_bp.route('/adjust_balance', methods=['POST'])
def adjust_balance():
    employee_id = request.form.get('employee_id')
    leave_type = request.form.get('leave_type')
    operation = request.form.get('operation')
    days = request.form.get('days')
    reason = request.form.get('reason', '')

    # Validate input
    if not employee_id or not leave_type or not operation or not days:
        flash('All fields are required.', 'error')
        return redirect(url_for('leave.index'))

    try:
        days = int(days)
        if days <= 0:
            raise ValueError
    except Exception:
        flash('Days must be a positive number.', 'error')
        return redirect(url_for('leave.index'))

    if operation not in ['add', 'reduce']:
        flash('Invalid operation.', 'error')
        return redirect(url_for('leave.index'))

    # Calculate adjustment
    adjust_days = days if operation == 'add' else -days

    allowed_types = ['casual_leave', 'sick_leave', 'personal_leave', 'emergency_leave']
    if leave_type not in allowed_types:
        flash('Invalid leave type.', 'error')
        return redirect(url_for('leave.index'))

    # Transaction safety
    from utils.db import get_db
    db = get_db()
    try:
        # Check if leave_balance row exists
        balance = fetchone("SELECT * FROM leave_balance WHERE employee_id = %s", (employee_id,))
        if not balance:
            # Optionally, create a new row if missing (admin only)
            execute("""
                INSERT INTO leave_balance (employee_id, casual_leave, sick_leave, personal_leave, emergency_leave)
                VALUES (%s, 0, 0, 0, 0)
            """, (employee_id,))
        # Update the leave balance
        execute(
            f"UPDATE leave_balance SET {leave_type} = {leave_type} + %s WHERE employee_id = %s",
            (adjust_days, employee_id)
        )
        flash(f'Leave balance {operation}d successfully.', 'success')
    except Exception as e:
        flash('Failed to adjust leave balance.', 'error')
    return redirect(url_for('leave.index'))


@leave_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    employee_id = request.args.get('employee_id', type=int)
    if not employee_id:
        employee_id = session.get('employee_id')
    
    # Security check: only admin/hr can apply for others
    if session.get('role') not in ['admin', 'hr'] and employee_id != session.get('employee_id'):
        flash('Access denied', 'error')
        return redirect(url_for('leave.index'))

    if request.method == 'POST':
        leave_type = request.form.get('leave_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason')

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        total_days = (end - start).days + 1

        if total_days <= 0:
            flash('Invalid date range', 'error')
            return redirect(url_for('leave.index'))

        balance = fetchone("""
            SELECT * FROM leave_balance WHERE employee_id = %s
        """, (employee_id,))

        if not balance:
            flash("Leave balance not found. Contact admin.", "error")
            return redirect(url_for("leave.index"))

        leave_map = {
            'Casual Leave': 'casual_leave',
            'Sick Leave': 'sick_leave',
            'Personal Leave': 'personal_leave',
            'Emergency Leave': 'emergency_leave'
        }

        column = leave_map.get(leave_type)
        if column and balance[column] < total_days:
            flash('Insufficient leave balance', 'error')
            return redirect(url_for('leave.index'))

        try:
            execute("""
                INSERT INTO leaves
                (employee_id, leave_type, start_date, end_date, total_days, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (employee_id, leave_type, start_date, end_date, total_days, reason))
            flash('Leave application submitted', 'success')
            return redirect(url_for('leave.index'))
        except Exception as e:
            flash('Failed to submit leave application', 'error')
            return redirect(url_for('leave.index'))

    balance = fetchone("""
        SELECT * FROM leave_balance WHERE employee_id = %s
    """, (employee_id,))

    if not balance:
        flash("Leave balance not found. Contact admin.", "error")
        return redirect(url_for("leave.index"))

    employee = fetchone("SELECT full_name FROM employees WHERE id = %s", (employee_id,))
    if not employee:
        flash('Employee not found', 'error')
        return redirect(url_for('leave.index'))
    employee_name = employee['full_name']

    # Get today's date for date input min attribute
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')

    return render_template('leave/apply_leave.html', balance=balance, today=today, employee_name=employee_name)


@leave_bp.route('/cancel/<int:leave_id>', methods=['POST'])
@login_required
def cancel(leave_id):
    employee_id = session.get('employee_id')

    leave = fetchone("""
        SELECT * FROM leaves
        WHERE id = %s AND employee_id = %s AND status = 'pending'
    """, (leave_id, employee_id))

    if not leave:
        flash('Cannot cancel this leave', 'error')
        return redirect(url_for('leave.index'))

    execute("DELETE FROM leaves WHERE id = %s", (leave_id,))
    flash('Leave cancelled', 'success')
    return redirect(url_for('leave.index'))

# ==================== ADMIN ROUTES ====================

@leave_bp.route('/approve/<int:leave_id>', methods=['POST'])
@admin_required
def approve(leave_id):
    approver_id = session.get('employee_id')

    leave = fetchone("""
        SELECT * FROM leaves WHERE id = %s AND status = 'pending'
    """, (leave_id,))

    if not leave:
        flash('Leave not found', 'error')
        return redirect(url_for('leave.index'))

    if leave['employee_id'] == approver_id and requester_role != 'admin':
        flash('You cannot approve your own leave', 'error')
        return redirect(url_for('leave.index'))

    # Get requester's role
    emp = fetchone("SELECT user_id FROM employees WHERE id = %s", (leave['employee_id'],))
    if not emp:
        flash('Employee not found', 'error')
        return redirect(url_for('leave.index'))
    user = fetchone("SELECT role FROM users WHERE id = %s", (emp['user_id'],))
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('leave.index'))
    requester_role = user['role']
    approver_role = session.get('role')

    # Hierarchy check
    if requester_role == 'employee':
        if approver_role not in ['hr', 'admin']:
            flash('Only HR or Admin can approve employee leaves', 'error')
            return redirect(url_for('leave.index'))
    elif requester_role == 'hr':
        if approver_role != 'admin':
            flash('Only Admin can approve HR leaves', 'error')
            return redirect(url_for('leave.index'))
    elif requester_role == 'admin':
        if approver_role != 'admin':
            flash('Only Admin can approve admin leaves (manual approval)', 'error')
            return redirect(url_for('leave.index'))

    execute("""
        UPDATE leaves
        SET status = 'approved',
            approved_by = %s,
            approved_date = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (approver_id, leave_id))

    leave_map = {
        'Casual Leave': 'casual_leave',
        'Sick Leave': 'sick_leave',
        'Personal Leave': 'personal_leave',
        'Emergency Leave': 'emergency_leave'
    }

    column = leave_map.get(leave['leave_type'])
    if column:
        allowed_columns = set(leave_map.values())
        if column in allowed_columns:
            execute(
                "UPDATE leave_balance SET " + column + " = " + column + " - %s WHERE employee_id = %s",
                (leave['total_days'], leave['employee_id'])
            )

    # Send approval email (best-effort, don't break flow on email errors)
    try:
        emp = fetchone("SELECT full_name, email FROM employees WHERE id = %s", (leave['employee_id'],))
        if emp and emp.get('email'):
            approver_name = session.get('full_name', 'HR')
            email_service.send_leave_approval(
                emp['email'], emp.get('full_name', ''), leave['leave_type'], leave['start_date'], leave['end_date'], approver_name
            )
    except Exception:
        pass

    flash('Leave approved', 'success')
    return redirect(url_for('leave.index'))


@leave_bp.route('/reject/<int:leave_id>', methods=['POST'])
@admin_required
def reject(leave_id):
    reason = request.form.get('rejection_reason', 'No reason provided')
    approver_id = session.get('employee_id')

    leave = fetchone("""
        SELECT * FROM leaves WHERE id = %s AND status = 'pending'
    """, (leave_id,))

    if not leave:
        flash('Leave not found', 'error')
        return redirect(url_for('leave.index'))

    if leave['employee_id'] == approver_id and requester_role != 'admin':
        flash('You cannot reject your own leave', 'error')
        return redirect(url_for('leave.index'))

    # Get requester's role
    emp = fetchone("SELECT user_id FROM employees WHERE id = %s", (leave['employee_id'],))
    if not emp:
        flash('Employee not found', 'error')
        return redirect(url_for('leave.index'))
    user = fetchone("SELECT role FROM users WHERE id = %s", (emp['user_id'],))
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('leave.index'))
    requester_role = user['role']
    approver_role = session.get('role')

    # Hierarchy check
    if requester_role == 'employee':
        if approver_role not in ['hr', 'admin']:
            flash('Only HR or Admin can reject employee leaves', 'error')
            return redirect(url_for('leave.index'))
    elif requester_role == 'hr':
        if approver_role != 'admin':
            flash('Only Admin can reject HR leaves', 'error')
            return redirect(url_for('leave.index'))
    elif requester_role == 'admin':
        if approver_role != 'admin':
            flash('Only Admin can reject admin leaves (manual approval)', 'error')
            return redirect(url_for('leave.index'))

    # ✅ Transaction safety
    from utils.db import get_db
    db = get_db()
    try:
        db.start_transaction()
    except AttributeError:
        pass
    
    try:
        # Update leave status
        execute("""
            UPDATE leaves
            SET status = 'rejected',
                approved_by = %s,
                approved_date = CURRENT_TIMESTAMP,
                rejection_reason = %s
            WHERE id = %s AND status = 'pending'
        """, (approver_id, reason, leave_id))
        
        db.commit()

        # Send rejection email (best-effort)
        try:
            lv = fetchone("SELECT employee_id, leave_type, start_date, end_date FROM leaves WHERE id = %s", (leave_id,))
            if lv:
                emp = fetchone("SELECT full_name, email FROM employees WHERE id = %s", (lv['employee_id'],))
                if emp and emp.get('email'):
                    rejected_by = session.get('full_name', 'HR')
                    email_service.send_leave_rejection(
                        emp['email'], emp.get('full_name', ''), lv.get('leave_type'), lv.get('start_date'), lv.get('end_date'), reason, rejected_by
                    )
        except Exception:
            pass

        flash('Leave rejected', 'success')
        return redirect(url_for('leave.index'))
        
    except Exception as e:
        db.rollback()
        flash('Failed to reject leave', 'error')
        return redirect(url_for('leave.index'))

# ==================== API ====================

@leave_bp.route('/api/balance')
@login_required
def api_balance():
    employee_id = session.get('employee_id')

    balance = fetchone("""
        SELECT * FROM leave_balance WHERE employee_id = %s
    """, (employee_id,))

    if not balance:
        return jsonify({'error': 'Not found'}), 404

    return jsonify({
        'casual_leave': balance['casual_leave'],
        'sick_leave': balance['sick_leave'],
        'personal_leave': balance['personal_leave'],
        'emergency_leave': balance['emergency_leave']
    })


@leave_bp.route('/api/calendar')
@login_required
def api_calendar():
    """Get calendar view of leaves for all employees in a month"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    if not year or not month:
        # Default to current month
        now = datetime.now()
        year = now.year
        month = now.month

    # Only admin/HR can view team calendar
    role = session.get('role')
    if role not in ['admin', 'hr']:
        return jsonify({'error': 'Access denied'}), 403

    from utils.db import get_db
    db = get_db()
    cur = db.cursor(dictionary=True)

    # Get all approved leaves for this month
    cur.execute("""
        SELECT
            l.start_date,
            l.end_date,
            l.leave_type,
            e.full_name as employee_name,
            e.id as employee_id
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        WHERE l.status = 'approved'
          AND (
              (YEAR(l.start_date) = %s AND MONTH(l.start_date) = %s)
              OR (YEAR(l.end_date) = %s AND MONTH(l.end_date) = %s)
              OR (l.start_date <= %s AND l.end_date >= %s)
          )
        ORDER BY l.start_date
    """, (year, month, year, month, f"{year}-{month:02d}-01", f"{year}-{month:02d}-01"))

    leave_records = cur.fetchall()

    # Generate calendar data for the month
    from datetime import date
    calendar_data = []
    days_in_month = (date(year + (1 if month == 12 else 0), (month % 12) + 1, 1) - timedelta(days=1)).day

    # Create a map of date -> list of employees on leave
    leave_map = {}
    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        leave_map[date_str] = []

    # Populate leave map
    for leave in leave_records:
        current_date = leave['start_date']
        while current_date <= leave['end_date']:
            if current_date.year == year and current_date.month == month:
                date_str = current_date.strftime('%Y-%m-%d')
                leave_map[date_str].append({
                    'employee_name': leave['employee_name'],
                    'employee_id': leave['employee_id'],
                    'leave_type': leave['leave_type']
                })
            current_date += timedelta(days=1)

    # Convert to calendar format
    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        employees_on_leave = leave_map[date_str]

        calendar_data.append({
            'date': date_str,
            'employees_on_leave': employees_on_leave,
            'leave_count': len(employees_on_leave)
        })

    cur.close()

    return jsonify({
        'status': 'ok',
        'month': f"{year}-{month:02d}",
        'calendar': calendar_data
    })
