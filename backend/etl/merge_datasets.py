"""
Merge FUNDEB, IBGE population, and IDEB into a single analytical base.
Output: data/processed/base_municipal_mvp.csv

Join key: cod_municipio (7-digit IBGE code, present in all three sources)
Strategy: left join from FUNDEB (most complete) → IBGE → IDEB
Derived metric: total_receitas_per_capita = total_receitas / populacao
"""

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).parents[2] / "data" / "processed"
RAW_DIR = Path(__file__).parents[2] / "data" / "raw"

FUNDEB_YEAR = 2026
IDEB_YEAR = 2023


def load_fundeb() -> pd.DataFrame:
    path = PROCESSED_DIR / f"fundeb_municipios_{FUNDEB_YEAR}.csv"
    df = pd.read_csv(path, dtype={"cod_municipio": str})
    df["cod_municipio"] = df["cod_municipio"].str.zfill(7)
    return df


def load_ibge() -> pd.DataFrame:
    path = RAW_DIR / "ibge_populacao.csv"
    df = pd.read_csv(path, dtype={"cod_municipio": str})
    df["cod_municipio"] = df["cod_municipio"].str.strip().str.zfill(7)
    df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce")
    return df[["cod_municipio", "populacao"]]


def load_ideb() -> pd.DataFrame:
    path = PROCESSED_DIR / f"ideb_municipios_{IDEB_YEAR}.csv"
    df = pd.read_csv(path, dtype={"cod_municipio": str})
    df["cod_municipio"] = df["cod_municipio"].str.zfill(7)
    return df


def run() -> pd.DataFrame:
    fundeb = load_fundeb()
    ibge = load_ibge()
    ideb = load_ideb()

    print(f"[merge] FUNDEB:  {len(fundeb):,} registros")
    print(f"[merge] IBGE:    {len(ibge):,} registros")
    print(f"[merge] IDEB:    {len(ideb):,} registros")

    # Join FUNDEB ← IBGE
    base = fundeb.merge(ibge, on="cod_municipio", how="left")

    # Join base ← IDEB (drop redundant uf/nome columns from IDEB)
    ideb_cols = ["cod_municipio", f"ideb_anos_iniciais_{IDEB_YEAR}", f"ideb_anos_finais_{IDEB_YEAR}"]
    base = base.merge(ideb[ideb_cols], on="cod_municipio", how="left")

    # Derived metric
    base["total_receitas_per_capita"] = (
        base["total_receitas"] / base["populacao"]
    ).round(2)

    # Report match quality
    sem_ibge = base["populacao"].isna().sum()
    sem_ideb = base[f"ideb_anos_iniciais_{IDEB_YEAR}"].isna().sum()
    com_tudo = base[
        base["populacao"].notna() &
        base[f"ideb_anos_iniciais_{IDEB_YEAR}"].notna()
    ]

    print(f"\n[merge] Resultado:")
    print(f"  Total linhas:               {len(base):,}")
    print(f"  Municípios únicos:          {base['cod_municipio'].nunique():,}")
    print(f"  Sem match IBGE (pop):       {sem_ibge:,}")
    print(f"  Sem match IDEB:             {sem_ideb:,}")
    print(f"  Com as 3 bases completas:   {len(com_tudo):,}")

    out_path = PROCESSED_DIR / "base_municipal_mvp.csv"
    base.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\n[merge] salvo -> {out_path}")
    return base


if __name__ == "__main__":
    base = run()

    print("\n=== COLUNAS FINAIS ===")
    for c in base.columns:
        non_null = base[c].notna().sum()
        print(f"  {c:<40} {non_null:,} não-nulos de {len(base):,}")

    print("\n=== AMOSTRA (5 linhas) ===")
    cols_show = [
        "uf", "cod_municipio", "nome_municipio",
        "total_receitas", "populacao", "total_receitas_per_capita",
        f"ideb_anos_iniciais_{IDEB_YEAR}", f"ideb_anos_finais_{IDEB_YEAR}",
    ]
    print(base[cols_show].head(5).to_string())
