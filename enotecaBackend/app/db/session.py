from typing import AsyncGenerator

# Componenti asincroni di SQLAlchemy
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)

# Classe base per definire i modelli ORM
from sqlalchemy.orm import DeclarativeBase

# Configurazione dell'applicazione (DATABASE_URL, DEBUG, ecc.)
from app.config.settings import get_settings


# Carica le impostazioni definite nei file di configurazione
settings = get_settings()


# ============================================================
# ENGINE DATABASE
# ============================================================
#
# L'engine rappresenta il punto di accesso al database.
# Gestisce:
#   - connessioni
#   - pool di connessioni
#   - comunicazione con MySQL
#
# In questo caso usiamo:
#   MySQL + driver asincrono aiomysql
#
# Esempio URL:
# mysql+aiomysql://user:password@localhost:3306/enoteca
#
engine = create_async_engine(
    settings.database_url,

    # Controlla che una connessione sia ancora valida
    # prima di riutilizzarla.
    pool_pre_ping=True,

    # Se debug=True mostra tutte le query SQL nel terminale.
    echo=settings.debug,

    # Numero massimo di connessioni mantenute aperte.
    pool_size=10,

    # Connessioni extra temporanee se il pool è pieno.
    max_overflow=20,

    # Ricrea automaticamente le connessioni dopo 1 ora.
    # Utile perché MySQL chiude connessioni inattive.
    pool_recycle=3600,
)


# ============================================================
# SESSION FACTORY
# ============================================================
#
# Una Session rappresenta una "conversazione"
# con il database.
#
# Tramite la Session possiamo:
#   - eseguire query
#   - inserire dati
#   - modificare dati
#   - eliminare dati
#
# async_sessionmaker è una fabbrica che genera
# nuove sessioni quando servono.
#
AsyncSessionLocal = async_sessionmaker(

    # Associa le sessioni all'engine creato sopra.
    bind=engine,

    # Tipo di sessione: asincrona.
    class_=AsyncSession,

    # Dopo commit gli oggetti restano utilizzabili.
    expire_on_commit=False,

    # Il commit verrà eseguito manualmente.
    autocommit=False,

    # SQLAlchemy non invia automaticamente
    # modifiche pendenti prima di una query.
    autoflush=False,
)


# ============================================================
# CLASSE BASE ORM
# ============================================================
#
# Tutte le entità del database erediteranno da Base.
#
# Esempio:
#
# class Wine(Base):
#     __tablename__ = "wines"
#
# class User(Base):
#     __tablename__ = "users"
#
# SQLAlchemy usa questa classe per raccogliere
# i metadati di tutte le tabelle.
#
class Base(DeclarativeBase):
    pass


# ============================================================
# FASTAPI DATABASE DEPENDENCY
# ============================================================
#
# Questa funzione viene utilizzata con:
#
# db: AsyncSession = Depends(get_db)
#
# FastAPI:
#   1. apre una sessione
#   2. la passa al controller
#   3. esegue commit se tutto va bene
#   4. esegue rollback se c'è un errore
#   5. chiude la sessione
#
async def get_db() -> AsyncGenerator[AsyncSession, None]:

    # Crea una nuova sessione.
    async with AsyncSessionLocal() as session:

        try:

            # Consegna la sessione al controller.
            #
            # Esempio:
            #
            # @router.get("/wines")
            # async def get_wines(
            #     db: AsyncSession = Depends(get_db)
            # ):
            #     ...
            #
            yield session

            # Se il controller termina senza errori,
            # salva tutte le modifiche nel database.
            await session.commit()

        except Exception:

            # Se si verifica un errore:
            # annulla tutte le modifiche non ancora salvate.
            await session.rollback()

            # Rilancia l'eccezione affinché FastAPI
            # possa gestirla correttamente.
            raise

        finally:

            # Chiude la sessione e restituisce
            # la connessione al pool.
            await session.close()