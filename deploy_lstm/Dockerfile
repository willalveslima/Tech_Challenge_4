# deploy_lstm/Dockerfile

# Use uma imagem base oficial do Python.
FROM python:3.9-slim

# Defina o diretório de trabalho no container.
WORKDIR /app

# Copie o arquivo de dependências primeiro para aproveitar o cache do Docker.
# O caminho é relativo ao contexto do build (projeto_raiz/)
COPY deploy_lstm/requirements_deploy.txt /app/requirements_deploy.txt

# Instale as dependências.
# --no-cache-dir para reduzir o tamanho da imagem
# --default-timeout=100 para evitar timeouts em conexões lentas
# --retries=3 para tentar novamente em caso de falha na rede
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 --retries=3 -r /app/requirements_deploy.txt

# Copie os arquivos do modelo da pasta 'modelo/' (relativo ao contexto do build)
# para o diretório de trabalho /app no container.
COPY modelo/melhor_modelo_lstm.keras /app/melhor_modelo_lstm.keras
COPY modelo/min_max_scaler.gz /app/min_max_scaler.gz

# Copie o script da aplicação FastAPI da pasta 'deploy_lstm/' (relativo ao contexto do build)
# para o diretório de trabalho /app no container.
COPY deploy_lstm/api_deploy_fastapi.py /app/api_deploy_fastapi.py

# Se houver outros arquivos dentro de 'deploy_lstm/' que sua aplicação precise,
# copie-os também. Por exemplo:
# COPY deploy_lstm/outros_arquivos_necessarios.py /app/

# Exponha a porta que a aplicação usará.
EXPOSE 8000

# Comando para executar a aplicação quando o container iniciar.
# uvicorn api_deploy_fastapi:app --host 0.0.0.0 --port 8000
CMD ["uvicorn", "api_deploy_fastapi:app", "--host", "0.0.0.0", "--port", "8000"]
