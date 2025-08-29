# Dashboard de Wi-Fi – APM Terminals

## Objetivo

Este projeto é um **dashboard web autossuficiente e offline-first** criado para a equipa de TI da **APM Terminals**. O seu objetivo é monitorizar, visualizar e analisar a qualidade do sinal Wi-Fi no terminal de forma proativa e detalhada.

O sistema processa logs de conectividade de dispositivos Android, utiliza algoritmos de análise inteligente para identificar e agrupar áreas problemáticas e apresenta essas informações em **KPIs de alto nível, mapas interativos com controlo de camadas e gráficos analíticos sincronizados**.

---

## Arquitetura e Modo de Funcionamento

O sistema foi consolidado numa **aplicação web unificada**, onde o **Backend (Python/Flask)** é responsável por toda a lógica de negócio e também por servir a interface do **Frontend (HTML/CSS/JS)**. Esta arquitetura foi desenhada para funcionar em **ambientes de rede restritos e offline**, sem depender de recursos externos da internet.

-   **Backend (Python/Flask)**
    Responsável pela ingestão e processamento de dados, análises, disponibilização via API REST e por servir a aplicação web completa (HTML, CSS, JS, e tiles de mapa) para o navegador do utilizador.

-   **Frontend (HTML/CSS/JS)**
    Interface de utilizador dinâmica e reativa, renderizada no navegador, que consome a API do próprio backend para exibir todas as visualizações e controlos.

---

## Backend

### Estrutura e Lógica

-   **Fonte de Dados:** `raw_data.csv` com logs de conectividade, incluindo `current_ssid` e `latency_ms`.
-   **Base de Dados:** `db/dashboard.db` (SQLite) – armazena os dados processados na tabela `raw_points`.
-   **Análise Inteligente (`analysis.py`):**
    -   **Classificação:** Categoriza os pontos de medição em `critical`, `attention`, ou `good`.
    -   **Agregação por Grelha:** Para garantir consistência visual, o mapa agrupa os pontos numa grelha geográfica fixa.
    -   **Deteção de Vizinhança (Gráfico):** Utiliza um algoritmo que analisa a proximidade entre as grelhas para agrupar "manchas" de problemas de forma coesa, garantindo que o gráfico reflita a realidade do mapa.
-   **Servidor Web e API (`app.py`):**
    -   Serve a aplicação completa na rota principal (`/`).
    -   Fornece os dados para os KPIs, mapa e gráfico através dos endpoints `/api/kpis`, `/api/map_data`, e `/api/critical_points`.
    -   Gera relatórios `.xlsx` detalhados e formatados através do endpoint `/api/export`.

---

## Frontend

### Estrutura e Funcionalidades

-   **`templates/index.html`**: Estrutura principal da aplicação, agora com referências a recursos locais (offline).
-   **`static/`**: Contém todos os recursos necessários para o funcionamento offline:
    -   `css/`: Ficheiros de estilo, incluindo `leaflet.css`.
    -   `js/`: Scripts, incluindo `leaflet.js` e `chart.js`.
    -   `tiles/`: "Azulejos" do mapa de satélite pré-descarregados para a área do terminal, garantindo o funcionamento do mapa sem acesso à internet.

---

## Instalação e Execução

### 1. Preparação do Ambiente (Offline)

Para instalar as dependências num ambiente sem acesso à internet, foi criada uma pasta `offline-pack` com todos os pacotes necessários.

1.  Transfira a pasta `offline-pack` para o servidor.
2.  Navegue no terminal até à pasta `backend/` e execute:
    ```bash
    pip install --no-index --find-links=../offline-pack -r requirements.txt
    ```

Se o ambiente tiver acesso à internet, pode simplesmente executar:
```bash
pip install -r requirements.txt
````

### 2\. Execução do Servidor

1.  Navegue até à pasta `backend/` no seu terminal.
2.  Inicie o servidor Flask com o comando:
    ```bash
    python app.py
    ```
3.  Abra um navegador web e aceda ao endereço do servidor, por exemplo: `http://127.0.0.1:5000`.

-----

## Funcionalidades Implementadas

  * **KPIs de Alto Nível**: Cartões de resumo com métricas chave como Total de Medições, % de Pontos Críticos, Nº de Desconexões e o Tablet com mais problemas.
  * **Mapa Interativo Offline**: Utiliza tiles de mapa locais, garantindo o funcionamento sem internet. A interação (zoom/arraste) está bloqueada para focar na visualização de dados.
  * **Controlos de Camada Sincronizados**: Permite ligar/desligar as camadas de pontos (Bom, Atenção, Crítico), com a alteração a refletir-se instantaneamente tanto no mapa como no gráfico.
  * **Filtros Avançados e Combinados**:
      * Filtro por área de cobertura (Pátio/TMUT).
      * Filtro por intervalo de datas.
      * Filtro por tipo de conexão (Todas, Rede Principal, Desconectados, Outras).
      * Pesquisa por ID de dispositivo específico.
  * **Gráfico Inteligente e Sincronizado**: O gráfico "Top 10" agrupa áreas de problema vizinhas para refletir as "manchas" vistas no mapa, e é atualizado com base nos controlos de camada.
  * **Exportação de Dados Robusta**: Gera um relatório `.xlsx` que respeita **todos** os filtros ativos na tela, com abas separadas por dia e dados enriquecidos (coluna de Área, Data/Hora separadas, cabeçalhos em português).
  * **UX (Experiência do Utilizador) Refinada**:
      * Atualização automática dos dados a cada 60 segundos.
      * Indicador de carregamento (spinner) durante a busca de dados.
      * Funcionalidade de copiar IDs com um clique (nos KPIs e nos popups do mapa) que funciona em ambientes HTTP.
      * Notificações de erro na tela, evitando redirecionamentos.