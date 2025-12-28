from sqlmodel.ext.asyncio.session import AsyncSession
from postmarker.core import PostmarkClient
from app.config import settings
from fastapi import HTTPException


class EmailService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.from_email = 'no-reply@wailist.com'
        self.client = PostmarkClient(server_token=settings.postmark_server_token)

    def send_email(self, to: str, subject: str, body: str):
        try: self.client.emails.send(From=self.from_email, To=to, Subject=subject, TextBody=body)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    def send_verification_otp(self, to: str, token: str):
        subject = "Verify your email"
        body = f"""Email Verification
                Thank you for signing up! Please use the following OTP to verify your email address:
                Your verification code: {token}
                This code will expire in 10 minutes. If you didn't request this verification, please ignore this email.
                Best regards,
                Resumevx Team"""
        self.send_email(to, subject, body)

    def send_verification_link(self, to: str, token: str):
        subject = "Verify your email"
        body = f"""Email Verification
                Thank you for signing up! Please use the following link to verify your email address:
                {settings.app_url}/api/auth/verify-email?token={token}
                This link will expire in 10 minutes. If you didn't request this verification, please ignore this email.
                Best regards,
                Resumevx Team"""
        self.send_email(to, subject, body)
