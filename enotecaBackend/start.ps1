# Avvia il backend EnotecaSisDis: .env, container Docker, migration Alembic e seed admin opzionale.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host "Creo .env da .env.example..."
    Copy-Item ".env.example" ".env"
    Write-Host "Ricorda di compilare .env con i valori reali prima di proseguire." -ForegroundColor Yellow
}

Write-Host "Avvio i container (API + MySQL)..."
docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Errore: avvio dei container fallito. Docker Desktop e' in esecuzione?" -ForegroundColor Red
    exit 1
}

Write-Host "Eseguo le migration Alembic..."
docker compose exec api alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "Errore: migration Alembic fallita." -ForegroundColor Red
    exit 1
}

#$seed = Read-Host "Vuoi creare l'utente admin di test? (s/n)"
#if ($seed -eq "s") {
#    docker compose exec api python seed_admin.py
#}

Write-Host "Backend pronto su http://localhost:8000 (docs su http://localhost:8000/docs)" -ForegroundColor Green
