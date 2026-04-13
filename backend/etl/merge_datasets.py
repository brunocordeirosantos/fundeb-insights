"""
Merge FUNDEB, IBGE population, IDEB, and Censo Escolar into a single analytical base.
Output: data/processed/base_municipal_mvp.csv

Join key: cod_municipio (7-digit IBGE code, present in all sources)
Join strategy: left join from FUNDEB (most complete) → IBGE → IDEB → Censo Escolar

Derived metrics:
    total_receitas_per_capita       = total_receitas / populacao
        Context metric only — population includes all ages, not just students.

    fundeb_per_aluno_municipal      = total_receitas / mat_municipal_total
        Primary per-student metric. Denominator is students enrolled in the
        municipal school network — the direct beneficiary of municipal FUNDEB funds.

    fundeb_per_aluno_publica        = total_receitas / mat_publica_total
        Alternative metric using all public-network students (municipal + state +
        federal) for regional comparisons where administrative boundaries blur.

NOTE on network distinction:
    FUNDEB funds received by the municipality finance the REDE MUNICIPAL only.
    State schools (rede estadual) are funded by the state's share of FUNDEB.
    Mixing both networks when calculating per-student investment would understate
    the true investment for municipalities that manage a large municipal network
    and overstate it for those where the state absorbed most enrollment.
"""

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).parents[2] / "data" / "processed"
RAW_DIR = Path(__file__).parents[2] / "data" / "raw"

FUNDEB_YEAR = 2026
IDEB_YEAR = 2023
CENSO_YEAR = 2023


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


def load_censo_escolar() -> pd.DataFrame | None:
    path = PROCESSED_DIR / f"matriculas_municipios_{CENSO_YEAR}.csv"
    if not path.exists():
        print(
            f"[merge] AVISO: {path} não encontrado. "
            f"Execute extract_censo_escolar.py primeiro para habilitar as métricas "
            f"fundeb_per_aluno_municipal e fundeb_per_aluno_publica."
        )
        return None
    df = pd.read_csv(path, dtype={"cod_municipio": str})
    df["cod_municipio"] = df["cod_municipio"].str.zfill(7)
    return df


def run() -> pd.DataFrame:
    fundeb = load_fundeb()
    ibge = load_ibge()
    ideb = load_ideb()
    censo = load_censo_escolar()

    print(f"[merge] FUNDEB:         {len(fundeb):,} registros")
    print(f"[merge] IBGE:           {len(ibge):,} registros")
    print(f"[merge] IDEB:           {len(ideb):,} registros")
    if censo is not None:
        print(f"[merge] Censo Escolar:  {len(censo):,} registros")

    # --- Joins ---
    base = fundeb.merge(ibge, on="cod_municipio", how="left")

    ideb_cols = [
        "cod_municipio",
        f"ideb_anos_iniciais_{IDEB_YEAR}",
        f"ideb_anos_finais_{IDEB_YEAR}",
    ]
    base = base.merge(ideb[ideb_cols], on="cod_municipio", how="left")

    if censo is not None:
        censo_cols = [
            "cod_municipio",
            "mat_municipal_total",
            "mat_estadual_total",
            "mat_publica_total",
        ]
        # Only include columns that exist in the censo output
        censo_cols = [c for c in censo_cols if c in censo.columns]
        base = base.merge(censo[censo_cols], on="cod_municipio", how="left")

    # --- Derived metrics ---

    # Context metric: total population (all ages)
    base["total_receitas_per_capita"] = (
        base["total_receitas"] / base["populacao"]
    ).round(2)

    # Primary metric: per enrolled student in municipal network
    if "mat_municipal_total" in base.columns:
        base["fundeb_per_aluno_municipal"] = (
            base["total_receitas"] / base["mat_municipal_total"]
        ).round(2)

    # Alternative metric: per enrolled student in any public network
    if "mat_publica_total" in base.columns:
        base["fundeb_per_aluno_publica"] = (
            base["total_receitas"] / base["mat_publica_total"]
        ).round(2)

    # --- Quality report ---
    sem_ibge = base["populacao"].isna().sum()
    sem_ideb = base[f"ideb_anos_iniciais_{IDEB_YEAR}"].isna().sum()
    com_tudo_mask = (
        base["populacao"].notna()
        & base[f"ideb_anos_iniciais_{IDEB_YEAR}"].notna()
    )
    if "mat_municipal_total" in base.columns:
        sem_censo = base["mat_municipal_total"].isna().sum()
        com_tudo_mask &= base["mat_municipal_total"].notna()
    else:
        sem_censo = None

    print(f"\n[merge] Resultado:")
    print(f"  Total linhas:                  {len(base):,}")
    print(f"  Municípios únicos:             {base['cod_municipio'].nunique():,}")
    print(f"  Sem match IBGE (pop):          {sem_ibge:,}")
    print(f"  Sem match IDEB:                {sem_ideb:,}")
    if sem_censo is not None:
        print(f"  Sem match Censo Escolar:       {sem_censo:,}")
    print(f"  Com todas as bases completas:  {com_tudo_mask.sum():,}")

    out_path = PROCESSED_DIR / "base_municipal_mvp.csv"
    base.to_csv(out_path, index=False, encoding="utf-8")
    print(f"\n[merge] salvo -> {out_path}")
    return base


if __name__ == "__main__":
    base = run()

    print("\n=== COLUNAS FINAIS ===")
    for c in base.columns:
        non_null = base[c].notna().sum()
        print(f"  {c:<45} {non_null:,} não-nulos de {len(base):,}")

    print("\n=== AMOSTRA (5 linhas) ===")
    cols_show = [
        "uf", "cod_municipio", "nome_municipio",
        "total_receitas",
        "populacao", "total_receitas_per_capita",
    ]
    if "mat_municipal_total" in base.columns:
        cols_show += ["mat_municipal_total", "fundeb_per_aluno_municipal"]
    if "mat_publica_total" in base.columns:
        cols_show += ["mat_publica_total", "fundeb_per_aluno_publica"]
    cols_show += [
        f"ideb_anos_iniciais_{IDEB_YEAR}",
        f"ideb_anos_finais_{IDEB_YEAR}",
    ]
    print(base[[c for c in cols_show if c in base.columns]].head(5).to_string())
