# api_coleta_dados.py
from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
from datetime import datetime

app = Flask(__name__)


@app.route('/historico_acoes', methods=['GET'])
def get_historico_acoes():
    """
    Endpoint para buscar o histórico de preços de uma ação.
    Query Params:
        simbolo (str): O símbolo da ação (ex: 'PETR4.SA', 'AAPL').
        data_inicio (str): Data de início no formato 'YYYY-MM-DD'.
        data_fim (str): Data de fim no formato 'YYYY-MM-DD'.
    Retorna:
        JSON com os dados históricos ou uma mensagem de erro.
    """
    simbolo = request.args.get('simbolo')
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')

    # Validação básica dos parâmetros
    if not all([simbolo, data_inicio_str, data_fim_str]):
        return jsonify({"erro": "Parâmetros 'simbolo', 'data_inicio' e 'data_fim' são obrigatórios."}), 400

    try:
        # Validação do formato das datas
        datetime.strptime(data_inicio_str, '%Y-%m-%d')
        datetime.strptime(data_fim_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"erro": "Formato de data inválido. Use 'YYYY-MM-DD'."}), 400

    try:
        # Baixando os dados usando yfinance
        dados = yf.download(simbolo, start=data_inicio_str, end=data_fim_str)

        if dados.empty:
            return jsonify({"erro": f"Nenhum dado encontrado para o símbolo '{simbolo}' no período especificado."}), 404

        # --- INÍCIO DA CORREÇÃO ---
        # Garantir que os nomes das colunas sejam strings
        # Isso é importante porque yfinance pode retornar colunas com MultiIndex ou nomes de tupla
        if isinstance(dados.columns, pd.MultiIndex):
            # Se for MultiIndex, une os níveis com underscore
            # Ex: ('Adj Close', 'AAPL') se tornaria 'Adj Close_AAPL'
            #dados.columns = ['_'.join(map(str, col)).strip() for col in dados.columns.values]
            dados.columns = [str(col[0]) for col in dados.columns.values]
        else:
            # Se for um Index simples, apenas converte cada nome para string
            dados.columns = [str(col) for col in dados.columns]
        # --- FIM DA CORREÇÃO ---
        # Convertendo o índice (Data) para string para serialização JSON
        # O nome do índice também deve ser uma string se for usado após reset_index()
        if dados.index.name is not None:
            dados.index.name = str(dados.index.name)
        else:
            # Se o índice não tiver nome, reset_index() criará uma coluna 'index' ou 'level_0'
            # que já são strings.
            pass

        dados_resetados = dados.reset_index()

        # Garante que a nova coluna de índice (geralmente 'Date' ou 'index') também seja string
        dados_resetados.columns = [str(col) for col in dados_resetados.columns]

        # Convertendo o DataFrame para uma lista de dicionários JSON compatível
        dados_json = dados_resetados.to_dict(orient='records')

        return jsonify(dados_json), 200

    except Exception as e:
        # Para depuração, é útil logar o erro completo no servidor
        app.logger.error(f"Erro detalhado: {e}", exc_info=True)
        return jsonify({"erro": f"Erro ao buscar dados: {str(e)}"}), 500


if __name__ == '__main__':
    # Executar o app: python api_coleta_dados.py
    # Exemplo de URL para testar no navegador ou Postman:
    # http://127.0.0.1:5001/historico_acoes?simbolo=PETR4.SA&data_inicio=2023-01-01&data_fim=2023-12-31
    app.run(debug=True, port=5001)
