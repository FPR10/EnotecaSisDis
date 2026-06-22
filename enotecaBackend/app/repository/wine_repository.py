"""Wine repository - contiene le query sul DB relative ai vini.
Richiamato dal service.
"""
from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy import distinct, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.wine_entity import Wine, TipoVino
from app.dto.wine_dto import WineCreate, WineUpdate, WineFilter


class WineRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        
    '''
    OPERAZIONI DI LETTURA
    '''
    
    #Ricerca vino tramite id
    # con Optional gestisco il caso in cui è NONE perchè il vino non c'è
    async def find_by_id (self, wine_id: str) -> Optional[Wine]:
        return await self.session.get(Wine, wine_id)
    
    
    #Ricerca vini in base ai filtri
    async def find_all(self, filters: WineFilter, skip: int = 0, limit: int = 20) -> list[Wine]:
        """
        Restituisce vini con filtri applicati.
        I filtri sono da intendersi in AND tra loro.
        """
        query = select(Wine)

        if filters.tipo:
            query = query.where(Wine.tipo == filters.tipo)
        if filters.regione:
            query = query.where(Wine.regione == filters.regione)
        if filters.denominazione:
            query = query.where(Wine.denominazione == filters.denominazione)
        if filters.disponibile is not None:
            query = query.where(Wine.disponibile == filters.disponibile)
        if filters.annata_min:
            query = query.where(Wine.annata >= filters.annata_min)
        if filters.annata_max:
            query = query.where(Wine.annata <= filters.annata_max)
        if filters.prezzo_max:
            query = query.where(Wine.prezzo <= filters.prezzo_max)
        if filters.popolarita_min:
            query = query.where(Wine.popolarita >= filters.popolarita_min)
        if filters.q:
            # Ricerca testuale su nome, produttore e vitigno
            pattern = f"%{filters.q}%"
            query = query.where(
                or_(
                    Wine.nome.ilike(pattern),
                    Wine.produttore.ilike(pattern),
                    Wine.vitigno.ilike(pattern),
                    Wine.azienda_vinicola.ilike(pattern),
                )
            )

        query = query.offset(skip).limit(limit).order_by(Wine.nome)
        ret = await self.session.execute(query)
        return list(ret.scalars().all()) #estraggo la prima colonna e trasformo in lista 
    
    
    async def find_all_for_matching(self) -> list[Wine]:
        """
        Restituisce l'intero catalogo, senza paginazione.
        Usato dal text_processing_service come insieme di candidati su cui
        eseguire il confronto fuzzy (RapidFuzz) col testo OCR delle etichette.
        """
        query = select(Wine)
        result = await self.session.execute(query)
        return list(result.scalars().all())


    '''
    OPERAZIONI DI LETTURA PER FRONTEND
    '''
    async def get_regioni_by_tipo(self, tipo: TipoVino) -> list[str]:
        """Restituisce le regioni distinte per un dato tipo"""
        
        query = (
            select(distinct(Wine.regione)).where(Wine.tipo == tipo).order_by(Wine.regione)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    
    async def count(self, filters: WineFilter):
        query = select(func.count()).select_from(Wine)
        if filters.tipo:
            query = query.where(Wine.tipo == filters.tipo)
        if filters.regione:
            query = query.where(Wine.regione == filters.regione)
        if filters.disponibile is not None:
            query = query.where(Wine.disponibile == filters.disponibile)
        result = await self.session.execute(query)
        return result.scalar_one()
    
    
    '''
    OPERAZIONI DI WRITE (solo per utente ADMIN)
    
    Gestiamo le operazionid salvataggio, modifica ed eliminazione
    '''
    async def save(self, wine: Wine) -> Wine:
        self.session.add(wine)
        await self.session.flush()   #sincronizzo le modifiche in memoria con il database, senza fare commit.
        await self.session.refresh(wine)
        return wine

    async def update(self, wine: Wine, data: WineUpdate) -> Wine:
        """Aggiorna solo i campi forniti nel DTO """
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            # caratteristiche_organolettiche è un oggetto Pydantic: serializzalo in dict
            if field == "caratteristiche_organolettiche" and value is not None:
                value = value.model_dump(exclude_none=True)
            setattr(wine, field, value)
        await self.session.flush()
        await self.session.refresh(wine)
        return wine

    async def delete(self, wine: Wine) -> None:
        await self.session.delete(wine)
        await self.session.flush()
    