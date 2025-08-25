# Dashboard de Wi-Fi – APM Terminals

## Objetivo
Este projeto tem como objetivo criar um **dashboard web** para a equipe de TI da **APM Terminals**, projetado para **monitorar e visualizar a qualidade do sinal Wi-Fi** no terminal.

O sistema processa logs de conectividade de dispositivos Android, identifica áreas problemáticas através de algoritmos de clusterização e apresenta essas informações em **mapas interativos e gráficos analíticos** que se atualizam automaticamente.

---

## Arquitetura Geral
O sistema foi consolidado em uma **aplicação web unificada**, onde o **Backend (Python/Flask)** é responsável por toda a lógica de negócio e também por servir a interface do **Frontend (HTML/CSS/JS)**.

- **Backend (Python/Flask)**
  Responsável pela ingestão de dados, processamento, análises, disponibilização via API REST e por servir a aplicação web para o navegador do usuário.
- **Frontend (HTML/CSS/JS)**
  Interface do usuário dinâmica e reativa, renderizada no navegador, que consome a API do próprio backend para exibir mapas, gráficos e filtros interativos.

---

## Backend

### Estrutura
- **Fonte de dados:** `raw_data.csv` com logs de conectividade, incluindo o SSID da rede (`current_ssid`).
- **Banco de dados:** `db/dashboard.db` (SQLite) – tabela `raw_points`.
- **API e Servidor Web:** Servidor Flask em `app.py`.

### Scripts principais
- `process_data.py` → ETL que lê o CSV incrementalmente, trata a coluna `current_ssid` e salva no banco.
- `database.py` → Abstração de acesso ao banco.
- `analysis.py` → Processamento e análise:
  - **Classificação**: Categoriza os pontos (`critical`, `attention`, `good`).
  - **Clusterização**: Algoritmo DBSCAN para agrupar pontos próximos (≤35m).
  - **Zonas GeoJSON**: Geração de áreas circulares com raio/opacidade dinâmicos.
  - **Top 10**: Retorna os locais com mais incidentes, respeitando os filtros aplicados.
- `app.py` → Servidor Flask com os endpoints:
  - `GET /` → Rota principal que serve a aplicação web (`index.html`).
  - `GET /api/map_data` → Retorna zonas clusterizadas, aceitando filtros de `map`, `date` e `ssid_filter`.
  - `GET /api/critical_points` → Retorna dados para o gráfico "Top 10", aceitando os mesmos filtros.

---

## Frontend

### Estrutura
- **`templates/index.html`** → Estrutura principal da aplicação, servida pelo Flask.
- **`static/css/style.css`** → Estilos visuais, incluindo animações de carregamento.
- **`static/js/`**
  - `api.js` → Comunicação com a API do backend usando URLs relativas.
  - `map-view.js` → Lógica do mapa (Leaflet + Mapbox) e exibição de detalhes (incluindo SSID).
  - `chart-view.js` → Gráficos com Chart.js.
  - `main.js` → Orquestrador das interações, gerenciador de estado dos filtros e responsável pela lógica de atualização automática (polling).

### Bibliotecas usadas
- [Leaflet.js](https://leafletjs.com/) → Renderização do mapa.
- [Mapbox](https://www.mapbox.com/) → Tiles de satélite de alta resolução.
- [Chart.js](https://www.chartjs.org/) → Gráficos analíticos.

---

## Como Executar
1. Navegue até a pasta `backend/` no seu terminal.
2. Inicie o servidor Flask com o comando:
   ```bash
   python app.py
3. Abra um navegador web e acesse o endereço do servidor, por exemplo: http://127.0.0.1:5000.

## Funcionalidades Implementadas

* **Visualização Geográfica**: Zonas de qualidade de sinal (boas, atenção, críticas) no mapa. ✅
* **Filtros Avançados**:
    * Filtro por área de cobertura (Pátio/TMUT). ✅
    * Filtro por intervalo de datas. ✅
    * Filtro dinâmico por tipo de conexão (Rede Principal, Desconectados, Outras Redes). ✅
* **Análise de Desempenho**: Gráfico "Top 10" piores locais que reflete dinamicamente os filtros aplicados. ✅
* **Exportação de Dados**: Gera um relatório `.xlsx` que respeita o filtro de datas, com abas separadas por dia e dados agrupados por rede. ✅
* **Atualização Automática**: O dashboard busca e exibe novos dados a cada 60 segundos, sem necessidade de recarregar a página. ✅
* **UX**:
    * Clique no gráfico foca a área correspondente no mapa. ✅
    * Indicador de carregamento (spinner) durante a busca de dados. ✅
    * Interface visual coesa: o título do gráfico e o filtro ativo compartilham a mesma identidade de cor. ✅
    * Detalhes da medição no popup do mapa, incluindo o SSID da rede. ✅

---

## Roadmap

### Próximos Passos
* Implementar KPIs em cartões de resumo (ex: % de medições críticas no período).

### Funcionalidades Futuras
* Detecção de anomalias (Machine Learning).
* Adicionar camada de visualização de antenas no mapa.
* Path tracing de dispositivos para análise de roaming.
* Relatórios automáticos (PDF) e sistema de alertas.

---

## Licença

Projeto interno para APM Terminals. Uso restrito.
