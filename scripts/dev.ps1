# Launch the full ChessLab development environment.
# Backend (FastAPI) and frontend (Vite) each open in their own window.

$root = Split-Path $PSScriptRoot -Parent

Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$root\backend'; .\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$root\frontend'; npm run dev"

Write-Host "Backend:  http://127.0.0.1:8000/docs"
Write-Host "Frontend: http://127.0.0.1:5173"
