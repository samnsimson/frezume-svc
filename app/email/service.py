from sqlmodel.ext.asyncio.session import AsyncSession
from postmarker.core import PostmarkClient
from app.config import settings
from fastapi import HTTPException


class EmailService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.from_email = 'no-reply@wailist.com'
        self.client = PostmarkClient(server_token=settings.postmark_server_token)

    def _build_email_body(self, token: str, is_link: bool = False) -> str:
        verification_content = f"{settings.app_url}/api/auth/verify-email?token={token}" if is_link else f"Your verification code: {token}"
        return f"""Email Verification
            Thank you for signing up! Please use the following {'link' if is_link else 'OTP'} to verify your email address:
            {verification_content}
            This {'link' if is_link else 'code'} will expire in 10 minutes. If you didn't request this verification, please ignore this email.
            Best regards,
            Resumevx Team"""

    def send_email(self, to: str, subject: str, body: str) -> None:
        try: self.client.emails.send(From=self.from_email, To=to, Subject=subject, TextBody=body)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    def send_verification_otp(self, to: str, token: str) -> None:
        self.send_email(to, "Verify your email", self._build_email_body(token, is_link=False))

    def send_verification_link(self, to: str, token: str) -> None:
        self.send_email(to, "Verify your email", self._build_email_body(token, is_link=True))
