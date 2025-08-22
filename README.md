# Dashboard de Wi-Fi – APM Terminals

## Objetivo
Este projeto tem como objetivo criar um **dashboard web** para a equipe de TI da **APM Terminals**, projetado para **monitorar e visualizar a qualidade do sinal Wi-Fi** no terminal.  

O sistema processa logs de conectividade de dispositivos Android, identifica áreas problemáticas através de algoritmos de clusterização e apresenta essas informações em **mapas interativos e gráficos analíticos**.

---

## Arquitetura Geral
O sistema segue o padrão **Frontend + Backend** com comunicação via **API REST**:

- **Backend (Python/Flask)**  
  Responsável pela ingestão de dados, processamento, análises e disponibilização via API.
- **Frontend (HTML/CSS/JS)**  
  Aplicação web modular para visualização dos dados no mapa e em gráficos.

---

## Backend

### Estrutura
- **Fonte de dados:** `raw_data.csv` com logs de conectividade.  
- **Banco de dados:** `db/dashboard.db` (SQLite) – tabela `raw_points`.  
- **API:** Servidor Flask em `app.py`.

### Scripts principais
- `process_data.py` → ETL que lê o CSV incrementalmente e salva no banco.  
- `database.py` → Abstração de acesso ao banco.  
- `analysis.py` → Processamento e análise:
  - **Classificação**: Categoriza os pontos (`critical`, `attention`, `good`).  
  - **Clusterização**: Algoritmo DBSCAN para agrupar pontos próximos (≤35m).  
  - **Zonas GeoJSON**: Geração de áreas circulares com raio/opacidade dinâmicos.  
  - **Top 10**: Retorna os locais com mais incidentes (por mapa).  
- `app.py` → API Flask com os endpoints:
  - `GET /api/map_data` → Retorna zonas clusterizadas.  
  - `GET /api/critical_points?map=patio|tmut` → Retorna dados para o gráfico "Top 10".

---

## Frontend

### Estrutura
- **index.html** → Estrutura da aplicação.  
- **css/style.css** → Estilos.  
- **js/**  
  - `api.js` → Comunicação com o backend.  
  - `map-view.js` → Lógica do mapa (Leaflet + Mapbox).  
  - `chart-view.js` → Gráficos com Chart.js.  
  - `main.js` → Orquestrador das interações.

### Bibliotecas usadas
- [Leaflet.js](https://leafletjs.com/) → Renderização do mapa.  
- [Mapbox](https://www.mapbox.com/) → Tiles de satélite de alta resolução.  
- [Chart.js](https://www.chartjs.org/) → Gráficos analíticos.

---

## Funcionalidades já Implementadas

* Visualização de zonas (boas, atenção, críticas) no mapa. ✅ 
* Raio e opacidade dinâmicos para clusters. ✅ 
* Gráfico **Top 10** atualizado conforme o mapa (Pátio/TMUT). ✅ 
* Interatividade: clique no gráfico → foco no mapa. ✅ 
* Mapa de satélite de alta resolução (Mapbox). ✅ 

---

## Roadmap

### Fase 2 – Refatoração & Design (🎯 Atual)

* ✅ Clean Architecture concluída.
* Redesign visual com identidade da APM Terminals.

### Fase 3 – Funcionalidades Dinâmicas

* Filtros por data/hora.
* Exportar dados (CSV/Excel).
* KPIs em cartões de resumo.

### Fase 4 – Funcionalidades Futuras

* Detecção de anomalias (Machine Learning).
* Camada de antenas no mapa.
* Path tracing de dispositivos.
* Relatórios automáticos (PDF) e alertas.

---

## Licença

Projeto interno para APM Terminals. Uso restrito.

---
