# deploy_lstm/consumir_api_deploy.py
import requests
import json
import numpy as np # Apenas para gerar dados de exemplo sintéticos
import yfinance as yf # Para buscar dados reais

# URL da sua API (ajuste se estiver rodando em outro host/porta)
API_URL = "http://127.0.0.1:8000/prever/"
HEALTH_URL = "http://127.0.0.1:8000/health"

TAMANHO_JANELA = 60 # Deve ser o mesmo usado no treinamento e na API
USAR_DADOS_REAIS_YFINANCE = True # Mude para False para usar dados sintéticos

def verificar_saude_api():
    """Verifica o endpoint de saúde da API."""
    try:
        response = requests.get(HEALTH_URL)
        response.raise_for_status() # Lança exceção para erros HTTP
        print("Status da API:")
        print(json.dumps(response.json(), indent=2))
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao verificar a saúde da API: {e}")
        return False

def obter_previsao(dados_historicos: list):
    """
    Envia dados históricos para a API e obtém a previsão.
    Args:
        dados_historicos (list): Lista de floats com 'TAMANHO_JANELA' preços.
    """
    #if len(dados_historicos) != TAMANHO_JANELA:
    #    print(f"Erro: Os dados históricos devem conter {TAMANHO_JANELA} valores.")
    #    return None

    # Garantir que todos os elementos são floats Python
    dados_historicos_float = [float(preco) for preco in dados_historicos]
    payload = {"precos_fechamento": dados_historicos_float}
    
    try:
        print(f"\nEnviando {len(dados_historicos_float)} preços para {API_URL}...")
        # print(f"Payload: {json.dumps(payload)}") # Descomente para depurar o payload
        
        response = requests.post(API_URL, json=payload)
        response.raise_for_status() # Lança uma exceção para respostas de erro (4xx ou 5xx)
        
        resultado = response.json()
        print("Resposta da API:")
        print(json.dumps(resultado, indent=2))
        return resultado
        
    except requests.exceptions.HTTPError as http_err:
        print(f"Erro HTTP da API: {http_err}")
        try:
            print(f"Detalhes do erro da API: {response.json()}")
        except json.JSONDecodeError:
            print(f"Resposta não JSON: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer requisição para a API: {e}")
    return None

if __name__ == "__main__":
    if not verificar_saude_api():
        print("API não está saudável. Verifique o servidor da API.")
    else:
        dados_exemplo = []
        if USAR_DADOS_REAIS_YFINANCE:
            print("Tentando buscar dados reais com yfinance...")
            try:
                # Buscar um pouco mais de dados para garantir que temos o suficiente após remover NaNs etc.
                # E para ter dados recentes.
                simbolo_acao_teste = "PETR4.SA" # Ou qualquer outro símbolo que seu modelo espera
                dados_reais_yf = yf.download(simbolo_acao_teste, period=f"{TAMANHO_JANELA+30}d", progress=False) 
                
                if not dados_reais_yf.empty and 'Close' in dados_reais_yf.columns:
                    # Remover quaisquer NaNs que possam ter surgido (ex: dias sem negociação no início)
                    precos_fechamento_reais = dados_reais_yf['Close'].dropna().values
                    if len(precos_fechamento_reais) >= TAMANHO_JANELA:
                        # Pegar os últimos TAMANHO_JANELA valores e converter para lista de floats Python
                        dados_exemplo = [float(preco) for preco in precos_fechamento_reais[-TAMANHO_JANELA:]]
                        print(f"Dados reais de {simbolo_acao_teste} coletados com sucesso.")
                    else:
                        print(f"Não foi possível obter {TAMANHO_JANELA} pontos de dados reais de fechamento para {simbolo_acao_teste} após limpeza. Obtidos: {len(precos_fechamento_reais)}")
                else:
                    print(f"Nenhum dado de fechamento encontrado para {simbolo_acao_teste} com yfinance.")
            except Exception as e:
                print(f"Erro ao buscar dados reais com yfinance: {e}")
        
        if not dados_exemplo: # Se falhou em obter dados reais ou USAR_DADOS_REAIS_YFINANCE é False
            print("Usando dados sintéticos de exemplo.")
            # Gerar dados sintéticos como fallback
            dados_exemplo = [float(val) for val in np.linspace(start=30.0, stop=35.0, num=TAMANHO_JANELA)]


        if not dados_exemplo:
            print("Não foi possível obter ou gerar dados de exemplo. Encerrando.")
        else:
            print(f"\nUsando dados (primeiros 5): {dados_exemplo[:5]}...")
            print(f"Usando dados (últimos 5): {dados_exemplo[-5:]}...")
            
            previsao = obter_previsao(dados_exemplo)
            
            if previsao and "previsao_proximo_dia" in previsao:
                print(f"\nPreço previsto para o próximo dia: {previsao['previsao_proximo_dia']:.2f}")

            # Exemplo com dados incorretos (tamanho errado)
            print("\n--- Testando com dados de tamanho incorreto ---")
            dados_tamanho_errado = [10.0, 11.0, 12.0] # Tamanho menor que TAMANHO_JANELA
            obter_previsao(dados_tamanho_errado)
