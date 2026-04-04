"""
Clean and normalize IDEB municipal data.
Input:  data/raw/ideb_<etapa>_municipios_<year>.xlsx
Output: data/processed/ideb_municipios_<year>.csv

Strategy:
- Keep only REDE == 'Pública' (aggregates all public networks per municipality)
- Extract only the most recent observed score (VL_OBSERVADO_<year>)
- Pivot anos_iniciais and anos_finais into a single row per municipality
- Output join key: cod_municipio (7-digit string, matches FUNDEB and IBGE)
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).parents[2] / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

ETAPAS = ["anos_iniciais", "anos_finais"]


def clean_etapa(year: int, etapa: str) -> pd.DataFrame:
    path = RAW_DIR / f"ideb_{etapa}_municipios_{year}.xlsx"
    df = pd.read_excel(path, skiprows=9, dtype={"CO_MUNICIPIO": str})

    # Keep only valid municipality rows
    df = df[df["CO_MUNICIPIO"].notna() & df["CO_MUNICIPIO"].str.isnumeric()].copy()

    # Keep only public network aggregate
    df = df[df["REDE"] == "Pública"].copy()

    # Select and rename key columns
    score_col = f"VL_OBSERVADO_{year}"
    df = df[["CO_MUNICIPIO", "SG_UF", "NO_MUNICIPIO", score_col]].copy()
    df.columns = ["cod_municipio", "uf", "nome_municipio", f"ideb_{etapa}_{year}"]

    df["cod_municipio"] = df["cod_municipio"].str.strip().str.zfill(7)
    df["nome_municipio"] = df["nome_municipio"].str.strip().str.title()
    df["uf"] = df["uf"].str.strip().str.upper()

    # Convert score to numeric (some values may be '-' or '*')
    score = f"ideb_{etapa}_{year}"
    df[score] = pd.to_numeric(df[score], errors="coerce")

    return df.reset_index(drop=True)


def run(year: int) -> pd.DataFrame:
    dfs = [clean_etapa(year, etapa) for etapa in ETAPAS]

    # Merge the two etapas on cod_municipio
    merged = dfs[0].merge(
        dfs[1][["cod_municipio", f"ideb_anos_finais_{year}"]],
        on="cod_municipio",
        how="outer",
    )
    merged.insert(0, "ano_ideb", year)

    out_path = PROCESSED_DIR / f"ideb_municipios_{year}.csv"
    merged.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[ideb] processed -> {out_path} ({len(merged)} municipios)")
    return merged


if __name__ == "__main__":
    df = run(2023)
    print(df.head(5).to_string())
