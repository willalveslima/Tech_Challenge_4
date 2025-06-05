# deploy_lstm/api_deploy_fastapi.py
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
import joblib
import logging
import time # Para medir o tempo de processamento
from typing import List
from starlette_exporter import PrometheusMiddleware, handle_metrics
from prometheus_client import Counter, Histogram # Tipos de métricas

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API de Previsão de Preços de Ações com LSTM",
    description="Esta API recebe uma sequência de preços de fecho históricos e retorna a previsão para o próximo dia.",
    version="1.0.1" # Versão atualizada
)

# --- Métricas Prometheus ---
# Métricas padrão (tempo de requisição, etc.) são adicionadas pelo middleware.
# Métricas personalizadas:
PREVISOES_TOTAL = Counter(
    "api_previsoes_total",
    "Número total de previsões solicitadas."
)
ERROS_PREVISAO_TOTAL = Counter(
    "api_erros_previsao_total",
    "Número total de erros durante o processamento de previsões."
)
TEMPO_PROCESSAMENTO_PREVISAO = Histogram(
    "api_tempo_processamento_previsao_seconds",
    "Histograma do tempo de processamento para as previsões.",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0] # Buckets em segundos
)
MODELO_CARREGADO_SUCESSO = Counter(
    "api_modelo_carregado_sucesso_total",
    "Contador para indicar se o modelo foi carregado com sucesso na inicialização."
)
MODELO_CARREGADO_FALHA = Counter(
    "api_modelo_carregado_falha_total",
    "Contador para indicar se houve falha ao carregar o modelo na inicialização."
)


# Adicionar o middleware do Prometheus para expor métricas no endpoint /metrics
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics) # Endpoint para o Prometheus recolher

# Carregar o modelo e o scaler ao iniciar a API
MODEL_PATH = "melhor_modelo_lstm.keras" # Caminho relativo ao WORKDIR no Dockerfile (/app)
SCALER_PATH = "min_max_scaler.gz"   # Caminho relativo ao WORKDIR no Dockerfile (/app)
TAMANHO_JANELA = 60  # Deve ser o mesmo usado no treino

modelo = None
scaler = None

@app.on_event("startup")
async def startup_event():
    global modelo, scaler
    try:
        logger.info(f"A carregar modelo de: {MODEL_PATH}")
        modelo = tf.keras.models.load_model(MODEL_PATH)
        logger.info("Modelo carregado com sucesso.")
        
        logger.info(f"A carregar scaler de: {SCALER_PATH}")
        scaler = joblib.load(SCALER_PATH)
        logger.info("Scaler carregado com sucesso.")
        MODELO_CARREGADO_SUCESSO.inc()
    except Exception as e:
        logger.error(f"Erro ao carregar modelo ou scaler: {e}", exc_info=True)
        MODELO_CARREGADO_FALHA.inc()
        # A API ainda iniciará, mas o endpoint /health e as previsões indicarão o problema.
    
    if modelo is None or scaler is None:
        logger.error("Modelo ou scaler não foram carregados. A API pode não funcionar como esperado.")
    else:
        logger.info("API iniciada e pronta para receber requisições.")


class DadosHistoricos(BaseModel):
    precos_fechamento: List[float]

    class Config:
        schema_extra = {
            "example": {
                "precos_fechamento": [10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9,
                                      11.0, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9,
                                      12.0, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9,
                                      13.0, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9,
                                      14.0, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9,
                                      15.0, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9] 
                                      # Lista com 'TAMANHO_JANELA' preços (ex: 60)
            }
        }

@app.post("/prever/")
async def prever_preco_acao(dados_historicos: DadosHistoricos):
    """
    Recebe uma lista de preços de fecho históricos e retorna a previsão para o próximo dia.
    A lista deve conter exatamente `TAMANHO_JANELA` (ex: 60) preços.
    """
    start_time = time.time() # Início da medição de tempo

    if modelo is None or scaler is None:
        logger.error("Tentativa de previsão com modelo ou scaler não carregado.")
        ERROS_PREVISAO_TOTAL.inc()
        raise HTTPException(status_code=503, detail="Modelo não está disponível no momento. Tente novamente mais tarde.")

    if len(dados_historicos.precos_fechamento) != TAMANHO_JANELA:
        logger.warning(f"Dados de entrada com tamanho incorreto: {len(dados_historicos.precos_fechamento)}. Esperado: {TAMANHO_JANELA}")
        ERROS_PREVISAO_TOTAL.inc()
        raise HTTPException(
            status_code=400,
            detail=f"A lista 'precos_fechamento' deve conter exatamente {TAMANHO_JANELA} valores."
        )

    try:
        logger.info(f"Recebidos {len(dados_historicos.precos_fechamento)} preços para previsão.")
        
        ultimos_dados = np.array(dados_historicos.precos_fechamento).reshape(-1, 1)
        ultimos_dados_normalizados = scaler.transform(ultimos_dados)
        input_para_previsao = np.reshape(ultimos_dados_normalizados, (1, TAMANHO_JANELA, 1))
        
        logger.info("A realizar previsão com o modelo...")
        previsao_normalizada = modelo.predict(input_para_previsao)
        previsao_desnormalizada = scaler.inverse_transform(previsao_normalizada)
        
        preco_previsto = float(previsao_desnormalizada[0, 0])
        logger.info(f"Previsão gerada: {preco_previsto}")
        
        PREVISOES_TOTAL.inc() # Incrementar contador de previsões bem-sucedidas
        
        processing_time = time.time() - start_time # Tempo total de processamento
        TEMPO_PROCESSAMENTO_PREVISAO.observe(processing_time) # Observar o tempo

        return {"previsao_proximo_dia": preco_previsto}

    except Exception as e:
        logger.error(f"Erro durante a previsão: {e}", exc_info=True)
        ERROS_PREVISAO_TOTAL.inc() # Incrementar contador de erros
        processing_time = time.time() - start_time # Tempo total de processamento (mesmo com erro)
        TEMPO_PROCESSAMENTO_PREVISAO.observe(processing_time) # Observar o tempo
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar a previsão: {str(e)}")

@app.get("/health")
async def health_check():
    if modelo is not None and scaler is not None:
        return {"status": "ok", "message": "Modelo carregado e API operacional."}
    else:
        return {"status": "error", "message": "Modelo ou scaler não carregado."}

# Para executar localmente: uvicorn api_deploy_fastapi:app --reload --port 8000
# Certifique-se de ter os ficheiros 'melhor_modelo_lstm.keras' e 'min_max_scaler.gz' na mesma pasta.
