# FUNDEB Insights

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/Licença-MIT-green.svg)](LICENSE)

> Plataforma analítica que transforma dados públicos da educação brasileira em inteligência acionável — conectando repasses do FUNDEB, desempenho escolar e indicadores municipais em uma experiência web interativa e visualmente premium.

---

## Visão do Projeto

O FUNDEB movimenta bilhões de reais e é uma das principais fontes de financiamento da educação básica no Brasil. Apesar da ampla disponibilidade de dados públicos, essas informações estão dispersas em diferentes bases governamentais, o que dificulta análises comparativas e diagnósticos estratégicos.

O **FUNDEB Insights** consolida essas bases em uma plataforma analítica moderna, permitindo explorar:

- Como os recursos estão distribuídos entre municípios, estados e regiões
- Se maior investimento está associado a melhor desempenho educacional
- Quais municípios demonstram maior eficiência relativa no uso dos recursos
- Quais padrões e outliers podem ser identificados a partir dos dados públicos

---

## Demonstração

| Página | Descrição |
|---|---|
| **Visão Executiva** | KPIs nacionais, scatter de correlação FUNDEB × IDEB, rankings top/bottom |
| **Exploração Municipal** | Busca por município com autocomplete, ficha financeira completa e comparações |
| **Distribuição** | *(em desenvolvimento)* |
| **Eficiência** | *(em desenvolvimento)* |

---

## Stack Tecnológica

| Camada | Tecnologia | Uso |
|---|---|---|
| Extração e ETL | Python, pandas, requests | Coleta, limpeza e transformação dos dados |
| API | FastAPI, Pydantic | Exposição dos dados ao frontend |
| Frontend | HTML, CSS, JavaScript | Interface da aplicação |
| Visualização | Plotly.js | Gráficos interativos |
| Versionamento | Git + GitHub | Gestão do projeto |

---

## Fontes de Dados

| Fonte | Dados | Ano |
|---|---|---|
| FNDE | Receita total prevista do FUNDEB por ente federado | 2026 |
| INEP | IDEB por município (Anos Iniciais e Finais) | 2023 |
| IBGE | Estimativas populacionais municipais | 2021 |

---

## Arquitetura

```
Fontes públicas → ETL Python → base_municipal_mvp.csv → API FastAPI → Frontend HTML/JS
```

```
fundeb-insights/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entrypoint FastAPI
│   │   ├── api/municipios.py    # Endpoints
│   │   ├── services/            # Lógica de negócio
│   │   ├── schemas/             # Modelos Pydantic
│   │   └── utils/config.py      # Configurações
│   ├── etl/
│   │   ├── extract_fundeb.py    # Extração FNDE
│   │   ├── extract_ideb.py      # Extração INEP
│   │   ├── extract_ibge.py      # Extração IBGE
│   │   ├── clean_ideb.py        # Limpeza IDEB
│   │   └── merge_datasets.py    # Junção das bases
│   ├── sql/schema/              # Modelagem PostgreSQL
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Visão Executiva
│   ├── pages/                   # Demais páginas
│   └── assets/css/ e js/        # Estilos e scripts
├── data/
│   └── processed/               # Base analítica final
├── docs/
│   ├── DATA_DICTIONARY.md       # Dicionário de dados
│   └── SOURCES.md               # Fontes e URLs
└── render.yaml                  # Configuração de deploy
```

---

## Como Rodar Localmente

### Pré-requisitos

- Python 3.11+
- pip

### Instalação

```bash
# Clone o repositório
git clone https://github.com/brunocordeirosantos/fundeb-insights.git
cd fundeb-insights

# Crie o ambiente virtual
python -m venv .venv

# Instale as dependências
.venv\Scripts\python -m pip install -r backend\requirements.txt
```

### Rodando o backend

```bash
cd backend
..\.venv\Scripts\uvicorn app.main:app --reload --port 8001
```

API disponível em: `http://localhost:8001`
Documentação interativa: `http://localhost:8001/docs`

### Rodando o frontend

Abra `frontend/index.html` com o Live Server do VS Code ou execute:

```bash
python -m http.server 5500 --directory frontend
```

Acesse: `http://localhost:5500`

---

## Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Status da API |
| GET | `/api/resumo` | KPIs gerais do dataset |
| GET | `/api/filtros` | Opções disponíveis para filtros |
| GET | `/api/municipios` | Lista paginada com filtros `?uf=` e `?nome=` |
| GET | `/api/municipios/{cod}` | Ficha completa de um município |
| GET | `/api/uf/{uf}` | Médias de per capita e IDEB por estado |
| GET | `/api/ranking` | Ranking por receita FUNDEB per capita |
| GET | `/api/correlacao` | Dados para scatter FUNDEB × IDEB |

---

## Regenerando a Base Analítica

A base `data/processed/base_municipal_mvp.csv` está incluída no repositório. Para regenerá-la a partir das fontes originais:

```bash
# 1. Extração
.venv\Scripts\python backend\etl\extract_ibge.py
.venv\Scripts\python backend\etl\extract_fundeb.py
.venv\Scripts\python backend\etl\extract_ideb.py

# 2. Tratamento
.venv\Scripts\python backend\etl\clean_ideb.py

# 3. Junção
.venv\Scripts\python backend\etl\merge_datasets.py
```

---

## Principais Resultados

- **5.596 municípios** com dados financeiros FUNDEB 2026
- **R$ 370,3 bilhões** em receitas previstas
- **97% de cobertura** com as três fontes combinadas
- **Correlação negativa (r = −0,30)** entre FUNDEB per capita e IDEB — reflexo do mecanismo redistributivo do fundo
- Município com maior per capita: **Japurá/AM** — R$ 25.201/hab
- Município com menor per capita: **Douradoquara/MG** — R$ 176/hab
- IDEB médio nacional (rede pública): **5,82** Anos Iniciais · **4,77** Anos Finais

---

## Roadmap

- [x] ETL das três fontes principais
- [x] Base analítica municipal consolidada
- [x] API REST com 8 endpoints
- [x] Visão Executiva com KPIs e scatter interativo
- [x] Exploração Municipal com autocomplete e ficha completa
- [x] Deploy backend (Render)
- [ ] GitHub Pages para o frontend
- [ ] Página de Distribuição de Recursos
- [ ] Página de Eficiência Educacional
- [ ] Mapa coroplético nacional
- [ ] Série histórica (2021–2026)
- [ ] Responsividade mobile completa

---

## Autor

**Bruno Cordeiro Santos**
Analista de BI Comercial | Revenue Ops · CRM Analytics
Power BI · SQL · Excel · Python | Dashboards, KPIs, Forecast e Inteligência de Negócio

[![LinkedIn](https://img.shields.io/badge/LinkedIn-brunocordeirosantos-0077B5?logo=linkedin)](https://linkedin.com/in/brunocordeirosantos)

---

## Licença

Este projeto está sob a licença MIT.

> Nota: este projeto utiliza exclusivamente dados públicos disponibilizados por órgãos governamentais brasileiros. Todas as fontes estão documentadas em `docs/SOURCES.md`.
