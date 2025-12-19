# ============================================
# FaceTrack Pro - Email Service
# Leave Approval / Rejection Notifications
# ============================================

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


class EmailService:
    """Handles critical email notifications only (Leave workflow)"""

    def __init__(self, app=None):
        self.smtp_server = None
        self.smtp_port = None
        self.sender_email = None
        self.sender_password = None
        self.sender_name = "FaceTrack Pro"

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.smtp_server = app.config.get("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = app.config.get("SMTP_PORT", 587)
        self.sender_email = app.config.get("SENDER_EMAIL")
        self.sender_password = app.config.get("SENDER_PASSWORD")
        self.sender_name = app.config.get("SENDER_NAME", "FaceTrack Pro")

    # -----------------------------
    # Internal Helpers
    # -----------------------------
    def _connect(self):
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.sender_email, self.sender_password)
        return server

    def _html_template(self, title, body):
        return f"""
        <html>
        <body style="font-family: Arial; background:#f4f4f4; padding:20px;">
            <div style="max-width:600px; background:#fff; margin:auto; border-radius:8px;">
                <div style="background:#3b82f6; color:#fff; padding:20px; text-align:center;">
                    <h2>{self.sender_name}</h2>
                </div>
                <div style="padding:30px;">
                    <h3>{title}</h3>
                    {body}
                </div>
                <div style="padding:15px; text-align:center; color:#999; font-size:12px;">
                    © {datetime.now().year} FaceTrack Pro
                </div>
            </div>
        </body>
        </html>
        """

    def _send(self, to_email, subject, html_body):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        server = self._connect()
        server.send_message(msg)
        server.quit()

    # -----------------------------
    # Public APIs (ONLY 2)
    # -----------------------------
    def send_leave_approval(self, to_email, employee_name, leave_type, start_date, end_date, approver):
        body = f"""
            <p>Dear {employee_name},</p>
            <p>Your leave request has been <b style="color:green;">APPROVED</b>.</p>
            <p>
                <b>Type:</b> {leave_type}<br>
                <b>Duration:</b> {start_date} to {end_date}<br>
                <b>Approved By:</b> {approver}
            </p>
            <p>Regards,<br>HR Team</p>
        """
        html = self._html_template("Leave Approved", body)
        self._send(to_email, "Leave Request Approved", html)

    def send_leave_rejection(self, to_email, employee_name, leave_type, start_date, end_date, reason, rejected_by):
        body = f"""
            <p>Dear {employee_name},</p>
            <p>Your leave request has been <b style="color:red;">REJECTED</b>.</p>
            <p>
                <b>Type:</b> {leave_type}<br>
                <b>Duration:</b> {start_date} to {end_date}<br>
                <b>Reason:</b> {reason}<br>
                <b>Rejected By:</b> {rejected_by}
            </p>
            <p>Regards,<br>HR Team</p>
        """
        html = self._html_template("Leave Rejected", body)
        self._send(to_email, "Leave Request Rejected", html)


# Global instance
email_service = EmailService()
