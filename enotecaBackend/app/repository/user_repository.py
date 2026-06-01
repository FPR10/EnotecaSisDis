"""User repository - query sul DB relative agli utenti
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.user_entity import User

class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, user_id: str) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def find_by_azure_id(self, azure_oid: str) -> Optional[User]:
        """
        Cerca un utente per ID di Azure.
        Usato in fase di autenticazione (auth_service) per sincronizzare
        il record locale con i dati su Azure
        """
        query = select(User).where(User.azure_oid == azure_oid)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_last_login(self, user: User) -> None:
        from datetime import datetime, timezone
        user.last_login = datetime.now(timezone.utc)
        await self.session.flush()
