"""Wine -- Tabella per descrivere un vino

Campi della traccia:
  nome, produttore, annata, azienda_vinicola, denominazione,
  regione, descrizione, prezzo, disponibile, immagine_etichetta.
 
Campi aggiunti per la catalogazione frontend:
  tipo (rosso/bianco/rosato/bollicine), vitigno,
  caratteristiche organolettiche (colore, profumo, gusto) — come JSON.

"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    JSON,
    Enum as SAEnum,
    func,
)
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, mapped_column
import enum
 
from app.db.session import Base


class TipoVino (str, enum.Enum):
  """
  Enum delle categorie di vini disponibili: ROSSO, BIANCO, ROSATO, BOLLICINE.
  Usata poi nel menù a sx del frontend
  """
  ROSSO = "rosso"
  BIANCO = "bianco"
  ROSATO = "rosato"
  BOLLICINE = "bollicine"
  

class Wine(Base):
  __tablename__ = "vini"
  
  # Chiave primaria (viene generato un ID interno, ignorando quello del dataset)
  id: Mapped[str] = mapped_column(
        CHAR(36), primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="UUID generato internamente — l'id del dataset viene ignorato",
    )
  
  #Campi della traccia
  nome: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Nome commerciale del vino",
    )
  produttore: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Nome del produttore / cantina",
    )
  annata: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Anno di produzione. Null per vini senza annata (NV)",
    )
  azienda_vinicola: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nome dell'azienda vinicola",
    )
  denominazione: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="DOC, DOCG, IGT, IGP, ecc.",
    )
  regione: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Regione italiana di provenienza",
    )
  descrizione: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Descrizione estesa del vino",
    )
  prezzo: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=False,
        comment="Prezzo al dettaglio in euro",
    )
  disponibile: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="True se il vino è attualmente disponibile in enoteca",
    )
  immagine_etichetta: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="URL dell'immagine su Azure Blob Storage",
    )

    # --- Campi per classificazione e AI ---
  tipo: Mapped[TipoVino] = mapped_column(
        SAEnum(
            TipoVino,
            name="tipo_vino",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        index=True,
        comment="Tipo di vino: rosso, bianco, rosato, bollicine",
    )
  vitigno: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Vitigno o blend (es. Nebbiolo, Sangiovese, Greco di Tufo)",
    )
  caratteristiche_organolettiche: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment=(
            "Oggetto JSON con proprietà sensoriali. "
            "Esempio: {colore: 'rosso rubino', profumo: ['ciliegia', 'vaniglia'], gusto: 'secco, tannico'}"
        ),
    )
  
  #Campi aggiuntivi inferiti da LLM e inseriti nel dataset
  popolarita: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="Punteggio popolarità 1-5 dal dataset",
    )
  scorte: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True,
        comment="Unità disponibili in magazzino. Se 0 → disponibile viene impostato a False",
    )

  # Dati per logging del sistema 
  dati_creazione: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        comment="Data di inserimento nel catalogo",
    )
  dati_aggiornamento: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Data ultima modifica",
    )

  def __repr__(self) -> str:
      return f" <Wine id={self.id} nome='{self.nome}' annata={self.annata} tipo={self.tipo.value}>"
