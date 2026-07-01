"""
Pairing service — abbinamento cibo-vino.

Basandosi su un piatto descritto dall'utente, viene interrogato un LLM (Groq, modello LLama) per
individuare, tra i vini nel catalogo, quelli più adatti ad accompagnarlo.
Ci si basa sulle caratteristiche organolettiche del vino (colore, profumo, gusto, vitigno, tipo, denominazione).
"""

import json

from groq import AsyncGroq
from groq import APIError as GroqAPIError

from app.config.logging import get_logger
from app.config.settings import get_settings
from app.entity.wine_entity import Wine
from app.repository.wine_repository import WineRepository

logger = get_logger(__name__)

# Limite di vini del catalogo inclusi nel prompt, per non superare il contesto del modello
_MAX_VINI_CAND = 80

_GENERAL_PROMT = (
    "Sei un sommelier esperto. L'utente descrive un piatto: il tuo compito è scegliere, "
    "esclusivamente tra i vini elencati nel catalogo fornito, quelli che si abbinano meglio "
    "sulla base delle loro caratteristiche organolettiche (colore, profumo, gusto, vitigno, "
    "tipo, denominazione). Non proporre mai vini che non sono nell'elenco fornito. "
    "Ricorda che i vini 'bollicine' sono spesso l'abbinamento migliore per fritti, "
    "antipasti, aperitivi, crudi di pesce e dolci: considerali attivamente quando il piatto rientra in queste categorie."
    "Rispondi SOLO con un oggetto JSON nella forma "
    '{"suggerimenti": [{"wine_id": "<id dal catalogo>", "motivazione": "<breve spiegazione in italiano>"}]}, '
    "senza altro testo."
)


class PairingServiceError(Exception):
    """Errore durante la generazione dell'abbinamento cibo-vino."""


class PairingService:
    """
    Wrapper su Groq (modelli Llama): dato un piatto, individua nel catalogo i vini
    più adatti ad accompagnarlo, sulla base delle caratteristiche organolettiche.
    """

    def __init__(self, wine_repository: WineRepository) -> None:
        settings = get_settings()

        # Groq non settato
        if not settings.groq_api_key:
            raise PairingServiceError(
                "Groq non configurato: impostare GROQ_API_KEY"
            )

        self.wine_repository = wine_repository
        self._model = settings.groq_model
        self._client = AsyncGroq(api_key=settings.groq_api_key)

    @staticmethod
    def _descrivi_vino(wine: Wine) -> str:
        """Riga sintetica del vino (per il catalogo nel prompt): id e caratteristiche organolettiche."""
        caratteristiche = wine.caratteristiche_organolettiche or {}
        dettagli_vino = [f"tipo {wine.tipo.value}"]
        if wine.vitigno:
            dettagli_vino.append(f"vitigno {wine.vitigno}")
        if wine.denominazione:
            dettagli_vino.append(wine.denominazione)

        colore = caratteristiche.get("colore")
        if colore:
            dettagli_vino.append(f"colore {colore}")
        profumo = caratteristiche.get("profumo")
        if profumo:
            dettagli_vino.append(f"profumo {', '.join(profumo) if isinstance(profumo, list) else profumo}")
        gusto = caratteristiche.get("gusto")
        if gusto:
            dettagli_vino.append(f"gusto {gusto}")

        return f"- id={wine.id} | {wine.nome} ({', '.join(dettagli_vino)})"

    async def suggerisci_vini(self, cibo: str, limit: int = 3) -> list[tuple[Wine, str]]:
        """
        Dato un piatto (testo libero), restituisce i vini del catalogo più indicati
        per l'abbinamento, ciascuno con la motivazione generata da Groq (Llama).
        """
        cibo = cibo.strip() #rimozione spazi a inizio e fine 
        if not cibo:
            raise PairingServiceError("Descrizione del piatto vuota")

        candidati = await self._trova_vini_disponibili()
        risposta_grezza = await self._chiedi_abbinamento_a_groq(cibo, candidati)
        suggerimenti = self._estrai_suggerimenti(risposta_grezza)

        risultati = self._risolvi_vini_suggeriti(suggerimenti, candidati)
        if not risultati:
            raise PairingServiceError("Nessun vino del catalogo individuato nella risposta di Groq")

        logger.debug(f"Pairing: {len(risultati)} vini suggeriti per il piatto '{cibo}'")
        return risultati[:limit]

    async def _trova_vini_disponibili(self) -> list[Wine]:
        """Carica dal repository i vini disponibili, limitati al massimo numero di candidati."""
        tutti_i_vini = await self.wine_repository.find_all_for_matching()
        candidati = [wine for wine in tutti_i_vini if wine.disponibile]
        if not candidati:
            raise PairingServiceError("Nessun vino disponibile in catalogo")
        return candidati[:_MAX_VINI_CAND]

    async def _chiedi_abbinamento_a_groq(self, cibo: str, candidati: list[Wine]) -> str:
        """Invia il prompt a Groq e restituisce il contenuto testuale della risposta."""
        catalogo = "\n".join(self._descrivi_vino(wine) for wine in candidati)
        prompt_utente = (
            f"Piatto da abbinare: {cibo}\n\n"
            f"Catalogo vini disponibili:\n{catalogo}\n\n"
            f"Suggerisci al massimo {_MAX_VINI_CAND} vini, in ordine di adeguatezza."
        )

        try:
            risposta = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _GENERAL_PROMT},
                    {"role": "user", "content": prompt_utente},
                ],
                temperature=0.4,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
        except GroqAPIError as exception:
            logger.error(f"Groq: suggerimento abbinamento fallito per piatto '{cibo}': {exception}")
            raise PairingServiceError("Generazione dell'abbinamento cibo-vino fallita") from exception

        contenuto = risposta.choices[0].message.content
        if not contenuto:
            raise PairingServiceError("Groq ha restituito una risposta vuota")
        return contenuto

    def _estrai_suggerimenti(self, contenuto: str) -> list[dict]:
        """Effettua il parsing del JSON restituito da Groq ed estrae la lista dei suggerimenti."""
        try:
            return json.loads(contenuto)["suggerimenti"]
        except (json.JSONDecodeError, KeyError, TypeError) as exception:
            logger.error(f"Groq: risposta non interpretabile come JSON: {contenuto!r}")
            raise PairingServiceError("Risposta di Groq non interpretabile") from exception

    def _risolvi_vini_suggeriti(
        self, suggerimenti: list[dict], candidati: list[Wine]
    ) -> list[tuple[Wine, str]]:
        """Associa ogni suggerimento al vino reale del catalogo, scartando eventuali allucinazioni."""
        vini_per_id = {wine.id: wine for wine in candidati}
        risultati: list[tuple[Wine, str]] = []
        for voce in suggerimenti:
            wine_id = voce.get("wine_id")
            if not isinstance(wine_id, str):
                continue  # id mancante o malformato: probabile allucinazione del modello
            wine = vini_per_id.get(wine_id)
            if wine is None:
                continue  # id non presente nel catalogo: probabile allucinazione del modello
            risultati.append((wine, voce.get("motivazione", "")))
        return risultati