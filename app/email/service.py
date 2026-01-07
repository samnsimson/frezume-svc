from sqlmodel.ext.asyncio.session import AsyncSession
from postmarker.core import PostmarkClient
from app.config import settings
from app.lib.constants import (
    EMAIL_FROM_ADDRESS,
    EMAIL_SUBJECT_VERIFY,
    EMAIL_VERIFICATION_BODY_TEMPLATE,
    ERROR_FAILED_TO_SEND_EMAIL,
)
from fastapi import HTTPException


class EmailService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.from_email = EMAIL_FROM_ADDRESS
        self.client = PostmarkClient(server_token=settings.postmark_server_token)

    def _build_email_body(self, token: str, is_link: bool = False) -> str:
        verification_content = f"{settings.app_url}/api/auth/verify-email?token={token}" if is_link else f"Your verification code: {token}"
        verification_type = "link" if is_link else "OTP"
        expiry_type = "link" if is_link else "code"
        return EMAIL_VERIFICATION_BODY_TEMPLATE.format(
            verification_type=verification_type,
            verification_content=verification_content,
            expiry_type=expiry_type
        )

    def send_email(self, to: str, subject: str, body: str) -> None:
        try: self.client.emails.send(From=self.from_email, To=to, Subject=subject, TextBody=body)
        except Exception as e: raise HTTPException(status_code=500, detail=ERROR_FAILED_TO_SEND_EMAIL.format(error=str(e)))

    def send_verification_otp(self, to: str, token: str) -> None:
        self.send_email(to, EMAIL_SUBJECT_VERIFY, self._build_email_body(token, is_link=False))

    def send_verification_link(self, to: str, token: str) -> None:
        self.send_email(to, EMAIL_SUBJECT_VERIFY, self._build_email_body(token, is_link=True))
