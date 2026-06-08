"""
Validazione token Azure Entra External ID e dependency FastAPI.

Flusso:
  1. Il frontend autentica l'utente con MSAL e ottiene un access token Azure.
  2. Ogni richiesta invia il token come "Authorization: Bearer <token>".
  3. Il backend scarica le chiavi pubbliche Azure (JWKS) con cache TTL 1h.
  4. Il token viene verificato (firma RS256 + audience + exp).
  5. L'utente viene sincronizzato nel DB locale (creazione al primo accesso).
"""

import time
from typing import Optional

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.db.session import get_db
from app.entity.user_entity import User, UserRole
from app.repository.user_repository import UserRepository

settings = get_settings()

# ── JWKS cache ─────────────────────────────────────────────────────────────────
_jwks_cache: dict = {}
_jwks_fetched_at: float = 0.0
_JWKS_TTL = 3600.0  # 1 ora


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    now = time.monotonic()
    if not _jwks_cache or (now - _jwks_fetched_at) > _JWKS_TTL:
        url = (
            f"https://login.microsoftonline.com/"
            f"{settings.azure_entra_tenant_id}/discovery/v2.0/keys"
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_fetched_at = now
    return _jwks_cache


async def _validate_azure_token(token: str) -> dict:
    """Verifica firma RS256 e claims del token Azure Entra."""
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token malformato")

    kid = header.get("kid")
    jwks = await _get_jwks()
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)

    if key is None:
        # Forza refresh JWKS alla prossima chiamata (chiave ruotata)
        _jwks_cache.clear()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Chiave pubblica non trovata")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.azure_entra_client_id,
        )
    except JWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token non valido: {exc}")

    return payload


# ── Dependency: utente autenticato ─────────────────────────────────────────────

async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Valida il Bearer token Azure e sincronizza l'utente nel DB.
    Al primo accesso crea il record; alle chiamate successive aggiorna
    last_login e il ruolo (in caso di cambio su Azure).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Token di autenticazione mancante",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.removeprefix("Bearer ")
    payload = await _validate_azure_token(token)

    oid: str = payload.get("oid", "")
    if not oid:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token privo di Object ID")

    email: str = payload.get("email") or payload.get("preferred_username", "")
    nome: Optional[str] = payload.get("name")
    roles: list[str] = payload.get("roles", [])
    ruolo = (
        UserRole.ADMIN
        if settings.azure_entra_admin_role in roles
        else UserRole.USER
    )

    repo = UserRepository(db)
    user = await repo.find_by_azure_id(oid)

    if user is None:
        user = User(azure_oid=oid, email=email, nome=nome, ruolo=ruolo)
        user = await repo.save(user)
    else:
        user.ruolo = ruolo
        await repo.update_last_login(user)

    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabilitato")

    return user


# ── Dependency: solo admin ─────────────────────────────────────────────────────

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Richiede ruolo ADMIN; solleva 403 altrimenti."""
    if not current_user.is_admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Accesso riservato agli amministratori",
        )
    return current_user
