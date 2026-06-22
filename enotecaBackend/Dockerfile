FROM python:3.12-slim

WORKDIR /app

# Installa dipendenze di sistema necessarie per compilare le estensioni native di spaCy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e installa le dipendenze Python prima del codice
# (sfrutta la cache Docker: il layer viene ricostruito solo se requirements.txt cambia)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Modello italiano usato da spaCy per la Named Entity Recognition sul testo OCR (text_processing_service)
RUN python -m spacy download it_core_news_sm

# Copia il codice sorgente
COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
