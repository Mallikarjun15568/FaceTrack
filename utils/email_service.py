# ============================================
# FaceTrack Pro - Enhanced Email Service
# Comprehensive notification system
# ============================================

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Comprehensive email notification system for FaceTrack Pro"""

    def __init__(self, app=None):
        self.smtp_server = None
        self.smtp_port = None
        self.sender_email = None
        self.sender_password = None
        self.sender_name = "FaceTrack Pro"
        self.enabled = False

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.smtp_server = app.config.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = app.config.get("SMTP_PORT", 587)
        self.sender_email = app.config.get("SENDER_EMAIL")
        self.sender_password = app.config.get("SENDER_PASSWORD")
        self.sender_name = app.config.get("SENDER_NAME", "FaceTrack Pro")
        
        # Email enabled only if credentials present
        self.enabled = bool(self.sender_email and self.sender_password)
        
        if self.enabled:
            logger.info(f"Email service enabled: {self.sender_email}")
        else:
            logger.warning("Email service disabled: Missing SMTP credentials")

    # -----------------------------
    # Internal Helpers
    # -----------------------------
    def _connect(self):
        """Establish SMTP connection"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            return server
        except Exception as e:
            logger.error(f"SMTP connection failed: {e}")
            raise

    def _html_template(self, title, body, color="#4f46e5"):
        """Professional HTML email template with indigo branding"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin:0; padding:0; font-family: 'Segoe UI', Arial, sans-serif; background:#f3f4f6;">
            <div style="max-width:600px; margin:40px auto; background:#ffffff; border-radius:16px; overflow:hidden; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background:linear-gradient(135deg, {color}, #8b5cf6); color:#ffffff; padding:30px 20px; text-align:center;">
                    <h1 style="margin:0; font-size:28px; font-weight:700; letter-spacing:-0.5px;">
                        <span style="display:inline-block; width:40px; height:40px; background:rgba(255,255,255,0.2); border-radius:8px; line-height:40px; margin-right:10px;">🎯</span>
                        {self.sender_name}
                    </h1>
                    <p style="margin:10px 0 0 0; opacity:0.9; font-size:14px;">AI-Powered Attendance System</p>
                </div>
                
                <!-- Content -->
                <div style="padding:40px 30px;">
                    <h2 style="color:#111827; font-size:22px; margin:0 0 20px 0; font-weight:600;">{title}</h2>
                    <div style="color:#4b5563; line-height:1.7; font-size:15px;">
                        {body}
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background:#f9fafb; padding:20px 30px; border-top:1px solid #e5e7eb;">
                    <p style="margin:0; color:#6b7280; font-size:13px; text-align:center;">
                        © {datetime.now().year} FaceTrack Pro. All rights reserved.<br>
                        <span style="color:#9ca3af;">This is an automated notification. Please do not reply.</span>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    def _send(self, to_email, subject, html_body):
        """Send email with error handling"""
        if not self.enabled:
            logger.warning(f"Email not sent (disabled): {subject} to {to_email}")
            return False
            
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))

            server = self._connect()
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent: {subject} to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    # -----------------------------
    # Generic Email Method
    # -----------------------------
    def send_email(self, to_email, subject, body):
        """Send a generic email"""
        if not self.enabled:
            logger.warning("Email service disabled, cannot send email")
            return False

        html_body = self._html_template("FaceTrack Pro", f"<pre style='white-space: pre-wrap;'>{body}</pre>")
        return self._send(to_email, subject, html_body)

    # -----------------------------
    # Leave Management Emails
    # -----------------------------
    # -----------------------------
    # Leave Management Emails
    # -----------------------------
    def send_leave_approval(self, to_email, employee_name, leave_type, start_date, end_date, approver):
        """Send leave approval notification"""
        body = f"""
            <p style="margin-bottom:20px;">Dear <strong>{employee_name}</strong>,</p>
            <div style="background:#d1fae5; border-left:4px solid #10b981; padding:20px; border-radius:8px; margin:20px 0;">
                <p style="margin:0; color:#065f46; font-weight:600; font-size:16px;">✓ Your leave request has been APPROVED</p>
            </div>
            <table style="width:100%; border-collapse:collapse; margin:20px 0;">
                <tr>
                    <td style="padding:10px; background:#f9fafb; border:1px solid #e5e7eb; font-weight:600; width:40%;">Leave Type</td>
                    <td style="padding:10px; background:#ffffff; border:1px solid #e5e7eb;">{leave_type}</td>
                </tr>
                <tr>
                    <td style="padding:10px; background:#f9fafb; border:1px solid #e5e7eb; font-weight:600;">Duration</td>
                    <td style="padding:10px; background:#ffffff; border:1px solid #e5e7eb;">{start_date} to {end_date}</td>
                </tr>
                <tr>
                    <td style="padding:10px; background:#f9fafb; border:1px solid #e5e7eb; font-weight:600;">Approved By</td>
                    <td style="padding:10px; background:#ffffff; border:1px solid #e5e7eb;">{approver}</td>
                </tr>
            </table>
            <p style="margin-top:25px;">Please ensure proper handover before your leave starts.</p>
            <p style="margin-top:15px; color:#6b7280;">Best regards,<br><strong>HR Team</strong></p>
        """
        html = self._html_template("Leave Request Approved", body, "#10b981")
        return self._send(to_email, "✓ Leave Request Approved", html)

    def send_leave_rejection(self, to_email, employee_name, leave_type, start_date, end_date, reason, rejected_by):
        """Send leave rejection notification"""
        body = f"""
            <p style="margin-bottom:20px;">Dear <strong>{employee_name}</strong>,</p>
            <div style="background:#fee2e2; border-left:4px solid #ef4444; padding:20px; border-radius:8px; margin:20px 0;">
                <p style="margin:0; color:#991b1b; font-weight:600; font-size:16px;">✕ Your leave request has been REJECTED</p>
            </div>
            <table style="width:100%; border-collapse:collapse; margin:20px 0;">
                <tr>
                    <td style="padding:10px; background:#f9fafb; border:1px solid #e5e7eb; font-weight:600; width:40%;">Leave Type</td>
                    <td style="padding:10px; background:#ffffff; border:1px solid #e5e7eb;">{leave_type}</td>
                </tr>
                <tr>
                    <td style="padding:10px; background:#f9fafb; border:1px solid #e5e7eb; font-weight:600;">Duration</td>
                    <td style="padding:10px; background:#ffffff; border:1px solid #e5e7eb;">{start_date} to {end_date}</td>
                </tr>
                <tr>
                    <td style="padding:10px; background:#f9fafb; border:1px solid #e5e7eb; font-weight:600;">Reason</td>
                    <td style="padding:10px; background:#ffffff; border:1px solid #e5e7eb;">{reason}</td>
                </tr>
                <tr>
                    <td style="padding:10px; background:#f9fafb; border:1px solid #e5e7eb; font-weight:600;">Rejected By</td>
                    <td style="padding:10px; background:#ffffff; border:1px solid #e5e7eb;">{rejected_by}</td>
                </tr>
            </table>
            <p style="margin-top:25px;">Please contact HR if you need further clarification.</p>
            <p style="margin-top:15px; color:#6b7280;">Best regards,<br><strong>HR Team</strong></p>
        """
        html = self._html_template("Leave Request Rejected", body, "#ef4444")
        return self._send(to_email, "✕ Leave Request Rejected", html)
    
    # ========================================================================
    # DISABLED: Welcome Email (Commented out - not implemented in workflow)
    # ========================================================================
    # This feature was prepared but not integrated into the employee add workflow.
    # Requires temporary password generation and user account creation logic.
    # Keep: Leave approval/rejection emails remain the primary email notifications.
    # ========================================================================
    
    # def send_welcome_email(self, to_email, employee_name, emp_id, temp_password):
    #     """Send welcome email to new employee"""
    #     body = f"""
    #         <p style="margin-bottom:20px;">Dear <strong>{employee_name}</strong>,</p>
    #         <div style="background:#dbeafe; border-left:4px solid #3b82f6; padding:20px; border-radius:8px; margin:20px 0;">
    #             <p style="margin:0; color:#1e40af; font-weight:600; font-size:16px;">🎉 Welcome to FaceTrack Pro!</p>
    #         </div>
    #         <p>Your employee account has been successfully created. Please find your login credentials below:</p>
    #         <table style="width:100%; border-collapse:collapse; margin:20px 0;">
    #             <tr>
    #                 <td style="padding:10px; background:#f9fafb; border:1px solid #e5e7eb; font-weight:600; width:40%;">Employee ID</td>
    #                 <td style="padding:10px; background:#ffffff; border:1px solid #e5e7eb;">{emp_id}</td>
    #             </tr>
    #             <tr>
    #                 <td style="padding:10px; background:#f9fafb; border:1px solid #e5e7eb; font-weight:600;">Temporary Password</td>
    #                 <td style="padding:10px; background:#ffffff; border:1px solid #e5e7eb;"><code style="background:#fef3c7; padding:4px 8px; border-radius:4px; font-family:monospace;">{temp_password}</code></td>
    #             </tr>
    #         </table>
    #         <div style="background:#fef3c7; border:1px solid #fbbf24; padding:15px; border-radius:8px; margin:20px 0;">
    #             <p style="margin:0; color:#92400e; font-size:13px;">⚠️ <strong>Important:</strong> Please change your password after first login for security.</p>
    #         </div>
    #         <p style="margin-top:25px; color:#6b7280;">Best regards,<br><strong>HR Team</strong></p>
    #     """
    #     html = self._html_template("Welcome to FaceTrack Pro", body, "#3b82f6")
    #     return self._send(to_email, "🎉 Welcome to FaceTrack Pro", html)
    
    # ========================================================================
    # DISABLED: Attendance Alert Email (Commented out - may irritate employees)
    # ========================================================================
    # This feature was intentionally disabled to avoid sending automated
    # disciplinary emails to employees for late/absent attendance.
    # Management prefers positive reinforcement over automated alerts.
    # Keep: Leave approval/rejection and welcome emails remain active.
    # ========================================================================
    
    # def send_attendance_alert(self, to_email, employee_name, date, status, message):
    #     """Send attendance alert (late, absent, etc.)"""
    #     color = "#ef4444" if status == "absent" else "#f59e0b"
    #     icon = "❌" if status == "absent" else "⚠️"
    #     
    #     body = f"""
    #         <p style="margin-bottom:20px;">Dear <strong>{employee_name}</strong>,</p>
    #         <div style="background:#fee2e2; border-left:4px solid {color}; padding:20px; border-radius:8px; margin:20px 0;">
    #             <p style="margin:0; color:#991b1b; font-weight:600; font-size:16px;">{icon} Attendance Alert</p>
    #         </div>
    #         <p><strong>Date:</strong> {date}</p>
    #         <p><strong>Status:</strong> {status.upper()}</p>
    #         <p style="margin-top:20px;">{message}</p>
    #         <p style="margin-top:25px; color:#6b7280;">Please contact HR if this is incorrect.</p>
    #         <p style="margin-top:15px; color:#6b7280;">Best regards,<br><strong>HR Team</strong></p>
    #     """
    #     html = self._html_template("Attendance Alert", body, color)
    #     return self._send(to_email, f"{icon} Attendance Alert - {date}", html)
    
    # -----------------------------
    # System Notifications
    # -----------------------------
    def send_password_reset(self, to_email, employee_name, reset_token, expiry_minutes=30):
        """Send password reset link"""
        from flask import request
        # Get base URL from request or use default
        try:
            base_url = request.url_root.rstrip('/')
        except:
            base_url = "http://127.0.0.1:5000"
            
        reset_link = f"{base_url}/auth/reset-password?token={reset_token}"
        
        body = f"""
            <p style="margin-bottom:20px;">Dear <strong>{employee_name}</strong>,</p>
            <p>We received a request to reset your password. Click the button below to proceed:</p>
            <div style="text-align:center; margin:30px 0;">
                <a href="{reset_link}" style="display:inline-block; background:#4f46e5; color:#ffffff; padding:14px 32px; text-decoration:none; border-radius:8px; font-weight:600; font-size:16px;">
                    Reset Password
                </a>
            </div>
            <p style="font-size:13px; color:#6b7280;">Or copy this link: <code style="background:#f3f4f6; padding:4px 8px; border-radius:4px; font-size:12px;">{reset_link}</code></p>
            <div style="background:#fef3c7; border:1px solid #fbbf24; padding:15px; border-radius:8px; margin:20px 0;">
                <p style="margin:0; color:#92400e; font-size:13px;">⏰ This link expires in {expiry_minutes} minutes.</p>
            </div>
            <p style="margin-top:25px; font-size:13px; color:#6b7280;">If you didn't request this, please ignore this email.</p>
        """
        html = self._html_template("Password Reset Request", body)
        return self._send(to_email, "🔐 Password Reset Request", html)


# Global instance
email_service = EmailService()

