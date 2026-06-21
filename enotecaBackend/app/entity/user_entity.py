"""
Entity User — gestione utenti sincronizzati da Azure Entra External ID.

Con Azure Entra:
  - Le credenziali (password) sono gestite interamente da Azure
  - Il nostro DB conserva solo i dati applicativi: ruolo, last_login, is_active
  - L'identificatore univoco è azure_oid (Object ID di Azure)
  - hashed_password rimane nel modello per compatibilità SQLAlchemy ma è sempre ""
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
    ADMIN = "admin"   # ruolo assegnato su portale Azure → Enoteca.Admin
    USER  = "user"    # ruolo di default per tutti gli altri utenti


class User(Base):
    __tablename__ = "users"

    # Chiave primaria interna
    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Identificatore interno (UUID v4)",
    )

    # Identificatore azure
    azure_oid: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Object ID di Azure Entra — identificatore univoco Microsoft, immutabile",
    )

    # Profilo (sincronizzato da Azure al login) 
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Email dell'utente — sincronizzata da Azure, può cambiare",
    )
    nome: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Nome completo — sincronizzato dal campo 'name' del token Azure",
    )

    # Ruolo
    ruolo: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.USER,
        comment="Ruolo: sincronizzato dagli App Roles di Azure Entra ad ogni login",
    )

    # Stato account
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="False = account disabilitato a livello applicativo (indipendente da Azure)",
    )

    # Campo legacy — non usato con Azure Entra 
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        comment="Non usato con Azure Entra — mantenuto per compatibilità schema",
    )

    # Metadati extra
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="Data primo accesso (creazione record)",
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="Data ultimo accesso verificato",
    )

    @property
    def is_admin(self) -> bool:
        return self.ruolo == UserRole.ADMIN

    def __repr__(self) -> str:
        return f"<User oid={self.azure_oid} email='{self.email}' role={self.ruolo.value}>"
