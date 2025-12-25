from sqlmodel import Session
from postmarker.core import PostmarkClient
from app.config import settings
from fastapi import HTTPException


class EmailService:
    def __init__(self, session: Session):
        self.session = session
        self.from_email = 'no-reply@wailist.com'
        self.client = PostmarkClient(server_token=settings.postmark_server_token)

    def send_email(self, to: str, subject: str, body: str):
        try: self.client.emails.send(From=self.from_email, To=to, Subject=subject, HtmlBody=body)
        except Exception as e: raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
