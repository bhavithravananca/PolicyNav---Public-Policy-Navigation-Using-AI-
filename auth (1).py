import re
import bcrypt
import jwt
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from config import *

def hash_text(text: str) -> str:
    return bcrypt.hashpw(text.encode(), bcrypt.gensalt()).decode()

def verify_text(text: str, hashed: str) -> bool:
    return bcrypt.checkpw(text.encode(), hashed.encode())

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least 1 uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least 1 lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least 1 number"
    return True, "Valid password"

def generate_token(email: str):
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except:
        return None

def generate_otp():
    return str(random.randint(100000, 999999))

def send_html_email(receiver, subject, html_content):
    msg = MIMEText(html_content, "html")
    msg["Subject"] = subject
    msg["From"] = EMAIL_ID
    msg["To"] = receiver

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ID, EMAIL_APP_PASSWORD)
        server.send_message(msg)

def send_otp_email(receiver, otp):
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 400px; margin: auto; background: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="color: #2c3e50;">PolicyNav Verification</h2>
            <p style="color: #555;">Use the OTP below to continue:</p>
            <div style="font-size: 28px; font-weight: bold; letter-spacing: 3px; color: #00b894; margin: 20px 0;">
                {otp}
            </div>
            <p style="color: #999; font-size: 12px;">This OTP is valid for 10 minutes.</p>
        </div>
    </body>
    </html>
    """
    send_html_email(receiver, "PolicyNav OTP Verification", html_content)

def send_admin_action_email(receiver, action_text):
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f8fafc; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; padding: 24px; border-radius: 12px;">
            <h2 style="color: #1e293b;">PolicyNav Account Notification</h2>
            <p style="font-size: 15px; color: #334155;">{action_text}</p>
            <p style="font-size: 13px; color: #64748b;">This action was performed by an administrator.</p>
        </div>
    </body>
    </html>
    """
    send_html_email(receiver, "PolicyNav Account Update", html_content)