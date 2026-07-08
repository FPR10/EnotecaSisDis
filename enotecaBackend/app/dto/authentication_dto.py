"""DTO per User e autenticazione - segue gli schemi Pydantic

Tutta la validazione (es. email) viene gestita automaticamente da Pydantic
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.entity.user_entity import UserRole

class UserOut (BaseModel):
    id: str
    azure_oid: str
    email: EmailStr
    nome: Optional[str]
    ruolo: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    model_config = {"from_attributes": True}
