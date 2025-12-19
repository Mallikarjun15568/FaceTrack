from flask import render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from functools import wraps

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
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated

# ==================== EMPLOYEE ROUTES ====================

@leave_bp.route('/')
@login_required
def index():
    role = session.get('role')
    employee_id = session.get('employee_id')

    if role in ['admin', 'hr']:
        leaves = fetchall("""
            SELECT l.*, e.full_name AS employee_name
            FROM leaves l
            JOIN employees e ON l.employee_id = e.id
            ORDER BY l.applied_date DESC
        """)
    else:
        leaves = fetchall("""
            SELECT l.*, e.full_name AS employee_name
            FROM leaves l
            JOIN employees e ON l.employee_id = e.id
            WHERE l.employee_id = %s
            ORDER BY l.applied_date DESC
        """, (employee_id,))

    balance = fetchone("""
        SELECT * FROM leave_balance WHERE employee_id = %s
    """, (employee_id,))

    return render_template(
        'leave/leave_list.html',
        leaves=leaves,
        balance=balance,
        role=role
    )


@leave_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    employee_id = session.get('employee_id')

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
            return redirect(url_for('leave.apply'))

        balance = fetchone("""
            SELECT * FROM leave_balance WHERE employee_id = %s
        """, (employee_id,))

        if not balance:
            flash("Leave balance not found. Contact admin.", "error")
            return redirect(url_for("leave.apply"))

        leave_map = {
            'Casual Leave': 'casual_leave',
            'Sick Leave': 'sick_leave',
            'Vacation Leave': 'vacation_leave',
            'Work From Home': 'work_from_home'
        }

        column = leave_map.get(leave_type)
        if column and balance[column] < total_days:
            flash('Insufficient leave balance', 'error')
            return redirect(url_for('leave.apply'))

        execute("""
            INSERT INTO leaves
            (employee_id, leave_type, start_date, end_date, total_days, reason)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (employee_id, leave_type, start_date, end_date, total_days, reason))

        flash('Leave application submitted', 'success')
        return redirect(url_for('leave.index'))

    balance = fetchone("""
        SELECT * FROM leave_balance WHERE employee_id = %s
    """, (employee_id,))

    if not balance:
        flash("Leave balance not found. Contact admin.", "error")
        return redirect(url_for("leave.apply"))

    return render_template('leave/apply_leave.html', balance=balance)


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
        'Vacation Leave': 'vacation_leave',
        'Work From Home': 'work_from_home'
    }

    column = leave_map.get(leave['leave_type'])
    if column:
        execute(f"""
            UPDATE leave_balance
            SET {column} = {column} - %s
            WHERE employee_id = %s
        """, (leave['total_days'], leave['employee_id']))

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

    # Update leave status
    execute("""
        UPDATE leaves
        SET status = 'rejected',
            approved_by = %s,
            approved_date = CURRENT_TIMESTAMP,
            rejection_reason = %s
        WHERE id = %s AND status = 'pending'
    """, (approver_id, reason, leave_id))

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
        'vacation_leave': balance['vacation_leave'],
        'work_from_home': balance['work_from_home']
    })
