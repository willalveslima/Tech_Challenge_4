# tests/api_load_tester.py
import requests
import json
import time
import random
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configurações ---
API_URL = "http://127.0.0.1:8000/prever/"
HEALTH_URL = "http://127.0.0.1:8000/health"
TAMANHO_JANELA = 60  # Deve ser o mesmo usado no treino e na API

NUMERO_REQUISICOES = 100  # Quantas requisições totais fazer
MAX_TRABALHADORES_CONCORRENTES = 10 # Quantas requisições fazer em paralelo
DELAY_ENTRE_REQUISICOES_S = 0.1 # Pequeno delay para não sobrecarregar instantaneamente

# --- Funções ---

def gerar_dados_historicos_aleatorios(tamanho_janela: int) -> list:
    """Gera uma lista de preços de fecho aleatórios para teste."""
    # Gera preços com uma pequena variação aleatória
    preco_base = random.uniform(20.0, 50.0)
    dados = [preco_base + random.uniform(-1.0, 1.0) for _ in range(tamanho_janela)]
    return [float(f"{d:.2f}") for d in dados] # Garante que são floats com 2 casas decimais

def enviar_requisicao_previsao(id_requisicao: int, dados_historicos: list):
    """Envia uma única requisição de previsão para a API."""
    payload = {"precos_fechamento": dados_historicos}
    try:
        start_time = time.time()
        response = requests.post(API_URL, json=payload, timeout=10) # Timeout de 10 segundos
        duration = time.time() - start_time

        if response.status_code == 200:
            # print(f"Req {id_requisicao}: Sucesso ({response.status_code}) - Previsão: {response.json().get('previsao_proximo_dia', 'N/A')} - Duração: {duration:.3f}s")
            return {"status": "sucesso", "id": id_requisicao, "duracao": duration, "status_code": response.status_code}
        else:
            # print(f"Req {id_requisicao}: Falha ({response.status_code}) - Resposta: {response.text} - Duração: {duration:.3f}s")
            return {"status": "falha_api", "id": id_requisicao, "duracao": duration, "status_code": response.status_code, "erro": response.text}
    except requests.exceptions.RequestException as e:
        duration = time.time() - start_time
        # print(f"Req {id_requisicao}: Erro de Requisição - {e} - Duração: {duration:.3f}s")
        return {"status": "erro_conexao", "id": id_requisicao, "duracao": duration, "erro": str(e)}

def verificar_saude_api():
    """Verifica o endpoint de saúde da API."""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            print(f"API Saudável: {response.json().get('message')}")
            return True
        else:
            print(f"API Não Saudável (Status {response.status_code}): {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Erro ao verificar saúde da API: {e}")
        return False

# --- Lógica Principal ---
if __name__ == "__main__":
    print("--- Testador de Carga da API de Previsão LSTM ---")

    if not verificar_saude_api():
        print("API não está acessível ou saudável. Saindo do teste de carga.")
        exit(1)

    print(f"A enviar {NUMERO_REQUISICOES} requisições para {API_URL} usando até {MAX_TRABALHADORES_CONCORRENTES} trabalhadores concorrentes.")
    
    sucessos = 0
    falhas_api = 0
    erros_conexao = 0
    tempos_resposta = []

    # Usar ThreadPoolExecutor para enviar requisições em paralelo
    with ThreadPoolExecutor(max_workers=MAX_TRABALHADORES_CONCORRENTES) as executor:
        futuros = []
        for i in range(NUMERO_REQUISICOES):
            dados_teste = gerar_dados_historicos_aleatorios(TAMANHO_JANELA)
            futuros.append(executor.submit(enviar_requisicao_previsao, i + 1, dados_teste))
            time.sleep(DELAY_ENTRE_REQUISICOES_S) # Espaçamento entre o envio das tasks

        print(f"Todas as {NUMERO_REQUISICOES} tarefas de requisição foram submetidas.")
        print("A aguardar resultados...")

        # Recolher resultados à medida que ficam prontos
        for i, futuro in enumerate(as_completed(futuros)):
            resultado = futuro.result()
            tempos_resposta.append(resultado.get("duracao", 0))

            if resultado["status"] == "sucesso":
                sucessos += 1
            elif resultado["status"] == "falha_api":
                falhas_api += 1
            elif resultado["status"] == "erro_conexao":
                erros_conexao += 1
            
            # Imprimir progresso a cada X requisições
            if (i + 1) % (NUMERO_REQUISICOES // 10 or 1) == 0 :
                 print(f"Progresso: {i + 1}/{NUMERO_REQUISICOES} requisições processadas.")


    print("\n--- Resumo do Teste de Carga ---")
    print(f"Total de Requisições Enviadas: {NUMERO_REQUISICOES}")
    print(f"  Sucessos (HTTP 200): {sucessos}")
    print(f"  Falhas da API (Outros HTTP): {falhas_api}")
    print(f"  Erros de Conexão/Timeout: {erros_conexao}")

    if tempos_resposta:
        tempo_medio = sum(tempos_resposta) / len(tempos_resposta)
        tempo_maximo = max(tempos_resposta)
        tempo_minimo = min(tempos_resposta)
        print(f"\nEstatísticas do Tempo de Resposta:")
        print(f"  Tempo Médio: {tempo_medio:.3f}s")
        print(f"  Tempo Mínimo: {tempo_minimo:.3f}s")
        print(f"  Tempo Máximo: {tempo_maximo:.3f}s")
    
    print("\nTeste de carga concluído.")
