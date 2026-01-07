import logging
from app.email.service import EmailService
from sqlmodel.ext.asyncio.session import AsyncSession


logger = logging.getLogger(__name__)


def send_verification_email(email: str, token: str, session: AsyncSession):
    try:
        logger.info(f"Sending verification email to {email} with token {token}")
        email_service = EmailService(session)
        email_service.send_verification_otp(email, token)
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
