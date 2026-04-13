"""
MunicipioService — loads base_municipal_mvp.csv into memory at startup
and provides all query methods consumed by the API routes.

Primary investment metric: fundeb_per_aluno_municipal
    FUNDEB total received by the municipality divided by the number of students
    enrolled in the municipal school network (rede municipal). This is the
    correct denominator because municipal FUNDEB funds finance municipal schools
    directly. State schools (rede estadual) are financed by the state's own
    FUNDEB share and must not be mixed into the municipal per-student calculation.

Context metric: total_receitas_per_capita
    FUNDEB divided by total population. Kept for reference and geographic
    comparisons but should not be used as a proxy for educational investment.
"""

import math
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd

BASE_PATH = Path(__file__).parents[3] / "data" / "processed" / "base_municipal_mvp.csv"

METRIC_PER_ALUNO = "fundeb_per_aluno_municipal"
METRIC_PER_CAPITA = "total_receitas_per_capita"


@lru_cache(maxsize=1)
def _load() -> pd.DataFrame:
    df = pd.read_csv(BASE_PATH, dtype={"cod_municipio": str})
    df["cod_municipio"] = df["cod_municipio"].str.zfill(7)
    df["nome_municipio"] = df["nome_municipio"].str.strip()
    df["uf"] = df["uf"].str.upper()
    return df


