"""
UFService — loads base_estadual_mvp.csv and provides state-level query methods.

Key concepts:
    fundeb_per_aluno_estadual   — state FUNDEB ÷ rede estadual enrollments
    mediana_per_aluno_municipal — median of municipal per-student investment within the state
    razao_per_aluno             — estadual ÷ mediana_municipal (benchmark ratio)

A razao_per_aluno > 1.0 means the state government invests more per student than
the median municipality in the same state. This does NOT mean the state is more
efficient — it may reflect structural differences (e.g. state manages secondary
schools which are more expensive, or fewer students in the rede estadual).
"""

import math
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd

BASE_PATH = Path(__file__).parents[3] / "data" / "processed" / "base_estadual_mvp.csv"


@lru_cache(maxsize=1)
def _load() -> pd.DataFrame:
    df = pd.read_csv(BASE_PATH, dtype={"cod_ibge_estado": str})
    df["uf"] = df["uf"].str.upper().str.strip()
    df["cod_ibge_estado"] = df["cod_ibge_estado"].str.zfill(2)
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
        "uf": row["uf"],
        "nome_estado": row["nome_estado"],
        "regiao": row["regiao"],
        "total_municipios": int(row.get("total_municipios", 0)),
        "fundeb_estadual_total": float(row["total_receitas"]),
        "fundeb_municipal_total": float(row.get("fundeb_municipal_total", 0)),
        "fundeb_total_uf": float(row.get("fundeb_total_uf", 0)),
        "mat_estadual_total": _nan_to_none(row.get("mat_estadual_total")),
        "mat_municipal_total_uf": _nan_to_none(row.get("mat_municipal_total_uf")),
        "mat_publica_total_uf": _nan_to_none(row.get("mat_publica_total_uf")),
        "pct_mat_estadual": _nan_to_none(row.get("pct_mat_estadual")),
        "fundeb_per_aluno_estadual": _nan_to_none(row.get("fundeb_per_aluno_estadual")),
        "mediana_per_aluno_municipal": _nan_to_none(row.get("mediana_per_aluno_municipal")),
        "razao_per_aluno": _nan_to_none(row.get("razao_per_aluno")),
        "media_ideb_iniciais": _nan_to_none(row.get("media_ideb_iniciais")),
        "media_ideb_finais": _nan_to_none(row.get("media_ideb_finais")),
    }


def _row_to_detalhe(row: pd.Series) -> dict:
    return {
        **_row_to_resumo(row),
        "ano_fundeb": int(row.get("ano", 2026)),
        "cod_ibge_estado": str(row.get("cod_ibge_estado", "")),
        "receita_contribuicao": float(row.get("receita_contribuicao", 0)),
        "comp_vaaf": float(row.get("comp_vaaf", 0)),
        "comp_vaat": float(row.get("comp_vaat", 0)),
        "comp_vaar": float(row.get("comp_vaar", 0)),
        "comp_uniao_total": float(row.get("comp_uniao_total", 0)),
        "media_per_aluno_municipal": _nan_to_none(row.get("media_per_aluno_municipal")),
        "media_per_capita": _nan_to_none(row.get("media_per_capita")),
        "municipios_com_ideb": int(row["municipios_com_ideb"]) if pd.notna(row.get("municipios_com_ideb")) else None,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def list_estados(regiao: Optional[str] = None) -> list[dict]:
    df = _load().copy()
    if regiao:
        df = df[df["regiao"].str.lower() == regiao.lower()]
    df = df.sort_values("uf")
    return [_row_to_resumo(row) for _, row in df.iterrows()]


def get_estado(uf: str) -> Optional[dict]:
    df = _load()
    rows = df[df["uf"] == uf.upper()]
    if rows.empty:
        return None
    return _row_to_detalhe(rows.iloc[0])


def get_ranking_estados(
    regiao: Optional[str] = None,
    metrica: str = "fundeb_per_aluno_estadual",
    ordem: str = "desc",
    limite: int = 27,
) -> list[dict]:
    """
    Rank states by a given metric.
    metrica: 'fundeb_per_aluno_estadual' | 'razao_per_aluno' | 'media_ideb_iniciais' | 'fundeb_estadual_total'
    """
    allowed = {
        "fundeb_per_aluno_estadual",
        "razao_per_aluno",
        "media_ideb_iniciais",
        "fundeb_estadual_total",
        "mediana_per_aluno_municipal",
    }
    if metrica not in allowed:
        metrica = "fundeb_per_aluno_estadual"

    col = metrica if metrica != "fundeb_estadual_total" else "total_receitas"
    df = _load().copy()
    df = df[df[col].notna()]

    if regiao:
        df = df[df["regiao"].str.lower() == regiao.lower()]

    ascending = ordem == "asc"
    df = df.sort_values(col, ascending=ascending).head(limite)

    return [
        {
            "posicao": pos,
            "uf": row["uf"],
            "nome_estado": row["nome_estado"],
            "regiao": row["regiao"],
            "fundeb_per_aluno_estadual": _nan_to_none(row.get("fundeb_per_aluno_estadual")),
            "mediana_per_aluno_municipal": _nan_to_none(row.get("mediana_per_aluno_municipal")),
            "razao_per_aluno": _nan_to_none(row.get("razao_per_aluno")),
            "mat_estadual_total": _nan_to_none(row.get("mat_estadual_total")),
            "fundeb_estadual_total": float(row["total_receitas"]),
            "media_ideb_iniciais": _nan_to_none(row.get("media_ideb_iniciais")),
        }
        for pos, (_, row) in enumerate(df.iterrows(), start=1)
    ]


def get_comparativo() -> list[dict]:
    """
    Returns all states sorted by regiao + uf for the
    estado vs municipal per-student comparison chart.
    """
    df = _load().copy()
    df = df.sort_values(["regiao", "uf"])

    return [
        {
            "uf": row["uf"],
            "nome_estado": row["nome_estado"],
            "regiao": row["regiao"],
            "fundeb_per_aluno_estadual": _nan_to_none(row.get("fundeb_per_aluno_estadual")),
            "mediana_per_aluno_municipal": _nan_to_none(row.get("mediana_per_aluno_municipal")),
            "razao_per_aluno": _nan_to_none(row.get("razao_per_aluno")),
            "pct_mat_estadual": _nan_to_none(row.get("pct_mat_estadual")),
            "media_ideb_iniciais": _nan_to_none(row.get("media_ideb_iniciais")),
            "media_ideb_finais": _nan_to_none(row.get("media_ideb_finais")),
        }
        for _, row in df.iterrows()
    ]


def get_resumo_nacional() -> dict:
    df = _load()
    pa = df[df["fundeb_per_aluno_estadual"].notna()]
    return {
        "total_estados": len(df),
        "fundeb_estadual_brasil": round(float(df["total_receitas"].sum()), 2),
        "fundeb_municipal_brasil": round(float(df["fundeb_municipal_total"].sum()), 2),
        "mat_estadual_brasil": int(df["mat_estadual_total"].sum()),
        "mat_municipal_brasil": int(df["mat_municipal_total_uf"].sum()),
        "media_per_aluno_estadual": round(float(pa["fundeb_per_aluno_estadual"].mean()), 2),
        "mediana_per_aluno_estadual": round(float(pa["fundeb_per_aluno_estadual"].median()), 2),
        "regioes": sorted(df["regiao"].unique().tolist()),
    }
