# **Tech Challenge Fase 4 \- Previsão de Preços de Ações com LSTM e Monitoramento**

Este projeto é uma solução desenvolvida para o Tech Challenge da Fase 4 do curso de Machine Learning Engineering, com o objetivo de criar um modelo preditivo de redes neurais Long Short Term Memory (LSTM) para prever o valor de fechamento da bolsa de valores de uma empresa, e implementar toda a pipeline de desenvolvimento, desde a criação do modelo até o deploy e monitoramento.

## **🎯 Objetivo**

O principal objetivo é desenvolver um modelo LSTM capaz de prever o preço de fechamento de ações, utilizando dados históricos. Além do modelo, o projeto inclui:

* Uma API para servir o modelo treinado.  
* Conteinerização da solução utilizando Docker.  
* Uma stack de monitoramento com Prometheus e Grafana para observar o desempenho da API e as métricas do modelo em "produção".

## **✨ Tecnologias Utilizadas**

* **Linguagem de Programação:** Python 3.9+  
* **Machine Learning:**  
  * TensorFlow / Keras (para construção e treino do modelo LSTM)  
  * Scikit-learn (para pré-processamento de dados, como o MinMaxScaler)  
  * Pandas & NumPy (para manipulação de dados)  
  * Yfinance (para coleta de dados históricos de ações)  
  * Joblib (para salvar/carregar o scaler)  
* **API:** FastAPI  
* **Conteinerização:** Docker, Docker Compose  
* **Monitoramento:**  
  * Prometheus (para coleta de métricas)  
  * Grafana (para visualização de dashboards e métricas)  
  * Starlette-Exporter (para expor métricas da API FastAPI)  
* **Notebook:** Jupyter Notebook (para treino e experimentação do modelo)  
* **Testes:** Scripts Python com a biblioteca requests.

## **📂 Estrutura do Projeto**

TECH\_CHALLENGE\_4/  
├── .venv/                          \# Ambiente virtual Python (opcional, não versionado)  
├── deploy\_lstm/                    \# Módulo da API de deploy e configurações de monitoramento  
│   ├── \_\_pycache\_\_/                \# Cache do Python  
│   ├── api\_deploy\_fastapi.py       \# Script da API FastAPI para servir o modelo  
│   ├── Dockerfile                  \# Dockerfile para construir a imagem da API  
│   ├── prometheus.yml              \# Configuração do Prometheus  
│   └── requirements\_deploy.txt     \# Dependências Python para a API  
├── grafana\_provisioning/           \# Configurações de provisioning para o Grafana  
│   ├── dashboards/  
│   │   ├── dashboard\_config.yml    \# Configuração do provedor de dashboards do Grafana  
│   │   └── lstm\_dashboard.json     \# JSON do dashboard exportado para o Grafana  
│   └── datasources/  
│       └── prometheus\_ds.yml       \# Configuração da fonte de dados Prometheus para o Grafana  
├── modelo/                         \# Modelos e scalers treinados  
│   ├── melhor\_modelo\_lstm.keras  \# Modelo LSTM treinado e salvo 
│   ├── min\_max\_scaler.gz         \# Scaler (MinMaxScaler) salvo
│   └── treinamento\_LSTM.ipynb          \# Jupyter Notebook para coleta, pré-processamento, treino e avaliação do modelo
├── tests/                          \# Scripts de teste  
│   └── api\_load\_tester.py          \# Script para gerar carga na API e testar monitoramento  
├── .gitignore                      \# Especifica arquivos e pastas ignorados pelo Git  
├── consumidor\_api\_exemplo.py       \# Script Python para consumir a API (exemplo)  
├── docker-compose.yml              \# Define e orquestra os serviços Docker (API, Prometheus, Grafana)  
├── LICENSE                         \# Licença do projeto (MIT)  
├── requirements.txt                \# Dependências Python para o ambiente de desenvolvimento/notebook  
├── run\_monitoring\_stack.ps1        \# Script PowerShell para iniciar a stack Docker no Windows  
└── run\_monitoring\_stack.sh         \# Script Shell para iniciar a stack Docker no Linux/macOS  
 

## **⚙️ Pré-requisitos**

Antes de começar, garanta que você tem os seguintes softwares instalados:

* Python (versão 3.9 ou superior)  
* Pip (gerenciador de pacotes Python)  
* Docker  
* Docker Compose (geralmente incluído com o Docker Desktop)  
* Git (para clonar o repositório)

## **🚀 Como Executar**

### **1\. Clone o Repositório**

git clone https://github.com/willalveslima/Tech_Challenge_4.git  
cd TECH\_CHALLENGE\_4

### **2\. Ambiente de Desenvolvimento e Treinamento do Modelo**

Recomenda-se o uso de um ambiente virtual Python.

python \-m venv .venv  
source .venv/bin/activate  \# Linux/macOS  
\# .venv\\Scripts\\activate    \# Windows

Instale as dependências para o notebook e desenvolvimento:

