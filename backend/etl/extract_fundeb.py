"""
Extract FUNDEB revenue data from FNDE (CSV format).
Source: https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas/financiamento/fundeb/2026-1/publicacoes-2026
Output: data/raw/fundeb_receita_<year>.csv
        data/processed/fundeb_municipios_<year>.csv

Granularity: one row per municipality (5,569 records for 2026).
Join key: cod_municipio (7-digit IBGE code) — compatible with IDEB and IBGE population data.
"""

import re
import requests
import pandas as pd
import urllib3
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RAW_DIR = Path(__file__).parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).parents[2] / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Direct CSV download URLs per year (FNDE publicacoes page)
FUNDEB_CSV_URLS: dict[int, str] = {
    2026: (
        "https://www.gov.br/fnde/pt-br/acesso-a-informacao/acoes-e-programas"
        "/financiamento/fundeb/2026-1/publicacoes-2026"
        "/1-receita-total-do-fundeb-por-ente-federado-iii.csv"
    ),
}

COLUMN_MAP = {
    "UF": "uf",
    "Código\nIBGE": "cod_municipio",
    "Entidade": "nome_municipio",
    "Receita da contribuição de estados e municípios ao Fundeb": "receita_contribuicao",
    "Complementação VAAF": "comp_vaaf",
    "Complementação VAAT": "comp_vaat",
    "Complementação VAAR": "comp_vaar",
    "Complementação da União Total": "comp_uniao_total",
    "Total das receitas previstas": "total_receitas",
}

FINANCIAL_COLS = [
    "receita_contribuicao",
    "comp_vaaf",
    "comp_vaat",
    "comp_vaar",
    "comp_uniao_total",
    "total_receitas",
]


def _parse_brl(value: str) -> float:
    """Convert Brazilian currency string to float. '-' or empty → 0.0."""
    if pd.isna(value):
        return 0.0
    cleaned = str(value).strip()
    if cleaned in ("-", "", "–"):
        return 0.0
    cleaned = re.sub(r"[^\d,]", "", cleaned).replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns regardless of encoding artifacts."""
    rename = {}
    for col in df.columns:
        normalized = col.encode("latin-1", errors="replace").decode("latin-1")
        for original, target in COLUMN_MAP.items():
            if original.encode("latin-1", errors="replace").decode("latin-1") in normalized or target in normalized.lower():
                rename[col] = target
                break
    return df.rename(columns=rename)


def extract(year: int) -> pd.DataFrame:
    """Download raw CSV from FNDE and save to data/raw/."""
    url = FUNDEB_CSV_URLS[year]
    response = requests.get(url, timeout=60, verify=False)
    response.raise_for_status()

    raw_path = RAW_DIR / f"fundeb_receita_{year}.csv"
    raw_path.write_bytes(response.content)
    print(f"[fundeb] raw -> {raw_path} ({len(response.content)/1024:.1f} KB)")
    return raw_path


def transform(raw_path: Path, year: int) -> pd.DataFrame:
    """Clean and normalize the raw CSV. Returns municipality-level DataFrame."""
    df = pd.read_csv(raw_path, sep=";", encoding="latin-1", skiprows=9)
    df = df.dropna(axis=1, how="all")

    # Rename columns
    df = _normalize_columns(df)

    # Keep only expected columns
    expected = list(COLUMN_MAP.values())
    df = df[[c for c in expected if c in df.columns]]

    # Normalize IBGE code to 7-digit integer string
    df["cod_municipio"] = (
        df["cod_municipio"]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .str.zfill(7)
    )

    # Keep only valid municipalities: 7-digit numeric codes, non-null UF
    df = df[
        (df["cod_municipio"].str.len() == 7)
        & (df["cod_municipio"].str.isnumeric())
        & (df["uf"].notna())
    ].copy()

    # Parse monetary values
    for col in FINANCIAL_COLS:
        if col in df.columns:
            df[col] = df[col].apply(_parse_brl)

    # Normalize text fields
    df["nome_municipio"] = df["nome_municipio"].str.strip().str.title()
    df["uf"] = df["uf"].str.strip().str.upper()

    # Add year column
    df.insert(0, "ano", year)

    df = df.reset_index(drop=True)
    return df


def load(df: pd.DataFrame, year: int) -> Path:
    """Save processed DataFrame to data/processed/."""
    out_path = PROCESSED_DIR / f"fundeb_municipios_{year}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[fundeb] processed -> {out_path} ({len(df)} municipios)")
    return out_path


def run(year: int) -> pd.DataFrame:
    raw_path = extract(year)
    df = transform(raw_path, year)
    load(df, year)
    return df


if __name__ == "__main__":
    for year in FUNDEB_CSV_URLS:
        df = run(year)
        print(df[["ano", "uf", "cod_municipio", "nome_municipio", "total_receitas"]].head(5).to_string())
