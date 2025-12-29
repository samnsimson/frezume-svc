from datetime import datetime, timezone
from typing import Literal
from uuid import UUID
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database.models import Verification
from app.verification.repository import VerificationRepository
from app.lib.utils import generate_otp, generate_jwt_token


class VerificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.verification_repository = VerificationRepository(session)

    async def create_verification(self, identifier: str, user_id: UUID, type: Literal['otp', 'link'] = 'otp') -> Verification:
        if type == 'otp': token = generate_otp()
        else: token = generate_jwt_token({"user_id": user_id})
        verification = Verification(user_id=user_id, identifier=identifier, token=token)
        data = await self.verification_repository.create(verification, commit=False)
        print(f"Verification: {data}")
        return data

    async def verify(self, token: str, identifier: str, user_id: UUID) -> bool:
        verification = await self.verification_repository.get_by_token(token)
        if not verification: raise HTTPException(status_code=401, detail="Invalid token")
        if verification.user_id != user_id: raise HTTPException(status_code=401, detail="Token does not belong to the user")
        if verification.identifier != identifier: raise HTTPException(status_code=401, detail="Invalid identifier")
        if verification.expires_at < datetime.now(timezone.utc): raise HTTPException(status_code=401, detail="Token expired")
        await self.verification_repository.delete(verification.id)
        return True