def _nan_to_none(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return None if math.isnan(float(value)) else float(value)
    except (TypeError, ValueError):
        return None


def _row_to_resumo(row: pd.Series) -> dict:
    return {
        "cod_municipio": row["cod_municipio"],
        "uf": row["uf"],
        "nome_municipio": row["nome_municipio"],
        "total_receitas": float(row["total_receitas"]),
        "fundeb_per_aluno_municipal": _nan_to_none(row.get(METRIC_PER_ALUNO)),
        "total_receitas_per_capita": _nan_to_none(row.get(METRIC_PER_CAPITA)),
        "ideb_anos_iniciais_2023": _nan_to_none(row.get("ideb_anos_iniciais_2023")),
        "ideb_anos_finais_2023": _nan_to_none(row.get("ideb_anos_finais_2023")),
    }


def _row_to_detalhe(row: pd.Series) -> dict:
    return {
        **_row_to_resumo(row),
        "ano": int(row["ano"]),
        "populacao": _nan_to_none(row.get("populacao")),
        "mat_municipal_total": _nan_to_none(row.get("mat_municipal_total")),
        "mat_estadual_total": _nan_to_none(row.get("mat_estadual_total")),
        "mat_publica_total": _nan_to_none(row.get("mat_publica_total")),
        "fundeb_per_aluno_publica": _nan_to_none(row.get("fundeb_per_aluno_publica")),
        "receita_contribuicao": float(row["receita_contribuicao"]),
        "comp_vaaf": float(row["comp_vaaf"]),
        "comp_vaat": float(row["comp_vaat"]),
        "comp_vaar": float(row["comp_uniao_total"]),
        "comp_uniao_total": float(row["comp_uniao_total"]),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def get_resumo() -> dict:
    df = _load()
    com_ideb = df["ideb_anos_iniciais_2023"].notna().sum()

    df_pa = df[df[METRIC_PER_ALUNO].notna()]
    df_pc = df[df[METRIC_PER_CAPITA].notna()]
    sem_mat = df["mat_municipal_total"].isna().sum() if "mat_municipal_total" in df.columns else 0

    return {
        "total_municipios": len(df),
        "total_municipios_com_ideb": int(com_ideb),
        "total_municipios_sem_matriculas": int(sem_mat),
        "ufs_disponiveis": df["uf"].nunique(),
        "soma_total_receitas": round(float(df["total_receitas"].sum()), 2),
        "media_per_aluno_municipal": round(float(df_pa[METRIC_PER_ALUNO].mean()), 2),
        "mediana_per_aluno_municipal": round(float(df_pa[METRIC_PER_ALUNO].median()), 2),
        "media_per_capita": round(float(df_pc[METRIC_PER_CAPITA].mean()), 2),
        "mediana_per_capita": round(float(df_pc[METRIC_PER_CAPITA].median()), 2),
        "media_ideb_iniciais": round(float(df["ideb_anos_iniciais_2023"].mean()), 2),
        "media_ideb_finais": round(float(df["ideb_anos_finais_2023"].mean()), 2),
        "ano_fundeb": int(df["ano"].iloc[0]),
        "ano_ideb": 2023,
    }


def get_filtros() -> dict:
    df = _load()
    df_pa = df[df[METRIC_PER_ALUNO].notna()]
    df_pc = df[df[METRIC_PER_CAPITA].notna()]
    df_ideb = df[df["ideb_anos_iniciais_2023"].notna()]

    return {
        "ufs": sorted(df["uf"].unique().tolist()),
        "ano_fundeb": int(df["ano"].iloc[0]),
        "ano_ideb": 2023,
        "per_aluno_min": round(float(df_pa[METRIC_PER_ALUNO].min()), 2),
        "per_aluno_max": round(float(df_pa[METRIC_PER_ALUNO].max()), 2),
        "per_capita_min": round(float(df_pc[METRIC_PER_CAPITA].min()), 2),
        "per_capita_max": round(float(df_pc[METRIC_PER_CAPITA].max()), 2),
        "ideb_min": round(float(df_ideb["ideb_anos_iniciais_2023"].min()), 2),
        "ideb_max": round(float(df_ideb["ideb_anos_iniciais_2023"].max()), 2),
    }


def list_municipios(
    uf: Optional[str] = None,
    nome: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 50,
) -> dict:
    df = _load().copy()

    if uf:
        df = df[df["uf"] == uf.upper()]
    if nome:
        df = df[df["nome_municipio"].str.contains(nome.strip(), case=False, na=False)]

    total = len(df)
    total_paginas = max(1, math.ceil(total / por_pagina))
    pagina = max(1, min(pagina, total_paginas))
    start = (pagina - 1) * por_pagina
    page_df = df.iloc[start : start + por_pagina]

    return {
        "meta": {
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_paginas": total_paginas,
        },
        "data": [_row_to_resumo(row) for _, row in page_df.iterrows()],
    }


def get_municipio(cod_municipio: str) -> Optional[dict]:
    df = _load()
    rows = df[df["cod_municipio"] == cod_municipio.zfill(7)]
    if rows.empty:
        return None
    return _row_to_detalhe(rows.iloc[0])


def get_ranking(
    uf: Optional[str] = None,
    limite: int = 20,
    ordem: str = "desc",
) -> list[dict]:
    df = _load()
    df = df[df[METRIC_PER_ALUNO].notna()].copy()

    if uf:
        df = df[df["uf"] == uf.upper()]

    ascending = ordem == "asc"
    df = df.sort_values(METRIC_PER_ALUNO, ascending=ascending).head(limite)

    return [
        {
            "posicao": pos,
            "cod_municipio": row["cod_municipio"],
            "uf": row["uf"],
            "nome_municipio": row["nome_municipio"],
            "total_receitas": float(row["total_receitas"]),
            "mat_municipal_total": _nan_to_none(row.get("mat_municipal_total")),
            "fundeb_per_aluno_municipal": _nan_to_none(row[METRIC_PER_ALUNO]),
            "total_receitas_per_capita": _nan_to_none(row.get(METRIC_PER_CAPITA)),
            "populacao": _nan_to_none(row.get("populacao")),
            "ideb_anos_iniciais_2023": _nan_to_none(row.get("ideb_anos_iniciais_2023")),
        }
        for pos, (_, row) in enumerate(df.iterrows(), start=1)
    ]


def get_eficiencia(
    uf: Optional[str] = None,
    etapa: str = "iniciais",
    per_capita_max: Optional[float] = None,
) -> list[dict]:
    """
    Calculates the regression residual (actual IDEB − expected IDEB given investment).
    Investment is measured by fundeb_per_aluno_municipal.
    Municipalities with positive residual deliver more than expected for their funding level.

    per_capita_max: optional upper bound on fundeb_per_aluno_municipal to exclude extreme outliers.
    """
    df = _load().copy()
    col_ideb = "ideb_anos_iniciais_2023" if etapa == "iniciais" else "ideb_anos_finais_2023"

    df = df[df[METRIC_PER_ALUNO].notna() & df[col_ideb].notna()]
    if uf:
        df = df[df["uf"] == uf.upper()]
    if per_capita_max:
        df = df[df[METRIC_PER_ALUNO] <= per_capita_max]

    if len(df) < 3:
        return []

    x = df[METRIC_PER_ALUNO]
    y = df[col_ideb]
    mx, my = float(x.mean()), float(y.mean())
    b = float(((x - mx) * (y - my)).sum() / ((x - mx) ** 2).sum())
    a = my - b * mx

    df = df.copy()
    df["ideb_esperado"] = (a + b * x).round(3)
    df["residuo"] = (y - df["ideb_esperado"]).round(3)

    max_abs = df["residuo"].abs().max()
    df["score_eficiencia"] = (df["residuo"] / max_abs * 100).round(1) if max_abs > 0 else 0.0

    df = df.sort_values("residuo", ascending=False)

    return [
        {
            "cod_municipio": row["cod_municipio"],
            "uf": row["uf"],
            "nome_municipio": row["nome_municipio"],
            "populacao": _nan_to_none(row.get("populacao")),
            "mat_municipal_total": _nan_to_none(row.get("mat_municipal_total")),
            "fundeb_per_aluno_municipal": round(float(row[METRIC_PER_ALUNO]), 2),
            "total_receitas_per_capita": _nan_to_none(row.get(METRIC_PER_CAPITA)),
            "ideb_real": float(row[col_ideb]),
            "ideb_esperado": float(row["ideb_esperado"]),
            "residuo": float(row["residuo"]),
            "score_eficiencia": float(row["score_eficiencia"]),
        }
        for _, row in df.iterrows()
    ]


def get_todas_ufs() -> list[dict]:
    df = _load()
    result = []
    for uf in sorted(df["uf"].unique()):
        sub = df[df["uf"] == uf]
        pa = sub[sub[METRIC_PER_ALUNO].notna()]
        pc = sub[sub[METRIC_PER_CAPITA].notna()]
        ini = sub[sub["ideb_anos_iniciais_2023"].notna()]
        fin = sub[sub["ideb_anos_finais_2023"].notna()]
        result.append({
            "uf": uf,
            "total_municipios": len(sub),
            "soma_receitas": round(float(sub["total_receitas"].sum()), 2),
            "media_per_aluno_municipal": round(float(pa[METRIC_PER_ALUNO].mean()), 2) if len(pa) else None,
            "mediana_per_aluno_municipal": round(float(pa[METRIC_PER_ALUNO].median()), 2) if len(pa) else None,
            "media_per_capita": round(float(pc[METRIC_PER_CAPITA].mean()), 2) if len(pc) else None,
            "mediana_per_capita": round(float(pc[METRIC_PER_CAPITA].median()), 2) if len(pc) else None,
            "media_ideb_iniciais": round(float(ini["ideb_anos_iniciais_2023"].mean()), 2) if len(ini) else None,
            "media_ideb_finais": round(float(fin["ideb_anos_finais_2023"].mean()), 2) if len(fin) else None,
        })
    return result


def get_medias_uf(uf: str) -> Optional[dict]:
    df = _load()
    sub = df[df["uf"] == uf.upper()]
    if sub.empty:
        return None
    pa = sub[sub[METRIC_PER_ALUNO].notna()]
    pc = sub[sub[METRIC_PER_CAPITA].notna()]
    ini = sub[sub["ideb_anos_iniciais_2023"].notna()]
    fin = sub[sub["ideb_anos_finais_2023"].notna()]
    return {
        "uf": uf.upper(),
        "total_municipios": len(sub),
        "media_per_aluno_municipal": round(float(pa[METRIC_PER_ALUNO].mean()), 2) if len(pa) else None,
        "media_per_capita": round(float(pc[METRIC_PER_CAPITA].mean()), 2) if len(pc) else None,
        "media_ideb_iniciais": round(float(ini["ideb_anos_iniciais_2023"].mean()), 2) if len(ini) else None,
        "media_ideb_finais": round(float(fin["ideb_anos_finais_2023"].mean()), 2) if len(fin) else None,
    }


def get_correlacao(
    uf: Optional[str] = None,
    per_capita_max: Optional[float] = None,
) -> list[dict]:
    """
    Returns data points for the investment × performance scatter chart.
    X-axis: fundeb_per_aluno_municipal (primary investment metric).
    per_capita_max applied to fundeb_per_aluno_municipal for outlier exclusion.
    """
    df = _load().copy()
    df = df[df[METRIC_PER_ALUNO].notna() & df["ideb_anos_iniciais_2023"].notna()]

    if uf:
        df = df[df["uf"] == uf.upper()]
    if per_capita_max:
        df = df[df[METRIC_PER_ALUNO] <= per_capita_max]

    return [
        {
            "cod_municipio": row["cod_municipio"],
            "uf": row["uf"],
            "nome_municipio": row["nome_municipio"],
            "fundeb_per_aluno_municipal": round(float(row[METRIC_PER_ALUNO]), 2),
            "total_receitas_per_capita": _nan_to_none(row.get(METRIC_PER_CAPITA)),
            "ideb_anos_iniciais_2023": _nan_to_none(row["ideb_anos_iniciais_2023"]),
            "ideb_anos_finais_2023": _nan_to_none(row["ideb_anos_finais_2023"]),
            "mat_municipal_total": _nan_to_none(row.get("mat_municipal_total")),
            "populacao": _nan_to_none(row.get("populacao")),
        }
        for _, row in df.iterrows()
    ]
