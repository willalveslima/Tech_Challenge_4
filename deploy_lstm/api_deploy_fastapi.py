# deploy_lstm/api_deploy_fastapi.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
import joblib
import logging
from typing import List

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API de Previsão de Preços de Ações com LSTM",
    description="Esta API recebe uma sequência de preços de fechamento históricos e retorna a previsão para o próximo dia.",
    version="1.0.0"
)

# Carregar o modelo e o scaler ao iniciar a API
MODEL_PATH = "melhor_modelo_lstm.keras"
SCALER_PATH = "min_max_scaler.gz"
TAMANHO_JANELA = 60  # Deve ser o mesmo usado no treinamento

try:
    logger.info(f"Carregando modelo de: {MODEL_PATH}")
    modelo = tf.keras.models.load_model(MODEL_PATH)
    logger.info("Modelo carregado com sucesso.")
    
    logger.info(f"Carregando scaler de: {SCALER_PATH}")
    scaler = joblib.load(SCALER_PATH)
    logger.info("Scaler carregado com sucesso.")
except Exception as e:
    logger.error(f"Erro ao carregar modelo ou scaler: {e}", exc_info=True)
    # Se não conseguir carregar, a API não deve iniciar corretamente.
    # Em um cenário de produção, você pode querer que a aplicação falhe ao iniciar.
    modelo = None
    scaler = None

class DadosHistoricos(BaseModel):
    precos_fechamento: List[float]

    class Config:
        schema_extra = {
            "example": {
                "precos_fechamento": [10.0, 10.1, 10.2, ..., 12.5] # Lista com 'TAMANHO_JANELA' preços
            }
        }

@app.on_event("startup")
async def startup_event():
    if modelo is None or scaler is None:
        logger.error("Modelo ou scaler não foram carregados. A API pode não funcionar como esperado.")
    else:
        logger.info("API iniciada e pronta para receber requisições.")

@app.post("/prever/")
async def prever_preco_acao(dados_historicos: DadosHistoricos):
    """
    Recebe uma lista de preços de fechamento históricos e retorna a previsão para o próximo dia.
    A lista deve conter exatamente `TAMANHO_JANELA` (ex: 60) preços.
    """
    if modelo is None or scaler is None:
        logger.error("Tentativa de previsão com modelo ou scaler não carregado.")
        raise HTTPException(status_code=503, detail="Modelo não está disponível no momento. Tente novamente mais tarde.")

    if len(dados_historicos.precos_fechamento) != TAMANHO_JANELA:
        logger.warning(f"Dados de entrada com tamanho incorreto: {len(dados_historicos.precos_fechamento)}. Esperado: {TAMANHO_JANELA}")
        raise HTTPException(
            status_code=400,
            detail=f"A lista 'precos_fechamento' deve conter exatamente {TAMANHO_JANELA} valores."
        )

    try:
        logger.info(f"Recebidos {len(dados_historicos.precos_fechamento)} preços para previsão.")
        
        # 1. Converter para numpy array e reshape
        ultimos_dados = np.array(dados_historicos.precos_fechamento).reshape(-1, 1)
        
        # 2. Normalizar os dados usando o scaler carregado
        ultimos_dados_normalizados = scaler.transform(ultimos_dados)
        
        # 3. Remodelar para o formato da LSTM [amostras, passos_no_tempo, features]
        input_para_previsao = np.reshape(ultimos_dados_normalizados, (1, TAMANHO_JANELA, 1))
        
        # 4. Fazer a previsão com o modelo treinado
        logger.info("Realizando previsão com o modelo...")
        previsao_normalizada = modelo.predict(input_para_previsao)
        
        # 5. Desnormalizar a previsão
        previsao_desnormalizada = scaler.inverse_transform(previsao_normalizada)
        
        preco_previsto = float(previsao_desnormalizada[0, 0])
        logger.info(f"Previsão gerada: {preco_previsto}")
        
        return {"previsao_proximo_dia": preco_previsto}

    except Exception as e:
        logger.error(f"Erro durante a previsão: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar a previsão: {str(e)}")

@app.get("/health")
async def health_check():
    """Verifica a saúde da API e a disponibilidade do modelo."""
    if modelo is not None and scaler is not None:
        return {"status": "ok", "message": "Modelo carregado e API operacional."}
    else:
        return {"status": "error", "message": "Modelo ou scaler não carregado."}

# Para executar localmente: uvicorn api_deploy_fastapi:app --reload --port 8000
# Certifique-se de ter os arquivos 'melhor_modelo_lstm.keras' e 'min_max_scaler.gz' na mesma pasta.
