#!/bin/bash

# Script para automatizar o build e run da API LSTM com Docker

# --- Configurações ---
IMAGE_NAME="lstm_prediction_api"
CONTAINER_NAME="lstm_api_container"
DOCKERFILE_PATH="deploy_lstm/Dockerfile" # Caminho para o Dockerfile a partir do diretório atual (projeto_raiz)
APP_PORT_HOST=8000  # Porta no host que será mapeada para a porta do container
APP_PORT_CONTAINER=8000 # Porta que a aplicação expõe dentro do container (definida no Dockerfile e CMD)

# --- Funções Auxiliares ---
echo_info() {
    echo "[INFO] $1"
}

echo_error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# --- Lógica Principal ---

# 1. Navegar para o diretório raiz do projeto (onde este script está)
#    Este passo é importante se o script for chamado de outro lugar.
#    Se o script SEMPRE for executado da pasta projeto_raiz/, esta linha pode ser opcional.
# cd "$(dirname "$0")"
echo_info "Diretório atual: $(pwd)"

# 2. Parar e remover contêiner existente com o mesmo nome (se houver)
if [ "$(docker ps -q -f name=^/${CONTAINER_NAME}$)" ]; then
    echo_info "Parando o contêiner existente: ${CONTAINER_NAME}..."
    docker stop ${CONTAINER_NAME} || echo_info "Não foi possível parar o contêiner (pode já estar parado)."
fi

if [ "$(docker ps -aq -f name=^/${CONTAINER_NAME}$)" ]; then
    echo_info "Removendo o contêiner existente: ${CONTAINER_NAME}..."
    docker rm ${CONTAINER_NAME} || echo_info "Não foi possível remover o contêiner (pode já ter sido removido)."
fi

# 3. Construir a imagem Docker
#    O '.' no final indica que o contexto do build é o diretório atual (projeto_raiz)
echo_info "Construindo a imagem Docker: ${IMAGE_NAME}..."
echo_info "Usando Dockerfile em: ${DOCKERFILE_PATH}"
echo_info "Contexto do build: $(pwd)"

docker build -t ${IMAGE_NAME} -f ${DOCKERFILE_PATH} .

# Verificar se o build foi bem-sucedido
if [ $? -ne 0 ]; then
    echo_error "Falha ao construir a imagem Docker."
fi
echo_info "Imagem Docker '${IMAGE_NAME}' construída com sucesso."

# 4. Executar o contêiner Docker
echo_info "Executando o contêiner Docker: ${CONTAINER_NAME}..."
docker run -d -p ${APP_PORT_HOST}:${APP_PORT_CONTAINER} --name ${CONTAINER_NAME} ${IMAGE_NAME}

# Verificar se o run foi bem-sucedido
if [ $? -ne 0 ]; then
    echo_error "Falha ao executar o contêiner Docker."
fi

echo_info "Contêiner '${CONTAINER_NAME}' está rodando."
echo_info "API deve estar acessível em http://localhost:${APP_PORT_HOST}"
echo_info "Para ver os logs do contêiner, use: docker logs ${CONTAINER_NAME}"
echo_info "Para parar o contêiner, use: docker stop ${CONTAINER_NAME}"

exit 0
