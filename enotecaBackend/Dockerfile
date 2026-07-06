FROM python:3.12-slim

WORKDIR /app

# Installa dipendenze di sistema necessarie per compilare le estensioni native di spaCy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installa torch in versione CPU-only: keybert (via sentence-transformers) lo richiede,
# ma di default pip scaricherebbe la build con CUDA (diversi GB) inutile per il deploy senza GPU
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copia e installa le dipendenze Python prima del codice
# (sfrutta la cache Docker: il layer viene ricostruito solo se requirements.txt cambia)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Modello italiano usato da spaCy per la Named Entity Recognition sul testo OCR (text_processing_service)
RUN python -m spacy download it_core_news_sm

# Prefetch del modello sentence-transformers usato da KeyBERT: viene scaricato una volta
# in fase di build e "cotto" nell'immagine, così a runtime non serve alcuna chiamata di rete
# verso HuggingFace (niente cold-start lento, niente rischio rate-limit/timeout in produzione)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# Copia il codice sorgente
COPY ./app ./app
COPY alembic.ini .
COPY ./alembic ./alembic

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]