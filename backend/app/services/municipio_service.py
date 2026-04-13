"""
MunicipioService — loads base_municipal_mvp.csv into memory at startup
and provides all query methods consumed by the API routes.

Designed to be swapped for a SQLAlchemy/PostgreSQL implementation
when the database layer is ready, without changing the route handlers.
"""

import math
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd

BASE_PATH = Path(__file__).parents[3] / "data" / "processed" / "base_municipal_mvp.csv"


@lru_cache(maxsize=1)
def _load() -> pd.DataFrame:
    df = pd.read_csv(BASE_PATH, dtype={"cod_municipio": str})
    df["cod_municipio"] = df["cod_municipio"].str.zfill(7)
    df["nome_municipio"] = df["nome_municipio"].str.strip()
    df["uf"] = df["uf"].str.upper()
    return df


def _nan_to_none(value):
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
        "total_receitas_per_capita": _nan_to_none(row.get("total_receitas_per_capita")),
        "ideb_anos_iniciais_2023": _nan_to_none(row.get("ideb_anos_iniciais_2023")),
        "ideb_anos_finais_2023": _nan_to_none(row.get("ideb_anos_finais_2023")),
    }


def _row_to_detalhe(row: pd.Series) -> dict:
    return {
        **_row_to_resumo(row),
        "ano": int(row["ano"]),
        "populacao": _nan_to_none(row.get("populacao")),
        "receita_contribuicao": float(row["receita_contribuicao"]),
        "comp_vaaf": float(row["comp_vaaf"]),
        "comp_vaat": float(row["comp_vaat"]),
        "comp_vaar": float(row["comp_vaar"]),
        "comp_uniao_total": float(row["comp_uniao_total"]),
    }


# ── Public API ────────────────────────────────────────────────────────────────

def get_resumo() -> dict:
    df = _load()
    com_ideb = df["ideb_anos_iniciais_2023"].notna().sum()
    sem_pop = df["populacao"].isna().sum()
    df_pc = df[df["total_receitas_per_capita"].notna()]

    return {
        "total_municipios": len(df),
        "total_municipios_com_ideb": int(com_ideb),
        "total_municipios_sem_populacao": int(sem_pop),
        "ufs_disponiveis": df["uf"].nunique(),
        "soma_total_receitas": round(float(df["total_receitas"].sum()), 2),
        "media_per_capita": round(float(df_pc["total_receitas_per_capita"].mean()), 2),
        "mediana_per_capita": round(float(df_pc["total_receitas_per_capita"].median()), 2),
        "media_ideb_iniciais": round(float(df["ideb_anos_iniciais_2023"].mean()), 2),
        "media_ideb_finais": round(float(df["ideb_anos_finais_2023"].mean()), 2),
        "ano_fundeb": int(df["ano"].iloc[0]),
        "ano_ideb": 2023,
    }


