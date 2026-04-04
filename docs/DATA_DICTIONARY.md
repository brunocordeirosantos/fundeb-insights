# Data Dictionary

> Document each field as it is mapped during Phase 1 exploration.

## dim_municipio

| Campo | Tipo | Fonte | Descrição |
|---|---|---|---|
| cod_municipio | CHAR(7) | IBGE | Código IBGE do município (7 dígitos) |
| nome | VARCHAR | IBGE | Nome do município |
| uf | CHAR(2) | IBGE | Sigla do estado |
| regiao | VARCHAR | IBGE | Norte, Nordeste, Centro-Oeste, Sudeste, Sul |
| populacao | INTEGER | IBGE | Estimativa populacional |

## fato_fundeb

Fonte: FNDE — "Receita total prevista do Fundeb por ente federado" (CSV)
URL base: https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/publicacoes-2026
Arquivo processado: `data/processed/fundeb_municipios_<ano>.csv`

| Campo | Tipo | Fonte | Descrição |
|---|---|---|---|
| ano | SMALLINT | FNDE | Ano de referência |
| uf | CHAR(2) | FNDE | Sigla do estado |
| cod_municipio | CHAR(7) | FNDE | Código IBGE 7 dígitos — chave de junção |
| nome_municipio | VARCHAR | FNDE | Nome do município (title case) |
| receita_contribuicao | NUMERIC | FNDE | Contribuição de estados e municípios ao FUNDEB (R$) |
| comp_vaaf | NUMERIC | FNDE | Complementação VAAF — equidade entre estados (R$) |
| comp_vaat | NUMERIC | FNDE | Complementação VAAT — resultado educacional (R$) |
| comp_vaar | NUMERIC | FNDE | Complementação VAAR — escolas rurais (R$) |
| comp_uniao_total | NUMERIC | FNDE | Soma das três complementações da União (R$) |
| total_receitas | NUMERIC | FNDE | **Métrica principal do MVP** — total previsto (R$) |

**Notas de limpeza:**
- Valores originais em formato BRL (`18.502.193,40`) → convertidos para float
- `-` nos campos de complementação → convertido para `0.0`
- Encoding original: `latin-1` → processado como `utf-8`
- Linhas de rodapé (total geral) filtradas pelo critério: `cod_municipio` numérico de 7 dígitos + `uf` não nulo

## fato_ideb

| Campo | Tipo | Fonte | Descrição |
|---|---|---|---|
| cod_municipio | CHAR(7) | INEP | Chave para dim_municipio |
| ano | SMALLINT | INEP | Ano da avaliação (ciclos: 2019, 2021, 2023) |
| etapa | VARCHAR | INEP | `anos_iniciais` ou `anos_finais` |
| nota_ideb | NUMERIC | INEP | Nota IDEB (0–10) |

## base_municipal_mvp

Arquivo final de análise do MVP. Gerado por `backend/etl/merge_datasets.py`.
Caminho: `data/processed/base_municipal_mvp.csv`

### Regras de junção

| Join | Tipo | Chave | Fonte esquerda | Fonte direita |
|---|---|---|---|---|
| FUNDEB ← IBGE | LEFT | `cod_municipio` | `fundeb_municipios_2026.csv` | `ibge_populacao.csv` |
| base ← IDEB | LEFT | `cod_municipio` | resultado anterior | `ideb_municipios_2023.csv` |

LEFT JOIN a partir do FUNDEB garante que todos os 5.596 entes permaneçam na base, mesmo sem match nas demais fontes.

### Colunas finais

| Coluna | Tipo | Cobertura | Descrição |
|---|---|---|---|
| `ano` | int | 100% | Ano de referência FUNDEB (2026) |
| `uf` | str | 100% | Sigla do estado |
| `cod_municipio` | str(7) | 100% | Código IBGE — chave primária da base |
| `nome_municipio` | str | 100% | Nome do município (title case) |
| `receita_contribuicao` | float | 100% | Contribuição de estados e municípios ao FUNDEB (R$) |
| `comp_vaaf` | float | 100% | Complementação VAAF — equidade entre estados (R$) |
| `comp_vaat` | float | 100% | Complementação VAAT — resultado educacional (R$) |
| `comp_vaar` | float | 100% | Complementação VAAR — escolas rurais (R$) |
| `comp_uniao_total` | float | 100% | Soma das complementações da União (R$) |
| `total_receitas` | float | 100% | Receita FUNDEB total prevista (R$) |
| `populacao` | float | 99,5% | Estimativa populacional IBGE 2021 |
| `total_receitas_per_capita` | float | 99,5% | total_receitas / populacao (R$/hab) |
| `ideb_anos_iniciais_2023` | float | 97,0% | Nota IDEB rede pública — Anos Iniciais |
| `ideb_anos_finais_2023` | float | 96,1% | Nota IDEB rede pública — Anos Finais |

### Nulos esperados
- 28 municípios sem `populacao`: emancipados após censo IBGE 2021
- 168 municípios sem `ideb_anos_iniciais_2023`: sem rede pública avaliada pelo INEP
- 216 municípios sem `ideb_anos_finais_2023`: idem para ensino fundamental II

## Key join notes

- FNDE uses 6-digit municipality codes; pad with leading zero to match IBGE 7-digit standard.
- INEP IDEB files use `CO_MUNICIPIO` (7 digits) — compatible with IBGE directly.
- IBGE population API returns 7-digit codes.
