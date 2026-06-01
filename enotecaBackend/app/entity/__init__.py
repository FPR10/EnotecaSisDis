"""
Import di tutte le entity del progetto.

Questo __init__.py è fondamentale per due motivi:
1. Alembic: env.py fa `import app.entity` e da qui trova tutti i modelli
   registrati nel Base.metadata, necessario per generare le migrazioni.
2. Evita import circolari: tutti gli altri moduli importano da qui,
   non direttamente dai singoli file entity.
"""
from app.entity.wine_entity import Wine, TipoVino
from app.entity.user_entity import User, UserRole

__all__ = [
    "Wine",
    "TipoVino",
    "User",
    "UserRole",
]
