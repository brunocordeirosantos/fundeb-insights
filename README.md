# FUNDEB Insights

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![Deploy](https://img.shields.io/badge/Deploy-GitHub%20Pages-222?logo=github)](https://brunocordeirosantos.github.io/fundeb-insights/)
[![License: MIT](https://img.shields.io/badge/Licença-MIT-green.svg)](LICENSE)

> Plataforma analítica que transforma dados públicos da educação brasileira em inteligência acionável — conectando repasses do FUNDEB, desempenho escolar e indicadores municipais em uma experiência web interativa e visualmente premium.

**[Acesse a plataforma ao vivo →](https://brunocordeirosantos.github.io/fundeb-insights/)**

---

## Visão do Projeto

O FUNDEB movimenta bilhões de reais e é uma das principais fontes de financiamento da educação básica no Brasil. Apesar da ampla disponibilidade de dados públicos, essas informações estão dispersas em diferentes bases governamentais, o que dificulta análises comparativas e diagnósticos estratégicos.

O **FUNDEB Insights** consolida essas bases em uma plataforma analítica moderna, permitindo explorar:

- Como os recursos estão distribuídos entre municípios, estados e regiões
- Se maior investimento por aluno está associado a melhor desempenho educacional
- Quais municípios demonstram maior eficiência relativa no uso dos recursos
- Quais padrões e outliers podem ser identificados a partir dos dados públicos

---

## Páginas

| Página | Status | Descrição |
|---|---|---|
| [Visão Executiva](https://brunocordeirosantos.github.io/fundeb-insights/) | ✅ | KPIs nacionais, ranking estadual, scatter FUNDEB × IDEB, rankings Top/Bottom 10 |
| [Análise Estadual](https://brunocordeirosantos.github.io/fundeb-insights/pages/estados.html) | ✅ | Comparativo estadual vs. municipal por aluno, tabela interativa, painel de detalhes |
| [Exploração Municipal](https://brunocordeirosantos.github.io/fundeb-insights/pages/municipio.html) | ✅ | Busca com autocomplete, ficha financeira completa e comparações regionais |
| Distribuição de Recursos | 🚧 | Quebra geográfica e temporal dos repasses |
| Eficiência Educacional | 🚧 | Comparação de eficiência relativa entre municípios |

---

## Stack Tecnológica

| Camada | Tecnologia | Uso |
|---|---|---|
| Extração e ETL | Python, pandas, requests | Coleta, limpeza e transformação dos dados |
| API | FastAPI, Pydantic | Exposição dos dados ao frontend |
| Frontend | HTML, CSS, JavaScript | Interface da aplicação |
| Visualização | Plotly.js | Gráficos interativos |
| Deploy | GitHub Pages + Render | Frontend estático + API em nuvem |
| CI/CD | GitHub Actions | Deploy automático a cada push na `main` |

---

## Fontes de Dados

| Fonte | Dados | Ano |
|---|---|---|
| FNDE | Receita total prevista do FUNDEB por ente federado | 2026 |
| INEP | IDEB por município (Anos Iniciais e Finais) | 2023 |
| INEP | Censo Escolar — matrículas por rede e etapa | 2023 |
| IBGE | Estimativas populacionais municipais | 2021 |

---

## Arquitetura

```
Fontes públicas → ETL Python → CSVs processados → API FastAPI → Frontend HTML/JS
```

```
fundeb-insights/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entrypoint FastAPI
│   │   ├── api/                 # Endpoints por domínio
│   │   ├── services/            # Lógica de negócio e agregações
│   │   ├── schemas/             # Modelos Pydantic
│   │   └── utils/config.py      # Configurações
│   ├── etl/
│   │   ├── extract_fundeb.py    # Extração FNDE
│   │   ├── extract_ideb.py      # Extração INEP
│   │   ├── extract_ibge.py      # Extração IBGE
│   │   ├── clean_ideb.py        # Limpeza IDEB
│   │   └── merge_datasets.py    # Junção das bases
│   ├── sql/schema/              # Modelagem PostgreSQL (próxima fase)
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Visão Executiva
│   ├── pages/                   # estados, municipio, distribuicao, eficiencia, sobre
│   └── assets/css/ e js/        # Estilos e scripts
├── data/
│   └── processed/               # Bases analíticas finais (CSV)
├── docs/
│   ├── DATA_DICTIONARY.md       # Dicionário de dados
│   └── SOURCES.md               # Fontes e URLs
└── render.yaml                  # Configuração de deploy do backend
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

### Municípios

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Status da API |
| GET | `/api/resumo` | KPIs gerais do dataset |
| GET | `/api/filtros` | Opções disponíveis para filtros |
| GET | `/api/municipios` | Lista paginada com filtros `?uf=` e `?nome=` |
| GET | `/api/municipios/{cod}` | Ficha completa de um município |
| GET | `/api/uf/{uf}` | Médias de per capita e IDEB por estado |
| GET | `/api/ranking` | Ranking por FUNDEB por aluno (`?uf=`, `?limite=`, `?ordem=`) |
| GET | `/api/correlacao` | Dados para scatter FUNDEB × IDEB (`?uf=`, `?per_capita_max=`) |
| GET | `/api/eficiencia` | Dados de eficiência relativa (`?uf=`, `?etapa=`) |

### Estados

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/estados` | Lista todos os estados (`?regiao=`) |
| GET | `/api/estados/resumo` | KPIs nacionais consolidados por estado |
| GET | `/api/estados/ranking` | Ranking estadual (`?regiao=`, `?metrica=`, `?ordem=`) |
| GET | `/api/estados/comparativo` | Comparativo estadual vs. municipal por aluno |
| GET | `/api/estados/{uf}` | Ficha completa de um estado |

---

## Regenerando a Base Analítica

As bases em `data/processed/` estão incluídas no repositório. Para regenerá-las a partir das fontes originais:

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
- **R$ 370,3 bilhões** em receitas previstas para 2026
- **97% de cobertura** com as três fontes combinadas
- **Correlação negativa (r = −0,30)** entre FUNDEB por aluno e IDEB — reflexo do mecanismo redistributivo do fundo
- Município com maior investimento por aluno: **São Julião/PI** — R$ 37.706/aluno
- Município com menor investimento por aluno: **Nazaré/BA** — R$ 3.438/aluno
- Razão entre extremos: **11x** (por aluno na rede municipal)
- Mediana nacional — rede municipal: **R$ 10.127/aluno**
- IDEB médio nacional (rede pública): **5,82** Anos Iniciais · **4,77** Anos Finais

---

## Roadmap

- [x] ETL das quatro fontes principais (FNDE, INEP IDEB, INEP Censo Escolar, IBGE)
- [x] Base analítica municipal consolidada (5.596 municípios)
- [x] Base analítica estadual consolidada (27 estados)
- [x] API REST com 13 endpoints
- [x] Visão Executiva com KPIs, ranking estadual e scatter interativo
- [x] Análise Estadual com comparativo estadual vs. municipal por aluno
- [x] Exploração Municipal com autocomplete e ficha completa
- [x] Deploy backend (Render) + frontend (GitHub Pages)
- [x] CI/CD com GitHub Actions
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