def get_filtros() -> dict:
    df = _load()
    df_pc = df[df["total_receitas_per_capita"].notna()]
    df_ideb = df[df["ideb_anos_iniciais_2023"].notna()]

    return {
        "ufs": sorted(df["uf"].unique().tolist()),
        "ano_fundeb": int(df["ano"].iloc[0]),
        "ano_ideb": 2023,
        "per_capita_min": round(float(df_pc["total_receitas_per_capita"].min()), 2),
        "per_capita_max": round(float(df_pc["total_receitas_per_capita"].max()), 2),
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
    df = _load()[_load()["total_receitas_per_capita"].notna()].copy()

    if uf:
        df = df[df["uf"] == uf.upper()]

    ascending = ordem == "asc"
    df = df.sort_values("total_receitas_per_capita", ascending=ascending).head(limite)

    result = []
    for posicao, (_, row) in enumerate(df.iterrows(), start=1):
        result.append({
            "posicao": posicao,
            **_row_to_resumo(row),
            "populacao": _nan_to_none(row.get("populacao")),
        })
    return result


def get_eficiencia(
    uf: Optional[str] = None,
    etapa: str = "iniciais",
    per_capita_max: Optional[float] = 5000,
) -> list[dict]:
    df = _load().copy()
    col_ideb = "ideb_anos_iniciais_2023" if etapa == "iniciais" else "ideb_anos_finais_2023"

    df = df[df["total_receitas_per_capita"].notna() & df[col_ideb].notna()]
    if uf:
        df = df[df["uf"] == uf.upper()]
    if per_capita_max:
        df = df[df["total_receitas_per_capita"] <= per_capita_max]

    if len(df) < 3:
        return []

    x = df["total_receitas_per_capita"]
    y = df[col_ideb]
    mx, my = float(x.mean()), float(y.mean())
    b = float(((x - mx) * (y - my)).sum() / ((x - mx) ** 2).sum())
    a = my - b * mx

    df = df.copy()
    df["ideb_esperado"] = (a + b * x).round(3)
    df["residuo"] = (y - df["ideb_esperado"]).round(3)

    max_abs = df["residuo"].abs().max()
    df["score_eficiencia"] = ((df["residuo"] / max_abs * 100).round(1) if max_abs > 0 else 0.0)

    df = df.sort_values("residuo", ascending=False)

    return [
        {
            "cod_municipio": row["cod_municipio"],
            "uf": row["uf"],
            "nome_municipio": row["nome_municipio"],
            "populacao": _nan_to_none(row.get("populacao")),
            "total_receitas_per_capita": round(float(row["total_receitas_per_capita"]), 2),
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
        pc = sub[sub["total_receitas_per_capita"].notna()]
        ini = sub[sub["ideb_anos_iniciais_2023"].notna()]
        fin = sub[sub["ideb_anos_finais_2023"].notna()]
        result.append({
            "uf": uf,
            "total_municipios": len(sub),
            "soma_receitas": round(float(sub["total_receitas"].sum()), 2),
            "media_per_capita": round(float(pc["total_receitas_per_capita"].mean()), 2) if len(pc) else None,
            "mediana_per_capita": round(float(pc["total_receitas_per_capita"].median()), 2) if len(pc) else None,
            "media_ideb_iniciais": round(float(ini["ideb_anos_iniciais_2023"].mean()), 2) if len(ini) else None,
            "media_ideb_finais": round(float(fin["ideb_anos_finais_2023"].mean()), 2) if len(fin) else None,
        })
    return result


def get_medias_uf(uf: str) -> Optional[dict]:
    df = _load()
    sub = df[df["uf"] == uf.upper()]
    if sub.empty:
        return None
    pc = sub[sub["total_receitas_per_capita"].notna()]
    ini = sub[sub["ideb_anos_iniciais_2023"].notna()]
    fin = sub[sub["ideb_anos_finais_2023"].notna()]
    return {
        "uf": uf.upper(),
        "total_municipios": len(sub),
        "media_per_capita": round(float(pc["total_receitas_per_capita"].mean()), 2) if len(pc) else None,
        "media_ideb_iniciais": round(float(ini["ideb_anos_iniciais_2023"].mean()), 2) if len(ini) else None,
        "media_ideb_finais": round(float(fin["ideb_anos_finais_2023"].mean()), 2) if len(fin) else None,
    }


def get_correlacao(
    uf: Optional[str] = None,
    per_capita_max: Optional[float] = None,
) -> list[dict]:
    df = _load().copy()
    df = df[df["total_receitas_per_capita"].notna() & df["ideb_anos_iniciais_2023"].notna()]

    if uf:
        df = df[df["uf"] == uf.upper()]
    if per_capita_max:
        df = df[df["total_receitas_per_capita"] <= per_capita_max]

    return [
        {
            "cod_municipio": row["cod_municipio"],
            "uf": row["uf"],
            "nome_municipio": row["nome_municipio"],
            "total_receitas_per_capita": round(float(row["total_receitas_per_capita"]), 2),
            "ideb_anos_iniciais_2023": _nan_to_none(row["ideb_anos_iniciais_2023"]),
            "ideb_anos_finais_2023": _nan_to_none(row["ideb_anos_finais_2023"]),
            "populacao": _nan_to_none(row.get("populacao")),
        }
        for _, row in df.iterrows()
    ]
