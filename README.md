# Dashboard de Análise de Qualidade de Sinal Wi-Fi para APM Terminals

## 1\. Visão Geral

Este projeto é uma aplicação web de dashboard projetada para monitorar, visualizar e analisar a qualidade do sinal Wi-Fi de dispositivos móveis (tablets) nas áreas operacionais da **APM Terminals Pecém**. A ferramenta permite que a equipe de TI e operações identifique rapidamente zonas com conectividade deficiente, analise o histórico de medições e exporte dados para relatórios detalhados.

O dashboard processa dados brutos enviados por tablets, os enriquece, e os apresenta de forma intuitiva através de um mapa interativo, indicadores de performance (KPIs) e gráficos analíticos.

## 2\. Funcionalidades Principais

  * **Mapa Interativo:** Visualização geoespacial das medições de sinal, agrupadas em clusters coloridos que representam a qualidade da rede (Bom, Atenção, Crítico).
  * **Dashboard de KPIs:** Cartões com métricas essenciais em tempo real, incluindo o total de medições, a porcentagem de pontos críticos, o número de desconexões e o tablet com o pior desempenho na área.
  * **Gráfico Analítico:** Um gráfico de barras dinâmico que exibe as 10 áreas (clusters) com a maior concentração de problemas (sinal crítico ou de atenção), permitindo focar no mapa ao clicar em uma barra.
  * **Filtragem Avançada:** Os usuários podem filtrar os dados por:
      * **Período:** Selecionando data de início e fim.
      * **Área do Mapa:** Alternando entre diferentes locais pré-configurados (ex: Pátio, TMUT).
      * **Tipo de Rede (SSID):** Filtrando por rede principal, desconexões, ou outras redes.
      * **ID do Dispositivo:** Isolando e analisando os dados de um único tablet.
  * **Controle de Camadas:** Checkboxes interativos para exibir ou ocultar as camadas de sinal (Bom, Atenção, Crítico) no mapa, atualizando dinamicamente a visualização e os contadores.
  * **Exportação para Excel:** Funcionalidade para exportar os dados brutos, já filtrados, para um arquivo `.xlsx`, com os dados organizados em abas por dia.
  * **Atualização Automática:** O dashboard busca por novos dados automaticamente em um intervalo pré-definido, garantindo uma visão sempre atualizada da operação.

## 3\. Arquitetura e Tecnologias

O projeto segue uma arquitetura cliente-servidor clássica.

### Backend

  * **Linguagem:** Python 3
  * **Framework:** Flask
  * **Análise de Dados:** Pandas & NumPy
  * **Banco de Dados:** SQLite
  * **Dependências:** Veja `requirements.txt`.

### Frontend

  * **Estrutura:** HTML5
  * **Estilização:** CSS3 (Dark Mode)
  * **Interatividade:** JavaScript (ES6 Modules)
  * **Biblioteca de Mapas:** Leaflet.js
  * **Biblioteca de Gráficos:** Chart.js

## 4\. Estrutura do Projeto

```
backend/
├── db/
│   ├── dashboard.db              # Banco de dados SQLite
│   └── .last_processed_line      # Arquivo de estado do ETL
├── static/
│   ├── css/
│   │   └── style.css             # Folha de estilos principal
│   └── js/
│       ├── main.js               # Orquestrador principal do frontend
│       ├── api.js                # Funções para chamadas à API
│       ├── map-view.js           # Lógica de controle e renderização do mapa
│       └── chart-view.js         # Lógica de controle e renderização do gráfico
├── templates/
│   └── index.html                # Template principal da aplicação
├── __pycache__/                   # Cache do Python
├── analysis.py                   # Lógica de negócio, classificação e clusterização dos dados
├── app.py                        # Aplicação principal Flask e rotas da API
├── database.py                   # Funções de acesso ao banco de dados
├── process_data.py               # Script ETL para processar CSV e popular o banco
└── requirements.txt              # Dependências do Python
```

## 5\. Instalação e Execução

### Pré-requisitos

  * Python 3.8 ou superior
  * pip

### Passos

1.  **Clone o repositório:**

    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd dashboard-backend
    ```

2.  **Crie e ative um ambiente virtual (Recomendado):**

    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Instale as dependências do Python:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o servidor Flask:**

    ```bash
    flask run --host=0.0.0.0
    ```

    A aplicação estará acessível em `http://127.0.0.1:5000` ou no IP da sua máquina na rede.

## 6\. Processo de ETL (Extração, Transformação e Carga)

O script `process_data.py` é responsável por alimentar o banco de dados.

  * **Fonte:** Ele lê um arquivo `raw_data.csv` localizado em `C:\APPS\Check Signal\data\`.
  * **Processamento:**
    1.  Verifica qual foi a última linha processada através do arquivo `db/.last_processed_line` para evitar duplicidade de dados.
    2.  Lê apenas as novas linhas do CSV.
    3.  Renomeia e formata as colunas para o padrão do banco de dados.
    4.  Converte e combina os campos de data e hora em um único campo `timestamp`.
    5.  Insere os dados tratados na tabela `raw_points` do `dashboard.db`.
    6.  Atualiza o arquivo `.last_processed_line` com o novo total de linhas lidas.
  * **Execução:** Este script pode ser executado manualmente ou agendado para rodar periodicamente (ex: via Agendador de Tarefas do Windows).

## 7\. Endpoints da API

  * `GET /`: Renderiza a página principal do dashboard (`index.html`).
  * `GET /api/map_data`: Retorna os dados geoespaciais clusterizados para a renderização do mapa. Aceita os parâmetros de filtro.
  * `GET /api/critical_points`: Retorna os dados para o gráfico com as 10 piores áreas. Aceita os parâmetros de filtro.
  * `GET /api/kpis`: Retorna os dados agregados para os cartões de KPI. Aceita os parâmetros de filtro.
  * `GET /api/export`: Gera e retorna um arquivo Excel com os dados brutos filtrados.