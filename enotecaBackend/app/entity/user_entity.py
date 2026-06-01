"""
User -- tabella per gestire l'autenticazione.
Il ruolo ADMIN è l'unico autorizzato ad aggiungere, modificare o eliminare vini dal catalogo.

"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Enum as SAEnum, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.db.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"   # può scrivere sul catalogo
    USER = "user"     # sola lettura + funzionalità AI


class User(Base):
    __tablename__ = "users"

    # Chiave primaria
    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Identificatore utente",
    )

    # Credenziali
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Email (usata come username per il login)",
    )
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Password hashata (bcrypt)"
    )

    # Profilo
    nome_utente: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Nome visualizzato dell'utente",
    )

    # Ruolo
    ruolo: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.USER,
        comment="Ruolo: admin (scrittura catalogo) o user (sola lettura)",
    )

   
    # --- Metadati di sistema ---
    data_registrazione: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="Data registrazione",
    )
    ultimo_accesso: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Ultimo accesso riuscito",
    )

    @property
    def is_admin(self) -> bool:
        """Shortcut per verificare il ruolo admin nei service e controller."""
        return self.ruolo == UserRole.ADMIN

    def __repr__(self) -> str:
        return f"<User id={self.id} email='{self.email}' role={self.ruolo.value}>"
