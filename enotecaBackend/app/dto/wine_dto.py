"""
DTO Wine — schemi Pydantic per validazione input/output.

WineCreate        → body POST /wines (admin)
WineUpdate        → body PUT /wines/{id} (admin, tutti i campi opzionali)
WineOut           → risposta JSON al client
WineFilter        → query params per ricerca/filtro
WinePageOut       → lista paginata
WineSimilarItem   → vino + score similarità
SemanticSearchItem→ vino + score ricerca semantica
OcrSearchOut      → testo estratto + risultati ricerca OCR
BulkImportResult  → esito import massivo CSV/JSON
AbbinamentoCiboIn → body POST per richiedere l'abbinamento (descrizione del piatto)
AbbinamentoOut    → risposta abbinamenti cibo-vino (AI generativa)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.entity.wine_entity import TipoVino


class CaratteristicheOrganolettiche(BaseModel):
    colore:  Optional[str]       = None
    profumo: Optional[list[str]] = None
    gusto:   Optional[str]       = None


# ── CREATE ─────────────────────────────────────────────────────────────────────

class WineCreate(BaseModel):
    # Campi obbligatori
    nome:             str      = Field(..., min_length=1, max_length=255)
    produttore:       str      = Field(..., min_length=1, max_length=255)
    azienda_vinicola: str      = Field(..., min_length=1, max_length=255)
    regione:          str      = Field(..., min_length=1, max_length=100)
    tipo:             TipoVino = Field(...)

    # Campi opzionali
    id:              Optional[str]   = Field(None, exclude=True)   # ignorato: il backend genera UUID
    annata:          Optional[int]   = Field(None, ge=1800, le=2100)
    denominazione:   Optional[str]   = Field(None, max_length=100)
    descrizione:     Optional[str]   = None
    prezzo:          Optional[float] = Field(None, ge=0)
    disponibile:     bool            = Field(True)
    immagine_etichetta: Optional[str] = Field(None, max_length=512)
    vitigno:         Optional[str]   = Field(None, max_length=255)
    caratteristiche_organolettiche: Optional[CaratteristicheOrganolettiche] = None

    # Campi aggiuntivi dal dataset
    popolarita: Optional[int] = Field(None, ge=1, le=5)
    scorte:     Optional[int] = Field(None, ge=0)

    @model_validator(mode="after")
    def sync_disponibile_da_scorte(self) -> "WineCreate":
        if self.scorte is not None and self.scorte == 0:
            self.disponibile = False
        return self


# ── UPDATE ─────────────────────────────────────────────────────────────────────

class WineUpdate(BaseModel):
    """Aggiornamento parziale: tutti i campi opzionali."""
    nome:             Optional[str]      = Field(None, min_length=1, max_length=255)
    produttore:       Optional[str]      = Field(None, min_length=1, max_length=255)
    azienda_vinicola: Optional[str]      = Field(None, min_length=1, max_length=255)
    regione:          Optional[str]      = Field(None, min_length=1, max_length=100)
    tipo:             Optional[TipoVino] = None
    annata:           Optional[int]      = Field(None, ge=1800, le=2100)
    denominazione:    Optional[str]      = Field(None, max_length=100)
    descrizione:      Optional[str]      = None
    prezzo:           Optional[float]    = Field(None, ge=0)
    disponibile:      Optional[bool]     = None
    immagine_etichetta: Optional[str]    = Field(None, max_length=512)
    vitigno:          Optional[str]      = Field(None, max_length=255)
    caratteristiche_organolettiche: Optional[CaratteristicheOrganolettiche] = None
    popolarita:       Optional[int]      = Field(None, ge=1, le=5)
    scorte:           Optional[int]      = Field(None, ge=0)

    @model_validator(mode="after")
    def sync_disponibile_da_scorte(self) -> "WineUpdate":
        if self.scorte is not None and self.scorte == 0:
            self.disponibile = False
        return self


# ── OUT ────────────────────────────────────────────────────────────────────────

class WineOut(BaseModel):
    # Campi obbligatori
    id:               str
    nome:             str
    produttore:       str
    azienda_vinicola: str
    regione:          str
    tipo:             TipoVino
    disponibile:      bool
    dati_creazione:   datetime
    dati_aggiornamento: datetime

    # Campi opzionali
    annata:           Optional[int]   = None
    denominazione:    Optional[str]   = None
    descrizione:      Optional[str]   = None
    prezzo:           Optional[float] = None
    immagine_etichetta: Optional[str] = None
    vitigno:          Optional[str]   = None
    caratteristiche_organolettiche: Optional[CaratteristicheOrganolettiche] = None
    popolarita:       Optional[int]   = None
    scorte:           Optional[int]   = None

    model_config = {"from_attributes": True}


# ── FILTRI ─────────────────────────────────────────────────────────────────────

class WineFilter(BaseModel):
    tipo:          Optional[TipoVino] = None
    regione:       Optional[str]      = None
    denominazione: Optional[str]      = None
    disponibile:   Optional[bool]     = None
    annata_min:    Optional[int]      = None
    annata_max:    Optional[int]      = None
    prezzo_max:    Optional[float]    = None
    popolarita_min: Optional[int]     = Field(None, ge=1, le=5)
    q:             Optional[str]      = None


# ── PAGINAZIONE ────────────────────────────────────────────────────────────────

class WinePageOut(BaseModel):
    items: list[WineOut]
    total: int
    skip:  int
    limit: int


# ── AI: similarità e ricerca semantica ────────────────────────────────────────

class WineSimilarItem(BaseModel):
    wine:  WineOut
    score: float = Field(ge=0.0, le=1.0, description="Score similarità 0-1")


class SemanticSearchItem(BaseModel):
    wine:  WineOut
    score: float = Field(ge=0.0, le=1.0, description="Score corrispondenza 0-1")


# ── AI: OCR ────────────────────────────────────────────────────────────────────

class OcrSearchOut(BaseModel):
    extracted_text: str                  = Field(description="Testo estratto dall'etichetta")
    results:        list[WineOut]        = Field(description="Vini trovati per corrispondenza testo")


# ── IMPORT MASSIVO ─────────────────────────────────────────────────────────────

class BulkImportResult(BaseModel):
    created: int
    errors:  list[dict]


# ── AI: abbinamenti cibo-vino ──────────────────────────────────────────────────

class AbbinamentoCiboIn(BaseModel):
    cibo: str = Field(..., min_length=1, description="Descrizione del piatto da abbinare")

    @field_validator("cibo")
    @classmethod
    def cibo_non_vuoto(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Descrizione del piatto vuota")
        return value


class VinoSuggerito(BaseModel):
    wine:        WineOut
    motivazione: str = Field(description="Spiegazione dell'abbinamento generata da un LLM (Groq, modello Llama)")


class AbbinamentoOut(BaseModel):
    cibo:          str
    suggerimenti: list[VinoSuggerito] = Field(description="Vini del catalogo più adatti al piatto, in ordine di adeguatezza")
