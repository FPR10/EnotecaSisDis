"""
DTO Wine — schemi Pydantic per validazione input/output.

WineCreate  → body POST /wines (admin)
WineUpdate  → body PUT /wines/{id} (admin, tutti i campi opzionali)
WineOut     → risposta JSON al client
WineFilter  → query params per ricerca/filtro
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.entity.wine_entity import TipoVino


class CaratteristicheOrganolettiche(BaseModel):
    colore:  Optional[str]       = None
    profumo: Optional[list[str]] = None
    gusto:   Optional[str]       = None


"""CREATE"""
class WineCreate(BaseModel):
    # Campi obbligatori
    nome:             str      = Field(..., min_length=1, max_length=255)
    produttore:       str      = Field(..., min_length=1, max_length=255)
    azienda_vinicola: str      = Field(..., min_length=1, max_length=255)
    regione:          str      = Field(..., min_length=1, max_length=100)
    tipo:             TipoVino = Field(...)

    # Campi opzionali
    # L'id del dataset viene ignorato — il backend genera UUID
    id:              Optional[str]   = Field(None, exclude=True)
    annata:          Optional[int]   = Field(None, ge=1800, le=2100)
    denominazione:   Optional[str]   = Field(None, max_length=100)
    descrizione:     Optional[str]   = None
    prezzo:          Optional[float] = Field(None, ge=0)
    disponibile:     bool            = Field(True)
    immagine_etichetta: Optional[str] = Field(None, max_length=512)
    vitigno:         Optional[str]   = Field(None, max_length=255)
    caratteristiche_organolettiche: Optional[CaratteristicheOrganolettiche] = None

    # Campi aggiuntivi del dataset
    popolarita: Optional[int] = Field(None, ge=1, le=5,
                                      description="Punteggio popolarità 1-5")
    scorte: Optional[int] = Field(None, ge=0,
                                      description="Unità disponibili in magazzino")

    
    @model_validator(mode="after")
    def sync_disponibile_da_scorte(self) -> "WineCreate":
        """Se scorte è 0 imposta disponibile=False automaticamente."""
        if self.scorte is not None and self.scorte == 0:
            self.disponibile = False
        return self


"""UPDATE"""
class WineUpdate(BaseModel):
    """ L'update è da interdersi parziale. I campi sono tutti opzionali
    """
    nome:             Optional[str]   = Field(None, min_length=1, max_length=255)
    produttore:       Optional[str]   = Field(None, min_length=1, max_length=255)
    azienda_vinicola: Optional[str]   = Field(None, min_length=1, max_length=255)
    regione:          Optional[str]   = Field(None, min_length=1, max_length=100)
    tipo:             Optional[TipoVino] = None

    annata:           Optional[int]   = Field(None, ge=1800, le=2100)
    denominazione:    Optional[str]   = Field(None, max_length=100)
    descrizione:      Optional[str]   = None
    prezzo:           Optional[float] = Field(None, ge=0)
    disponibile:      Optional[bool]  = None
    immagine_etichetta: Optional[str] = Field(None, max_length=512)
    vitigno:          Optional[str]   = Field(None, max_length=255)
    caratteristiche_organolettiche: Optional[CaratteristicheOrganolettiche] = None
    popolarita:       Optional[int]   = Field(None, ge=1, le=5)
    scorte:           Optional[int]   = Field(None, ge=0)

    @model_validator(mode="after")
    def sync_disponibile_da_scorte(self) -> "WineUpdate":
        if self.scorte is not None and self.scorte == 0:
            self.disponibile = False
        return self


"""OUT"""
class WineOut(BaseModel):
    # Campi obbligatori 
    id: str
    nome: str
    produttore: str
    azienda_vinicola: str
    regione: str
    tipo: TipoVino
    disponibile: bool
    created_at: datetime
    updated_at: datetime

    #  Campi opzionali 
    annata: Optional[int]
    denominazione: Optional[str]
    descrizione: Optional[str]
    prezzo:   Optional[float]
    immagine_etichetta: Optional[str]
    vitigno: Optional[str]
    caratteristiche_organolettiche: Optional[CaratteristicheOrganolettiche]
    popolarita:Optional[int]
    scorte:  Optional[int]

    model_config = {"from_attributes": True}

"""FILTRAGGIO"""
class WineFilter(BaseModel):
    tipo: Optional[TipoVino] = None
    regione: Optional[str]      = None
    denominazione: Optional[str]      = None
    disponibile: Optional[bool]     = None
    annata_min: Optional[int]      = None
    annata_max: Optional[int]      = None
    prezzo_max: Optional[float]    = None
    popolarita_min: Optional[int]     = Field(None, ge=1, le=5)
    q: Optional[str]      = None  
