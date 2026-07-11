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


#Database engine - punto di accesso al DB (MySQL)
engine = create_async_engine(
    settings.database_url,

    #Check connessione valida
    pool_pre_ping=True,

    # Se debug=True mostra tutte le query SQL nel terminale.
    echo=settings.debug,

    # Numero massimo di connessioni mantenute aperte.
    pool_size=10,

    # Max numero di connessioni mantenute se il pool è pieno
    max_overflow=20,

    # Ricrea automaticamente le connessioni dopo 1 ora (MySQL chiude l connessioni inattive)
    pool_recycle=3600,
)



#Sessione (per inserimento, modifica, eliminazione ed esecuzione di query)
AsyncSessionLocal = async_sessionmaker(

    # Associa le sessioni all'engine creato 
    bind=engine,

    # Tipo di sessione: asincrona.
    class_=AsyncSession,

    # Dopo commit gli oggetti restano utilizzabili.
    expire_on_commit=False,

    autocommit=False,

    # SQLAlchemy non invia automaticamente
    # modifiche pendenti prima di una query.
    autoflush=False,
)


# Classe Base (tutte le entity del DB eriditano da Base)
class Base(DeclarativeBase):
    pass



async def get_db() -> AsyncGenerator[AsyncSession, None]:

    # Crea una nuova sessione
    async with AsyncSessionLocal() as session:

        try:

            #Collegamento sessione-controller
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