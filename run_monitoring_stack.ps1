# run_monitoring_stack.ps1
# Script PowerShell para automatizar o build e run da stack de monitoramento com Docker Compose

# --- Configurações ---
$ComposeFile = "docker-compose.yml" # Nome do arquivo Docker Compose

# --- Funções Auxiliares ---
Function Write-Info {
    param ([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

Function Write-ErrorMsg {
    param ([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    # Pausa para o utilizador ver o erro antes de sair, útil se o script fechar rapidamente.
    Read-Host "Pressione Enter para sair..."
    exit 1
}

# --- Lógica Principal ---

# Define o diretório atual como o local do script.
# Isto é útil se o script for chamado de outro local.
$PSScriptRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
Set-Location -Path $PSScriptRoot
Write-Info "Diretório atual: $(Get-Location)"

# Verificar se o docker-compose está instalado
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-ErrorMsg "docker-compose não encontrado. Por favor, instale-o."
}

# Parar e remover serviços existentes definidos no docker-compose.yml (se estiverem a correr)
Write-Info "A parar e a remover quaisquer serviços existentes do compose (incluindo volumes)..."
docker-compose -f $ComposeFile down --volumes
if ($LASTEXITCODE -ne 0) {
    Write-Host "[AVISO] Não foi possível executar 'docker-compose down --volumes' completamente. Pode já estar parado ou ocorreram outros problemas." -ForegroundColor Yellow
}

# Construir as imagens (especialmente a da API, se houver alterações)
Write-Info "A construir imagens definidas no compose (se necessário)..."
docker-compose -f $ComposeFile build
if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Falha ao construir imagens com docker-compose."
}
Write-Info "Build do compose concluído."

# Iniciar todos os serviços em modo detached (-d)
Write-Info "A iniciar todos os serviços com docker-compose..."
docker-compose -f $ComposeFile up -d
if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Falha ao iniciar serviços com docker-compose."
}

Write-Info "Stack de monitoramento iniciada."
Write-Info "API LSTM acessível em: http://localhost:8000"
Write-Info "Métricas da API (para Prometheus) em: http://localhost:8000/metrics"
Write-Info "Prometheus acessível em: http://localhost:9090"
Write-Info "Grafana acessível em: http://localhost:3000 (Login: admin/grafana)"
Write-Info "Para ver os logs: docker-compose -f $ComposeFile logs -f"
Write-Info "Para parar os serviços: docker-compose -f $ComposeFile down"

# Pausa opcional para manter a janela aberta no final, se executado com duplo clique.
# Read-Host "Pressione Enter para fechar esta janela..."

exit 0
