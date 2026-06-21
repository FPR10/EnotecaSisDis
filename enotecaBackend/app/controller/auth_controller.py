"""Auth controller — profilo dell'utente autenticato.

Login e registrazione sono gestiti interamente da Azure Entra External ID
(MSAL lato frontend): qui esponiamo solo la lettura del profilo locale,
sincronizzato automaticamente al primo accesso dalla dependency
get_current_user (vedi app.config.security).
"""

from fastapi import APIRouter, Depends

from app.config.security import get_current_user
from app.dto.authentication_dto import UserOut
from app.entity.user_entity import User

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_profilo(current_user: User = Depends(get_current_user)) -> User:
    """Profilo dell'utente autenticato (creato/sincronizzato al login tramite Azure Entra)."""
    return current_user
