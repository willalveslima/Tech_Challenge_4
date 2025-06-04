# Dockerfile

# Use uma imagem base oficial do Python.
FROM python:3.9-slim

# Defina o diretório de trabalho no container.
WORKDIR /app

# Copie o arquivo de dependências primeiro para aproveitar o cache do Docker.
COPY requirements_deploy.txt .

# Instale as dependências.
# --no-cache-dir para reduzir o tamanho da imagem
# --default-timeout=100 para evitar timeouts em conexões lentas
# --retries=3 para tentar novamente em caso de falha na rede
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 --retries=3 -r requirements_deploy.txt

# Copie os arquivos da aplicação para o diretório de trabalho.
COPY . .
# Especificamente, copie o modelo e o scaler (já incluído no COPY . .)
# COPY melhor_modelo_lstm.keras .
# COPY min_max_scaler.gz .
# COPY api_deploy_fastapi.py .


# Exponha a porta que a aplicação usará.
EXPOSE 8000

# Comando para executar a aplicação quando o container iniciar.
# uvicorn api_deploy_fastapi:app --host 0.0.0.0 --port 8000
CMD ["uvicorn", "api_deploy_fastapi:app", "--host", "0.0.0.0", "--port", "8000"]
