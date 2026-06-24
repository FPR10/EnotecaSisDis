# EnotecaSisDis

## Avvio del progetto

Il progetto è composto da un backend FastAPI (`enotecaBackend`) e un frontend Angular (`enotecaFrontend`).

### Backend (`enotecaBackend`)

In alternativa ai passi manuali, su Windows è possibile eseguire lo script `start.ps1` (dalla cartella `enotecaBackend`), che esegue automaticamente i passi 1-4 sotto riportati:

```powershell
cd enotecaBackend
.\start.ps1
```

1. Crea il file `.env` a partire dall'esempio e compilalo con i valori reali (DB locale, chiavi Azure/Groq, ecc.):

   ```bash
   cd enotecaBackend
   cp .env.example .env
   ```

   Per lo sviluppo locale `DATABASE_URL` può restare quello di default (`mysql+aiomysql://admin:secret@localhost:3306/enoteca`), coerente con le credenziali del servizio `db` in `docker-compose.yml`.

2. Avvia i container (API + MySQL):

   ```bash
   docker compose up -d --build
   ```

3. Crea le tabelle nel database eseguendo le migration Alembic (la prima volta, e ogni volta che vengono aggiunte nuove migration):

   ```bash
   docker compose exec api alembic upgrade head
   ```

4. (Opzionale, solo la prima volta) crea un utente admin di test per poter testare le rotte protette senza Azure Entra configurato:

   ```bash
   docker compose exec api python seed_admin.py
   ```

L'API sarà disponibile su `http://localhost:8000` (documentazione interattiva su `http://localhost:8000/docs`).

### Frontend (`enotecaFrontend`)

1. Installa le dipendenze:

   ```bash
   cd enotecaFrontend
   npm install
   ```

2. Avvia il server di sviluppo:

   ```bash
   ng serve
   ```

L'app sarà disponibile su `http://localhost:4200` e punta di default al backend su `http://localhost:8000/api/v1` (configurabile in `src/environments/environment.ts`). Le funzionalità riservate agli admin (Aggiungi vino, Gestione enoteca) richiedono il login tramite Azure Entra ID configurato nello stesso file.