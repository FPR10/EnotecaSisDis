FROM python:3.12-slim

WORKDIR /app

# Installa dipendenze di sistema necessarie per asyncpg e bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e installa le dipendenze Python prima del codice
# (sfrutta la cache Docker: il layer viene ricostruito solo se requirements.txt cambia)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice sorgente
COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
