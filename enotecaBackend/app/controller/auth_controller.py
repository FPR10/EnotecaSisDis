"""Controller per la gestione del profilo dell'utente autenticato.

L'autenticazione (login e registrazione) è gestita da Azure Entra ID tramite MSAL sul frontend. 
Questo controller espone soltanto il profilo locale,sincronizzato automaticamente al primo accesso dalla dependency
 `get_current_user` ( `app.config.security`).
"""

from fastapi import APIRouter, Depends

from app.config.security import get_current_user
from app.dto.authentication_dto import UserOut
from app.entity.user_entity import User

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user),) -> User:
    """
    Restituisce il profilo dell'utente autenticato.

    L'utente viene creato o sincronizzato automaticamente al primo accesso
    tramite Azure Entra External ID.
    """
    return current_user