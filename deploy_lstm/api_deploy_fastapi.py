# deploy_lstm/api_deploy_fastapi.py
from fastapi import FastAPI, HTTPException, Request, Body 
from pydantic import BaseModel, Field 
import numpy as np
import tensorflow as tf
import joblib
import logging
import time 
from typing import List
from starlette_exporter import PrometheusMiddleware, handle_metrics
from prometheus_client import Counter, Histogram 

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API de Previsão de Preços de Ações com LSTM",
    description="Esta API recebe uma sequência de preços de fecho históricos e retorna a previsão para o próximo dia.",
    version="1.0.5" # Versão atualizada
)

# --- Métricas Prometheus ---
PREVISOES_TOTAL = Counter("api_previsoes_total", "Número total de previsões solicitadas.")
ERROS_PREVISAO_TOTAL = Counter("api_erros_previsao_total", "Número total de erros durante o processamento de previsões.")
TEMPO_PROCESSAMENTO_PREVISAO = Histogram("api_tempo_processamento_previsao_seconds", "Histograma do tempo de processamento para as previsões.", buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0])
MODELO_CARREGADO_SUCESSO = Counter("api_modelo_carregado_sucesso_total", "Contador para indicar se o modelo foi carregado com sucesso na inicialização.")
MODELO_CARREGADO_FALHA = Counter("api_modelo_carregado_falha_total", "Contador para indicar se houve falha ao carregar o modelo na inicialização.")

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics) 

MODEL_PATH = "melhor_modelo_lstm.keras" 
SCALER_PATH = "min_max_scaler.gz"   
TAMANHO_JANELA = 60  

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
    
    if modelo is None or scaler is None:
        logger.error("Modelo ou scaler não foram carregados. A API pode não funcionar como esperado.")
    else:
        logger.info("API iniciada e pronta para receber requisições.")

# --- Modelos Pydantic ---
class DadosHistoricos(BaseModel):
    precos_fechamento: List[float] = Field(
        ..., 
        description=f"Uma lista de exatamente {TAMANHO_JANELA} preços de fecho históricos."
    )

class PrevisaoResponse(BaseModel):
    previsao_proximo_dia: float = Field(..., example=16.05, description="O preço previsto para o próximo dia de negociação.")

class HealthResponse(BaseModel):
    status: str = Field(..., example="ok", description="Indica o estado da API ('ok' ou 'error').")
    message: str = Field(..., example="Modelo carregado e API operacional.", description="Uma mensagem detalhando o estado.")


# Exemplo de dados para o corpo da requisição da rota /prever/
exemplo_previsao_body = {
    "precos_fechamento": [
        10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9,
        11.0, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9,
        12.0, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9,
        13.0, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9,
        14.0, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9,
        15.0, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9
    ]
}

@app.post(
    "/prever/",
    response_model=PrevisaoResponse, 
    responses={
        200: {
            "description": "Previsão bem-sucedida do preço da ação.",
            "content": {
                "application/json": {
                    "example": {"previsao_proximo_dia": 16.05}
                }
            },
        },
        400: {
            "description": "Erro de Validação: Dados de entrada inválidos.",
            "content": {
                "application/json": {
                    "example": {"detail": f"A lista 'precos_fechamento' deve conter exatamente {TAMANHO_JANELA} valores."}
                }
            },
        },
        503: {
            "description": "Serviço Indisponível: Modelo não carregado.",
             "content": {
                "application/json": {
                    "example": {"detail": "Modelo não está disponível no momento. Tente novamente mais tarde."}
                }
            },
        }
    }
)
async def prever_preco_acao(
    dados_historicos: DadosHistoricos = Body(..., example=exemplo_previsao_body)
):
    """
    Recebe uma lista de preços de fecho históricos e retorna a previsão para o próximo dia.
    A lista deve conter exatamente `TAMANHO_JANELA` (ex: 60) preços.
    """
    start_time = time.time() 

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
        
        PREVISOES_TOTAL.inc() 
        
        processing_time = time.time() - start_time 
        TEMPO_PROCESSAMENTO_PREVISAO.observe(processing_time) 

        return PrevisaoResponse(previsao_proximo_dia=preco_previsto)

    except Exception as e:
        logger.error(f"Erro durante a previsão: {e}", exc_info=True)
        ERROS_PREVISAO_TOTAL.inc() 
        processing_time = time.time() - start_time 
        TEMPO_PROCESSAMENTO_PREVISAO.observe(processing_time) 
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar a previsão: {str(e)}")

@app.get(
    "/health",
    response_model=HealthResponse, # Indica o modelo Pydantic da resposta
    responses={
        200: {
            "description": "Verificação de saúde bem-sucedida.",
            "content": {
                "application/json": {
                    "examples": { # Usar 'examples' para múltiplos cenários
                        "api_ok": {
                            "summary": "API operacional",
                            "value": {"status": "ok", "message": "Modelo carregado e API operacional."}
                        },
                        "api_error_modelo": {
                            "summary": "Erro no modelo",
                            "value": {"status": "error", "message": "Modelo ou scaler não carregado."}
                        }
                    }
                }
            },
        }
    }
)
async def health_check():
    """Verifica a saúde da API e a disponibilidade do modelo."""
    if modelo is not None and scaler is not None:
        return HealthResponse(status="ok", message="Modelo carregado e API operacional.")
    else:
        # Ainda que a função retorne este dicionário, a documentação OpenAPI gerada por `response_model`
        # e `responses` é o que a Swagger UI usa para exibir o esquema e exemplos.
        # O FastAPI validará que o retorno corresponde ao HealthResponse.
        return HealthResponse(status="error", message="Modelo ou scaler não carregado.")

