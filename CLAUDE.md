# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Objective

**FUNDEB Insights** is an analytical platform that consolidates Brazilian public education data (FUNDEB transfers, IDEB performance, IBGE demographics) into a modern, interactive web interface. The goal is to answer three core analytical questions:

1. How are FUNDEB transfers distributed across municipalities, states, and regions?
2. Is there a relationship between per-student investment and educational outcomes?
3. Which municipalities or regions show greater relative efficiency in resource use?

Target audiences: public managers, GovTech/B2G consultancies, BI analysts, and public policy teams.

## Stack

| Layer | Tool | Purpose |
|---|---|---|
| ETL | Python, pandas, requests | Data collection, cleaning, transformation |
| Database | PostgreSQL 16+ | Analytical storage layer |
| API | FastAPI | Exposes metrics and queries to the frontend |
| Frontend | HTML, CSS, JavaScript | Web interface |
| Visualization | Plotly.js | Interactive charts |
| Exploration | Jupyter Notebooks | Preliminary analysis |

## Repository Structure

```
fundeb-insights/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entrypoint
│   │   ├── api/             # Route handlers
│   │   ├── services/        # Business logic and aggregations
│   │   ├── models/          # Data models
│   │   ├── schemas/         # Pydantic input/output schemas
│   │   ├── db/              # DB connection and session
│   │   └── utils/           # Config and helpers
│   ├── etl/                 # Extract, clean, merge scripts
│   ├── sql/
│   │   ├── schema/          # Table and view definitions
│   │   ├── queries/         # Analytical queries
│   │   └── etl/             # Load scripts
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html           # Main page (Visão Executiva)
│   ├── pages/               # distribuicao, desempenho, eficiencia, municipio, sobre
│   ├── assets/
│   │   ├── css/             # main.css, dashboard.css
│   │   └── js/              # app.js, api.js, charts.js, filters.js
│   └── components/          # Reusable UI blocks
├── data/
│   ├── raw/                 # Original downloaded files (not versioned)
│   ├── processed/           # Cleaned, merged datasets
│   └── models/
├── docs/                    # ARCHITECTURE.md, DATA_DICTIONARY.md, SOURCES.md, ROADMAP.md
├── notebooks/               # Jupyter exploratory analysis
└── tests/
```

## Data Sources

- **FNDE** — FUNDEB transfers per municipality (CSV/XLSX)
- **INEP** — IDEB, SAEB, Censo Escolar (CSV)
- **SIOPE** — Education budget execution (CSV)
- **IBGE** — Municipal demographics (CSV / API)
- **Tesouro Nacional** — FINBRA municipal finances (CSV)

## Architecture Flow

```
Public Sources → ETL (Python) → PostgreSQL (fact tables, dimensions, views) → FastAPI → Frontend
```

The DB layer uses a star-schema approach: fact tables for transfers and performance, dimension tables for municipalities/years, and pre-built analytical views for common aggregations.

## Platform Pages

1. **Visão Executiva** (`index.html`) — KPIs, national map, rankings
2. **Distribuição de Recursos** — Geographic/temporal FUNDEB breakdown
3. **Investimento vs Desempenho** — Correlation analysis, outliers
4. **Eficiência Educacional** — Relative efficiency comparisons
5. **Exploração Municipal** — Per-municipality profile with history
6. **Sobre o Projeto** — Context, sources, methodology

## Coding Preferences

- Python: PEP 8, type hints on all function signatures, Pydantic schemas for API I/O
- Frontend: vanilla JS only — no React/Vue; keep dependencies minimal
- Visual quality is a priority: smooth transitions, premium typography, dark/light mode
- Mobile-first responsive design
- ETL scripts are standalone and idempotent — safe to re-run
- SQL: use views for reusable aggregations, avoid raw queries in application code

## Development Commands

```bash
# Setup (run from project root)
.venv/Scripts/python -m pip install -r backend/requirements.txt   # Windows
cp backend/.env.example backend/.env

# Run API (from backend/)
cd backend
..\.venv\Scripts\uvicorn app.main:app --reload --port 8001
# API: http://127.0.0.1:8001  |  Docs: http://127.0.0.1:8001/docs

# Run ETL pipeline (from project root, in order)
.venv/Scripts/python backend/etl/extract_ibge.py       # popula data/raw/ibge_populacao.csv
.venv/Scripts/python backend/etl/extract_fundeb.py     # popula data/raw/ e data/processed/
.venv/Scripts/python backend/etl/clean_ideb.py         # trata data/raw/ideb_*.xlsx
.venv/Scripts/python backend/etl/merge_datasets.py     # gera data/processed/base_municipal_mvp.csv

# Tests
cd backend && ../.venv/Scripts/pytest ../tests/

# Frontend — abrir com Live Server (VS Code) na porta 5500
```

## Current Roadmap

- **Phase 1 — Data Foundation:** map sources, extract FUNDEB/IDEB/IBGE, build data dictionary
- **Phase 2 — Backend:** ETL in Python, PostgreSQL schema, FastAPI endpoints
- **Phase 3 — Frontend:** HTML/CSS/JS layout, charts, filters, responsiveness
- **Phase 4 — Publish:** deploy, finalize docs, LinkedIn/GitHub case study
