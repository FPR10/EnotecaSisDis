"""Text processing service — secondo stadio della pipeline di riconoscimento etichette.

In questa classe viene effettuata l'analisi del testo OCR e matching con il catalogo vini.

Flusso: ocr_service.py -> text_processing_service.py -> wine_repository.py

Viene eseguita:
- Pulizia ed eliminazione del testo inutile PRIMA di ogni analisi

Si usano:
- spaCy: riconoscimento delle entità nominate nel testo (produttore,denominazione, luoghi) presente sull'etichetta
- KeyBERT  : individuazione delle parole/frasi chiave più rilevanti, a complemento delle entità riconosciute da spaCy
- RapidFuzz: confronto fuzzy fra le informazioni estratte e il catalogo vini, per identificare automaticamente il prodotto
"""

import re
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

# Frasi sulle etichette di vino italiane: generano confusione nel fuzzy matching
_BOILERPLATE_PATTERNS = [
    r"denominazione\s+di\s+origine\s+controllata(\s+e\s+garantita)?",
    r"indicazione\s+geografica\s+tipica",
    r"\bd\.?\s*o\.?\s*c\.?\s*g\.?\b",
    r"\bd\.?\s*o\.?\s*c\.?\b",
    r"\bi\.?\s*g\.?\s*t\.?\b",
    r"imbottigliato\s+(all'?origine\s+)?(da|presso)",
    r"estate\s+bottled\s+by",
    r"produced?\s+and\s+bottled\s+by",
    r"contiene\s+solfiti",
    r"contains?\s+sulf?ites?",
    r"product\s+of\s+italy",
    r"prodotto\s+in\s+italia",
    r"\bappellation\b.*?\bcontr[oô]l[ée]e\b",
    r"\b\d{2,4}\s*m[lL]\b",
    r"\b\d{1,2}([.,]\d)?\s*%\s*vol\.?\b",
    r"\bgradazione\s+alcolica\b",
]
_BOILERPLATE_RE = re.compile("|".join(_BOILERPLATE_PATTERNS), re.IGNORECASE)

# Lunghezza minima di un valore di catalogo perché sia utile come termine di ricerca
# (evita di usare come termine di ricerca stringhe troppo corte e poco distintive)
_CATALOGO_LUNGHEZZA_MIN_TERMINE = 3

# Soglia (score RapidFuzz 0-100) sopra la quale un termine di catalogo è considerato
# presente nel testo OCR ripulito
_CATALOGO_SOGLIA_MATCH = 85.0

@lru_cache 
def _carica_modello_spacy() -> "spacy.language.Language":
    return spacy.load(_SPACY_MODEL)


@lru_cache
def _carica_modello_keybert() -> KeyBERT:
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
        self._nlp = _carica_modello_spacy()
        self._keybert = _carica_modello_keybert()

    @staticmethod
    def pulisci_testo_ocr(text: str) -> str:
        """
        Rimuove dal testo OCR le frasi legali/boilerplate note (denominazioni, diciture
        di imbottigliamento, allergeni, gradazione, ...) prima di passarlo a NLP e matching,
        così da evitare che vengano scambiate per entità o inquinino il fuzzy matching.
        """
        cleaned_lines = []
        for line in text.splitlines():
            cleaned = _BOILERPLATE_RE.sub(" ", line)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if cleaned:
                cleaned_lines.append(cleaned)
        return "\n".join(cleaned_lines)

    def estrai_entita(self, text: str) -> list[str]:
        """spaCy: individua le entità nominate nel testo (produttore, azienda, luoghi)."""
        doc = self._nlp(text)
        return [ent.text for ent in doc.ents if ent.label_ in _RELEVANT_ENTITY_LABELS]

    def estrai_parole_chiave(self, text: str, top_n: int = 10) -> list[str]:
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

    @staticmethod
    def _termini_noti_catalogo(candidates: list[Wine]) -> set[str]:
        """Valori distinti del catalogo (produttore, denominazione, vitigno, ...) usabili come vocabolario di ricerca."""
        terms: set[str] = set()
        for wine in candidates:
            for field in (
                wine.nome,
                wine.produttore,
                wine.azienda_vinicola,
                wine.vitigno,
                wine.denominazione,
                wine.regione,
            ):
                if field and len(field.strip()) >= _CATALOGO_LUNGHEZZA_MIN_TERMINE:
                    terms.add(field.strip())
        return terms

    def _cerca_termini_catalogo_nel_testo(self, cleaned_text: str, candidates: list[Wine]) -> list[str]:
        """
        Cerca direttamente nel testo OCR ripulito le stringhe del catalogo (fuzzy substring
        matching), invece di lasciare che un NER "open domain" indovini cosa è rilevante:
        il catalogo è chiuso e finito, quindi sappiamo già quali produttori/denominazioni/
        vitigni sono possibili.
        """
        if not cleaned_text.strip():
            return []
        text_lower = cleaned_text.lower()
        return [
            term
            for term in self._termini_noti_catalogo(candidates)
            if fuzz.partial_ratio(term.lower(), text_lower) >= _CATALOGO_SOGLIA_MATCH
        ]

    def _estrai_termini_ricerca(self, cleaned_text: str, candidates: list[Wine]) -> list[str]:
        """
        Combina i termini di catalogo trovati nel testo (gazetteer), le entità (spaCy)
        e le parole chiave (KeyBERT) nei termini di ricerca, senza duplicati.
        """
        terms = (
            self._cerca_termini_catalogo_nel_testo(cleaned_text, candidates)
            + self.estrai_entita(cleaned_text)
            + self.estrai_parole_chiave(cleaned_text)
        )
        seen: set[str] = set()
        unique_terms = []
        for term in terms:
            key = term.lower()
            if key not in seen:
                seen.add(key)
                unique_terms.append(term)
        return unique_terms

    @staticmethod
    def _blob_ricerca_vino(wine: Wine) -> str:
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

    async def abbina_vini(self, ocr_text: str, limit: int = 5) -> list[WineMatch]:
        """
        Individua i vini del catalogo che corrispondono al testo OCR dell'etichetta.

        1. Il testo OCR viene ripulito dal boilerplate legale (denominazioni, diciture
           di imbottigliamento, allergeni, ...) che altrimenti verrebbe scambiato per
           un'entità o inquinerebbe il fuzzy matching.
        2. Il catalogo viene usato come gazetteer (fuzzy substring matching) per
           individuare direttamente i termini di catalogo presenti nel testo, a
           complemento di spaCy + KeyBERT che individuano i restanti termini salienti.
        3. RapidFuzz confronta ciascun termine con i campi testuali di ogni vino
           del catalogo, tenendo per ognuno il punteggio migliore ottenuto.
        4. I vini sono restituiti in ordine di punteggio decrescente, scartando
           quelli sotto la soglia minima di somiglianza.
        """
        if not ocr_text.strip():
            return []

        candidates = await self.wine_repository.find_all_for_matching()
        if not candidates:
            return []

        cleaned_text = self.pulisci_testo_ocr(ocr_text)
        search_terms = self._estrai_termini_ricerca(cleaned_text, candidates)
        # se gazetteer/spaCy/KeyBERT non individuano nulla di saliente, confronta col testo ripulito intero
        queries = search_terms or [cleaned_text]

        blobs = {wine.id: self._blob_ricerca_vino(wine) for wine in candidates}
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