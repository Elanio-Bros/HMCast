<#
.SYNOPSIS
    Script de Reset Seguro e Inicialização Limpa do Banco de Dados SQLite do HMCast 3.0.
.DESCRIPTION
    Faz backup do arquivo atual em AppData\Local\ersatztv, remove a base antiga com migrations acumuladas
    e recria a base limpa com a arquitetura e dados padrão do HMCast 3.0.
#>

param(
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

$appDataPath = [System.IO.Path]::Combine($env:LOCALAPPDATA, "ersatztv")
$dbPath = [System.IO.Path]::Combine($appDataPath, "ersatztv.sqlite3")
$backupDir = [System.IO.Path]::Combine($appDataPath, "backups")

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " HMCast 3.0 - Script de Reset Limpo do Banco SQLite       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (Test-Path $dbPath) {
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    }
    
    $timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $backupFile = [System.IO.Path]::Combine($backupDir, "ersatztv_backup_$timestamp.sqlite3")
    
    Write-Host "[1/3] Realizando backup de seguranca para:" -ForegroundColor Yellow
    Write-Host "      $backupFile" -ForegroundColor DarkGray
    Copy-Item -Path $dbPath -Destination $backupFile -Force
    
    Write-Host "[2/3] Removendo base SQLite legada com historico acumulado..." -ForegroundColor Yellow
    Remove-Item -Path $dbPath -Force
    
    # Remover arquivos WAL e SHM se existirem
    if (Test-Path "$dbPath-wal") { Remove-Item -Path "$dbPath-wal" -Force }
    if (Test-Path "$dbPath-shm") { Remove-Item -Path "$dbPath-shm" -Force }
    
    Write-Host "[3/3] Base legada expurgada. Ao iniciar o HMCast, a base sera criada limpa e virgem com os 4 perfis factory." -ForegroundColor Green
} else {
    Write-Host "Nenhum banco de dados existente encontrado em $dbPath." -ForegroundColor Yellow
    Write-Host "O HMCast 3.0 inicializara uma base virgem automaticamente." -ForegroundColor Green
}

Write-Host "Operacao concluida com sucesso!" -ForegroundColor Cyan
