"""Text processing service — secondo stadio della pipeline di riconoscimento etichette.

In questa classe viene effettuata l'analisi del testo OCR e matching con il catalogo vini.

Flusso: ocr_service.py -> text_processing_service.py -> wine_repository.py

Tecniche impiegate:
    - spaCy    : riconoscimento delle entità nominate nel testo (produttore,denominazione, luoghi) presente sull'etichetta
    - KeyBERT  : individuazione delle parole/frasi chiave più rilevanti, a complemento delle entità riconosciute da spaCy
    - RapidFuzz: confronto fuzzy fra le informazioni estratte e il catalogo vini, per identificare automaticamente il prodotto
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import cast

import spacy
from keybert import KeyBERT
from rapidfuzz import fuzz, process

from app.config.logging import get_logger
from app.entity.wine_entity import Wine
from app.repository.wine_repository import WineRepository

logger = get_logger(__name__)

# Modello italiano (le etichette dei vini del catalogo sono in italiano)
_SPACY_MODEL = "it_core_news_sm"

# Modello multilingua: copre eventuali termini in inglese/francese presenti sulle etichette
_KEYBERT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Entità spaCy rilevanti per un'etichetta di vino (PER -> PERSONA, ORG -> ORGANIZZAZIONE, LOC -> LUOGO, MISC -> other)
_RELEVANT_ENTITY_LABELS = {"PER", "ORG", "LOC", "MISC"}

# Sotto questa soglia (score RapidFuzz 0-100) la corrispondenza è considerata irrilevante
_MATCH_SCORE_THRESHOLD = 60.0

# I modelli NLP sono pesanti da caricare: una sola istanza per processo
@lru_cache 
def _load_spacy_model() -> "spacy.language.Language":
    return spacy.load(_SPACY_MODEL)


@lru_cache
def _load_keybert_model() -> KeyBERT:
    return KeyBERT(model=_KEYBERT_MODEL)


@dataclass
class WineMatch:
    wine: Wine
    score: float  # score RapidFuzz della miglior corrispondenza, 0-100


class TextProcessingService:
    """
    Analizza il testo grezzo estratto dall'OCR ed individua il vino corrispondente nel catalogo, 
    combinando NLP (spaCy + KeyBERT) e fuzzy matching (RapidFuzz).
    """

    def __init__(self, wine_repository: WineRepository):
        self.wine_repository = wine_repository
        self._nlp = _load_spacy_model()
        self._keybert = _load_keybert_model()

    def extract_entities(self, text: str) -> list[str]:
        """spaCy: individua le entità nominate nel testo (produttore, azienda, luoghi)."""
        doc = self._nlp(text)
        return [ent.text for ent in doc.ents if ent.label_ in _RELEVANT_ENTITY_LABELS]

    def extract_keywords(self, text: str, top_n: int = 10) -> list[str]:
        """KeyBERT: individua le parole/frasi chiave più rilevanti nel testo OCR."""
        if not text.strip():
            return []
        # docs è una singola stringa, quindi il risultato è List[Tuple[str, float]]
        # (l'altro ramo dell'overload si applica solo quando si passa una lista di documenti)
        pairs = cast(
            "list[tuple[str, float]]",
            self._keybert.extract_keywords(text, keyphrase_ngram_range=(1, 3), top_n=top_n),
        )
        return [keyword for keyword, _score in pairs]

    def _extract_search_terms(self, text: str) -> list[str]:
        """Combina entità (spaCy) e parole chiave (KeyBERT) nei termini di ricerca, senza duplicati."""
        terms = self.extract_entities(text) + self.extract_keywords(text)
        seen: set[str] = set()
        unique_terms = []
        for term in terms:
            key = term.lower()
            if key not in seen:
                seen.add(key)
                unique_terms.append(term)
        return unique_terms

    @staticmethod
    def _wine_search_blob(wine: Wine) -> str:
        """Concatena i campi del vino rilevanti per il confronto testuale con l'etichetta."""
        fields = [
            wine.nome,
            wine.produttore,
            wine.azienda_vinicola,
            wine.vitigno,
            wine.denominazione,
            wine.regione,
        ]
        return " ".join(field for field in fields if field)

    async def match_wines(self, ocr_text: str, limit: int = 5) -> list[WineMatch]:
        """
        Individua i vini del catalogo che corrispondono al testo OCR dell'etichetta.

        1. spaCy + KeyBERT individuano i termini salienti del testo (produttore,
           denominazione, vitigno, ...).
        2. RapidFuzz confronta ciascun termine con i campi testuali di ogni vino
           del catalogo, tenendo per ognuno il punteggio migliore ottenuto.
        3. I vini sono restituiti in ordine di punteggio decrescente, scartando
           quelli sotto la soglia minima di somiglianza.
        """
        if not ocr_text.strip():
            return []

        candidates = await self.wine_repository.find_all_for_matching()
        if not candidates:
            return []

        search_terms = self._extract_search_terms(ocr_text)
        # se spaCy/KeyBERT non individuano nulla di saliente, confronta col testo OCR intero
        queries = search_terms or [ocr_text]

        blobs = {wine.id: self._wine_search_blob(wine) for wine in candidates}
        best_scores: dict[str, float] = {}
        for query in queries:
            for _blob, score, wine_id in process.extract(
                query, blobs, scorer=fuzz.token_set_ratio, limit=len(blobs)
            ):
                if score > best_scores.get(wine_id, 0.0):
                    best_scores[wine_id] = score

        wines_by_id = {wine.id: wine for wine in candidates}
        matches = [
            WineMatch(wine=wines_by_id[wine_id], score=score)
            for wine_id, score in best_scores.items()
            if score >= _MATCH_SCORE_THRESHOLD
        ]
        matches.sort(key=lambda match: match.score, reverse=True)

        logger.debug(
            f"Text processing: {len(matches)} corrispondenze sopra soglia "
            f"su {len(candidates)} vini in catalogo"
        )
        return matches[:limit]
