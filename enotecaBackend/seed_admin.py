"""
seed_admin.py — crea il primo utente admin nel DB.

Da eseguire UNA SOLA VOLTA dopo aver creato le tabelle con Alembic,
prima di configurare Azure Entra o durante i test locali.

Uso:
    python seed_admin.py

Il record creato avrà azure_oid fittizio — una volta configurato Azure Entra,
al primo login Azure il record viene aggiornato automaticamente con l'OID reale
(la ricerca avviene per email come fallback, oppure si elimina e si ricrea).
"""
import asyncio
import uuid
import sys
import os

# Aggiunge la root del progetto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import AsyncSessionLocal
from app.entity.user_entity import User, UserRole


ADMIN_EMAIL     = "admin@enoteca.local"
ADMIN_NOME      = "Amministratore Enoteca"
ADMIN_AZURE_OID = f"seed-admin-{uuid.uuid4()}"  # OID fittizio per i test locali


async def seed():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.email == ADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Admin già presente: {existing.email} (role={existing.ruolo.value})")
            return

        admin = User(
            id=str(uuid.uuid4()),
            azure_oid=ADMIN_AZURE_OID,
            email=ADMIN_EMAIL,
            nome=ADMIN_NOME,
            ruolo=UserRole.ADMIN,
            is_active=True,
            hashed_password="",
        )
        session.add(admin)
        await session.commit()
        print(f"Admin creato con successo:")
        print(f"  email:     {ADMIN_EMAIL}")
        print(f"  azure_oid: {ADMIN_AZURE_OID}  ← sostituito automaticamente al primo login Azure")
        print(f"  role:      {UserRole.ADMIN.value}")


if __name__ == "__main__":
    asyncio.run(seed())
