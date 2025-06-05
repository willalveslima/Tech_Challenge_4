#!/bin/bash

# Script para iniciar a stack de monitoramento (API, Prometheus, Grafana) com Docker Compose

# --- Configurações ---
COMPOSE_FILE="docker-compose.yml"

# --- Funções Auxiliares ---
echo_info() {
    echo "[INFO] $1"
}

echo_error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# --- Lógica Principal ---
# cd "$(dirname "$0")" # Garante que estamos no diretório do script (projeto_raiz)

echo_info "Diretório atual: $(pwd)"

# Verificar se o docker-compose está instalado
if ! command -v docker-compose &> /dev/null
then
    echo_error "docker-compose não encontrado. Por favor, instale-o."
fi

# Parar e remover serviços existentes definidos no docker-compose.yml (se estiverem rodando)
echo_info "Parando e removendo quaisquer serviços existentes do compose..."
docker-compose -f ${COMPOSE_FILE} down --volumes # '--volumes' remove volumes nomeados se não forem mais usados por outros containers

# Construir as imagens (especialmente a da API, se houver mudanças)
echo_info "Construindo imagens definidas no compose (se necessário)..."
docker-compose -f ${COMPOSE_FILE} build

if [ $? -ne 0 ]; then
    echo_error "Falha ao construir imagens com docker-compose."
fi
echo_info "Build do compose concluído."

# Iniciar todos os serviços em modo detached (-d)
echo_info "Iniciando todos os serviços com docker-compose..."
docker-compose -f ${COMPOSE_FILE} up -d

if [ $? -ne 0 ]; then
    echo_error "Falha ao iniciar serviços com docker-compose."
fi

echo_info "Stack de monitoramento iniciada."
echo_info "API LSTM acessível em: http://localhost:8000"
echo_info "Métricas da API (para Prometheus) em: http://localhost:8000/metrics"
echo_info "Prometheus acessível em: http://localhost:9090"
echo_info "Grafana acessível em: http://localhost:3000 (Login: admin/grafana)"
echo_info "Para ver os logs: docker-compose -f ${COMPOSE_FILE} logs -f"
echo_info "Para parar os serviços: docker-compose -f ${COMPOSE_FILE} down"

exit 0
