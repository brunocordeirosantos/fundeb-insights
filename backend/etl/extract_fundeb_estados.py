"""
Extract state-level FUNDEB data from the same FNDE raw file used for municipalities.
Source: data/raw/fundeb_receita_<year>.csv (already downloaded by extract_fundeb.py)

State entries in the FNDE file are identified by:
  - Entidade == 'GOVERNO DO ESTADO'
  - Código IBGE == 2-digit state code (e.g. 12 for Acre, 35 for São Paulo)

Output: data/processed/fundeb_estados_<year>.csv

Columns:
    ano                 — reference year
    cod_ibge_estado     — 2-digit IBGE state code
    uf                  — state abbreviation (AC, SP, ...)
    nome_estado         — full state name
    regiao              — macro-region (Norte, Nordeste, ...)
    receita_contribuicao
    comp_vaaf
    comp_vaat
    comp_vaar
    comp_uniao_total
    total_receitas      — FUNDEB received by the state government for rede estadual

NOTE: total_receitas here is the state government's share of FUNDEB, which finances
state-managed schools (rede estadual). It is independent from the municipal share.
"""

import re
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).parents[2] / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# IBGE 2-digit code → (UF abbreviation, full state name, macro-region)
ESTADOS: dict[str, tuple[str, str, str]] = {
    "11": ("RO", "Rondônia",             "Norte"),
    "12": ("AC", "Acre",                 "Norte"),
    "13": ("AM", "Amazonas",             "Norte"),
    "14": ("RR", "Roraima",              "Norte"),
    "15": ("PA", "Pará",                 "Norte"),
    "16": ("AP", "Amapá",               "Norte"),
    "17": ("TO", "Tocantins",            "Norte"),
    "21": ("MA", "Maranhão",             "Nordeste"),
    "22": ("PI", "Piauí",               "Nordeste"),
    "23": ("CE", "Ceará",               "Nordeste"),
    "24": ("RN", "Rio Grande do Norte",  "Nordeste"),
    "25": ("PB", "Paraíba",             "Nordeste"),
    "26": ("PE", "Pernambuco",           "Nordeste"),
    "27": ("AL", "Alagoas",             "Nordeste"),
    "28": ("SE", "Sergipe",             "Nordeste"),
    "29": ("BA", "Bahia",               "Nordeste"),
    "31": ("MG", "Minas Gerais",         "Sudeste"),
    "32": ("ES", "Espírito Santo",      "Sudeste"),
    "33": ("RJ", "Rio de Janeiro",       "Sudeste"),
    "35": ("SP", "São Paulo",           "Sudeste"),
    "41": ("PR", "Paraná",              "Sul"),
    "42": ("SC", "Santa Catarina",       "Sul"),
    "43": ("RS", "Rio Grande do Sul",    "Sul"),
    "50": ("MS", "Mato Grosso do Sul",   "Centro-Oeste"),
    "51": ("MT", "Mato Grosso",          "Centro-Oeste"),
    "52": ("GO", "Goiás",              "Centro-Oeste"),
    "53": ("DF", "Distrito Federal",     "Centro-Oeste"),
}

FINANCIAL_COLS_RAW = [
    "Receita da contribuição de estados e municípios ao Fundeb",
    "Complementação VAAF",
    "Complementação VAAT",
    "Complementação VAAR",
    "Complementação da União Total",
    "Total das receitas previstas",
]

FINANCIAL_COLS_OUT = [
    "receita_contribuicao",
    "comp_vaaf",
    "comp_vaat",
    "comp_vaar",
    "comp_uniao_total",
    "total_receitas",
]


def _parse_brl(value: str) -> float:
    if pd.isna(value):
        return 0.0
    cleaned = str(value).strip()
    if cleaned in ("-", "", "–", "-   ", " -   "):
        return 0.0
    cleaned = re.sub(r"[^\d,]", "", cleaned).replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def run(year: int = 2026) -> pd.DataFrame:
    raw_path = RAW_DIR / f"fundeb_receita_{year}.csv"
    if not raw_path.exists():
        raise FileNotFoundError(
            f"{raw_path} não encontrado. Execute extract_fundeb.py primeiro."
        )

    df_raw = pd.read_csv(raw_path, sep=";", encoding="latin1", skiprows=9)
    df_raw = df_raw.dropna(axis=1, how="all")

    ent_col = df_raw.columns[2]
    mask = df_raw[ent_col].astype(str).str.upper().str.contains("GOVERNO DO ESTADO", na=False)
    estados_df = df_raw[mask].copy()

    print(f"[fundeb_estados] linhas encontradas: {len(estados_df)}")

    # Normalize IBGE code
    cod_col = df_raw.columns[1]
    estados_df["cod_ibge_estado"] = (
        estados_df[cod_col]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .str.zfill(2)
    )

    # Map to UF, nome, regiao
    estados_df["uf"] = estados_df["cod_ibge_estado"].map(
        lambda c: ESTADOS.get(c, ("", "", ""))[0]
    )
    estados_df["nome_estado"] = estados_df["cod_ibge_estado"].map(
        lambda c: ESTADOS.get(c, ("", "", ""))[1]
    )
    estados_df["regiao"] = estados_df["cod_ibge_estado"].map(
        lambda c: ESTADOS.get(c, ("", "", ""))[2]
    )

    # Parse financial columns
    for raw_col, out_col in zip(FINANCIAL_COLS_RAW, FINANCIAL_COLS_OUT):
        if raw_col in estados_df.columns:
            estados_df[out_col] = estados_df[raw_col].apply(_parse_brl)
        else:
            estados_df[out_col] = 0.0

    result = estados_df[[
        "cod_ibge_estado", "uf", "nome_estado", "regiao",
        *FINANCIAL_COLS_OUT,
    ]].copy()
    result.insert(0, "ano", year)
    result = result.sort_values("uf").reset_index(drop=True)

    out_path = PROCESSED_DIR / f"fundeb_estados_{year}.csv"
    result.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[fundeb_estados] salvo -> {out_path} ({len(result)} estados)")
    return result


if __name__ == "__main__":
    df = run(2026)
    print()
    print(df[["uf", "nome_estado", "regiao", "total_receitas"]].to_string())
    print(f"\nTotal FUNDEB rede estadual (Brasil): R$ {df['total_receitas'].sum():,.2f}")
