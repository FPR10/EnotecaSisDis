"""
Authentication service — sincronizzazione utenti con Azure Entra.
"""

from typing import Optional

from app.config.logging import get_logger
from app.entity.user_entity import User, UserRole
from app.repository.user_repository import UserRepository

logger = get_logger(__name__)


class AuthenticationServiceError(Exception):
    """Errore durante la sincronizzazione o il recupero di un utente."""


class AuthenticationService:
    """
    Wrapper sullo UserRepository: sincronizza gli utenti Azure Entra nel DB
    locale al login e ne espone il profilo.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def sincronizza_da_azure(self,*,azure_oid: str,email: str,nome: Optional[str],ruolo: UserRole) -> User:
        """
        PRIMO ACCESSO:
        - crea l'utente
        
        UTENTE GIA' REGISTRATO:
        - risincronzizazione di email, nome e ruolo + aggiornamento del last_login
       
        """
        if not azure_oid:
            raise AuthenticationServiceError("Azure Object ID mancante")

        utente = await self.user_repository.find_by_azure_id(azure_oid)

        if utente is None:
            utente = User(azure_oid=azure_oid, email=email, nome=nome, ruolo=ruolo)
            utente = await self.user_repository.save(utente)
            logger.debug(f"Auth: creato nuovo utente per azure_oid={azure_oid}")
        else:
            utente.email = email
            utente.nome = nome
            utente.ruolo = ruolo
            await self.user_repository.update_last_login(utente)

        return utente

    async def get_utente(self, user_id: str) -> User:
        """Recupera un utente per id interno; solleva errore se non esiste."""
        utente = await self.user_repository.find_by_id(user_id)
        if utente is None:
            raise AuthenticationServiceError(f"Utente con id {user_id} non trovato")
        return utente

    async def get_utente_by_email(self, email: str) -> Optional[User]:
        """Recupera un utente per email (None se non trovato)."""
        return await self.user_repository.find_by_email(email)
