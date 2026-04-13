"""
Build the state-level analytical base (base_estadual_mvp.csv).

Joins:
    fundeb_estados_<year>.csv       — FUNDEB received by each state government
    matriculas_municipios_<year>.csv — Censo Escolar: aggregated to UF level
    base_municipal_mvp.csv          — municipal metrics aggregated to UF level

Output: data/processed/base_estadual_mvp.csv (27 rows, one per state)

Key derived metrics:
    fundeb_per_aluno_estadual
        State FUNDEB ÷ total rede estadual enrollments.
        Mirrors fundeb_per_aluno_municipal but for the state network.

    razao_per_aluno
        fundeb_per_aluno_estadual ÷ median fundeb_per_aluno_municipal across
        the state's municipalities.
        > 1.0 → state invests more per student than municipalities (on average)
        < 1.0 → municipalities invest more per student than the state

    pct_mat_estadual
        Share of public enrollment managed by the state (vs municipal).
        High value → state dominates public education in that UF.
"""

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).parents[2] / "data" / "processed"
FUNDEB_YEAR = 2026
CENSO_YEAR = 2023
IDEB_YEAR = 2023


def load_fundeb_estados() -> pd.DataFrame:
    path = PROCESSED_DIR / f"fundeb_estados_{FUNDEB_YEAR}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} não encontrado. Execute extract_fundeb_estados.py primeiro."
        )
    return pd.read_csv(path, dtype={"cod_ibge_estado": str})


def load_censo_por_uf() -> pd.DataFrame:
    """Aggregate Censo Escolar municipal data to UF level."""
    path = PROCESSED_DIR / f"matriculas_municipios_{CENSO_YEAR}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} não encontrado. Execute extract_censo_escolar.py primeiro."
        )
    df = pd.read_csv(path, dtype={"cod_municipio": str})

    # UF column in censo has full state name (e.g. "Rondônia"), not abbreviation.
    # The municipal base has the UF abbreviation — use that as key instead.
    base = pd.read_csv(PROCESSED_DIR / "base_municipal_mvp.csv", dtype={"cod_municipio": str})
    cod_to_uf = base.set_index("cod_municipio")["uf"].to_dict()
    df["uf"] = df["cod_municipio"].str.zfill(7).map(cod_to_uf)

    agg = df.groupby("uf", dropna=True).agg(
        mat_estadual_total=("mat_estadual_total", "sum"),
        mat_municipal_total_uf=("mat_municipal_total", "sum"),
        mat_publica_total_uf=("mat_publica_total", "sum"),
        mat_total_uf=("mat_total", "sum"),
    ).reset_index()

    return agg


def load_municipal_por_uf() -> pd.DataFrame:
    """Aggregate municipal base to UF level."""
    path = PROCESSED_DIR / "base_municipal_mvp.csv"
    df = pd.read_csv(path, dtype={"cod_municipio": str})

    agg = df.groupby("uf", dropna=True).agg(
        total_municipios=("cod_municipio", "count"),
        fundeb_municipal_total=("total_receitas", "sum"),
        media_per_aluno_municipal=("fundeb_per_aluno_municipal", "mean"),
        mediana_per_aluno_municipal=("fundeb_per_aluno_municipal", "median"),
        media_per_capita=("total_receitas_per_capita", "mean"),
        media_ideb_iniciais=("ideb_anos_iniciais_2023", "mean"),
        media_ideb_finais=("ideb_anos_finais_2023", "mean"),
        municipios_com_ideb=("ideb_anos_iniciais_2023", "count"),
    ).reset_index()

    # Round float columns
    float_cols = [c for c in agg.columns if agg[c].dtype == "float64"]
    agg[float_cols] = agg[float_cols].round(2)
    return agg


def run() -> pd.DataFrame:
    estados = load_fundeb_estados()
    censo_uf = load_censo_por_uf()
    mun_uf = load_municipal_por_uf()

    print(f"[merge_estados] estados FUNDEB:   {len(estados)}")
    print(f"[merge_estados] UFs censo:        {len(censo_uf)}")
    print(f"[merge_estados] UFs municipal:    {len(mun_uf)}")

    base = estados.merge(censo_uf, on="uf", how="left")
    base = base.merge(mun_uf, on="uf", how="left")

    # Primary metric: FUNDEB per enrolled student in state network
    base["fundeb_per_aluno_estadual"] = (
        base["total_receitas"] / base["mat_estadual_total"]
    ).round(2)

    # Ratio: state vs municipal per-student investment
    # Uses median of municipalities (more robust than mean against outliers)
    base["razao_per_aluno"] = (
        base["fundeb_per_aluno_estadual"] / base["mediana_per_aluno_municipal"]
    ).round(3)

    # Share of public enrollment managed by the state
    base["pct_mat_estadual"] = (
        base["mat_estadual_total"] / base["mat_publica_total_uf"] * 100
    ).round(1)

    # Total FUNDEB in the UF (state + all municipalities)
    base["fundeb_total_uf"] = (base["total_receitas"] + base["fundeb_municipal_total"]).round(2)

    out_path = PROCESSED_DIR / "base_estadual_mvp.csv"
    base.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[merge_estados] salvo -> {out_path} ({len(base)} estados)")
    return base


if __name__ == "__main__":
    base = run()

    print("\n=== COLUNAS FINAIS ===")
    for c in base.columns:
        print(f"  {c}")

    print("\n=== TOP 5 POR FUNDEB ESTADUAL TOTAL ===")
    top = base.sort_values("total_receitas", ascending=False).head(5)
    print(top[["uf", "nome_estado", "total_receitas", "mat_estadual_total",
               "fundeb_per_aluno_estadual", "mediana_per_aluno_municipal",
               "razao_per_aluno"]].to_string())

    print("\n=== RAZAO PER ALUNO (estado vs municipios) ===")
    ratio = base[["uf", "razao_per_aluno", "fundeb_per_aluno_estadual",
                  "mediana_per_aluno_municipal"]].sort_values("razao_per_aluno", ascending=False)
    print(ratio.to_string())