pip install \-r requirements.txt

Abra e execute o Jupyter Notebook treinamento\_LSTM.ipynb para:

* Coletar os dados históricos das ações.  
* Pré-processar os dados.  
* Treinar o modelo LSTM.  
* Avaliar o modelo.  
* Salvar o modelo treinado (melhor\_modelo\_lstm.keras) e o scaler (min\_max\_scaler.gz) na pasta modelo/.

**Nota:** Certifique-se que os arquivos melhor\_modelo\_lstm.keras e min\_max\_scaler.gz estejam presentes na pasta modelo/ antes de prosseguir para o deploy.

### **3\. Executando a Stack Completa (API, Prometheus, Grafana) com Docker Compose**

Os scripts run\_monitoring\_stack.sh (para Linux/macOS) e run\_monitoring\_stack.ps1 (para Windows) automatizam o processo de build e execução dos contêineres. Execute o script apropriado a partir da raiz do projeto (TECH\_CHALLENGE\_4/):

**Linux/macOS:**

chmod \+x run\_monitoring\_stack.sh  
./run\_monitoring\_stack.sh

**Windows (PowerShell):**

\# Pode ser necessário ajustar a política de execução do PowerShell:  
\# Set-ExecutionPolicy RemoteSigned \-Scope CurrentUser  
.\\run\_monitoring\_stack.ps1

Estes scripts irão:

1. Parar e remover quaisquer contêineres e volumes da execução anterior.  
2. Construir a imagem Docker para a API FastAPI (se necessário).  
3. Iniciar os serviços:  
   * **API de Previsão LSTM:** http://localhost:8000  
   * **Métricas da API (Prometheus scrape target):** http://localhost:8000/metrics  
   * **Servidor Prometheus:** http://localhost:9090  
   * **Servidor Grafana:** http://localhost:3000 (Login padrão: admin / grafana)

### **4\. Acessando os Serviços**

* **API:**  
  * Documentação Interativa (Swagger UI): http://localhost:8000/docs  
  * Documentação Alternativa (ReDoc): http://localhost:8000/redoc  
  * Endpoint de Saúde: http://localhost:8000/health  
  * Endpoint de Previsão: POST http://localhost:8000/prever/  
* **Prometheus:** http://localhost:9090  
  * Verifique "Status" \-\> "Targets" para confirmar que fastapi\_app está "UP".  
* **Grafana:** http://localhost:3000  
  * A fonte de dados Prometheus e um dashboard de exemplo (lstm\_dashboard.json) devem ser provisionados automaticamente.

### **5\. Consumindo a API**

* Utilize o script consumidor\_api\_exemplo.py (localizado na raiz do projeto) para enviar uma requisição de exemplo para a API:  
  python consumidor\_api\_exemplo.py

### **6\. Testando a Carga e Monitoramento**

* Utilize o script tests/api\_load\_tester.py para gerar múltiplas requisições para a API:  
  python tests/api\_load\_tester.py

  Enquanto este script roda, observe os dashboards no Grafana para ver as métricas em tempo real.

### **7\. Interrompendo a Stack Docker Compose**

Para parar todos os serviços:

docker-compose down \--volumes \# Executar na raiz do projeto  
\# Ou use o comando específico informado no final da execução dos scripts de inicialização.

## **🛠️ Componentes Principais**

### **API de Deploy (deploy\_lstm/api\_deploy\_fastapi.py)**

* Serve o modelo LSTM treinado.  
* Endpoint POST /prever/: Recebe uma lista de 60 preços de fechamento históricos e retorna a previsão para o próximo dia.  
* Endpoint GET /health: Verifica a saúde da API e se o modelo está carregado.  
* Endpoint GET /metrics: Expõe métricas para o Prometheus (via starlette-exporter).

### **Monitoramento**

* **Prometheus (deploy\_lstm/prometheus.yml):** Configurado para fazer scrape das métricas do endpoint /metrics da API.  
* **Grafana (grafana\_provisioning/):**  
  * **Fonte de Dados:** O Prometheus é provisionado automaticamente como fonte de dados (grafana\_provisioning/datasources/prometheus\_ds.yml).  
  * **Dashboard:** Um dashboard de exemplo (lstm\_dashboard.json) é provisionado (grafana\_provisioning/dashboards/). Este dashboard pode incluir gráficos para:  
    * Taxa de requisições.  
    * Latência das requisições (média, p95, p99).  
    * Taxa de erros (HTTP 5xx, erros da API).  
    * Contagem de previsões, erros de previsão.  
    * Tempo de processamento das previsões.  
    * Estado de carregamento do modelo.

## **📜 Licença**

Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE](http://docs.google.com/LICENSE) para mais detalhes.

## **👨‍💻 Autor(es)**

* \[Willian Alves Lima\] \- \[https://willalveslima.github.io\]

*Este README foi gerado para auxiliar na documentação do projeto Tech Challenge Fase 4\.*