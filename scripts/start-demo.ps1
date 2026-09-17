$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$root'; .\.venv\Scripts\python.exe -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$root'; npm.cmd run dev:web -- --host 127.0.0.1 --port 5173"

Write-Host 'Backend: http://127.0.0.1:8000'
Write-Host 'Facility web: http://127.0.0.1:5173'
Write-Host 'Mobile (optional): cd apps/mobile; npx.cmd expo start'
