from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.uf import UFComparativoItem, UFDetalhe, UFRankingItem, UFResumo
from app.services import uf_service as svc

router = APIRouter(prefix="/api/estados", tags=["estados"])


@router.get(
    "",
    response_model=list[UFResumo],
    summary="Lista todos os estados com indicadores FUNDEB",
)
def listar_estados(
    regiao: Optional[str] = Query(
        None,
        description="Filtrar por macrorregião: Norte, Nordeste, Sudeste, Sul, Centro-Oeste",
    ),
):
    """
    Returns all 27 states with FUNDEB totals, enrollment, per-student investment,
    and comparison ratios between state and municipal networks.
    """
    return svc.list_estados(regiao=regiao)


@router.get(
    "/resumo",
    summary="Totais nacionais da rede estadual",
)
def resumo_nacional():
    """National aggregates: total FUNDEB by network, total enrollments, national averages."""
    return svc.get_resumo_nacional()


@router.get(
    "/ranking",
    response_model=list[UFRankingItem],
    summary="Ranking de estados por métrica selecionada",
)
def ranking_estados(
    regiao: Optional[str] = Query(None, description="Filtrar por macrorregião"),
    metrica: str = Query(
        "fundeb_per_aluno_estadual",
        description=(
            "Métrica de ordenação: "
            "fundeb_per_aluno_estadual | razao_per_aluno | "
            "media_ideb_iniciais | fundeb_estadual_total | mediana_per_aluno_municipal"
        ),
    ),
    ordem: str = Query("desc", pattern="^(asc|desc)$"),
):
    return svc.get_ranking_estados(regiao=regiao, metrica=metrica, ordem=ordem)


@router.get(
    "/comparativo",
    response_model=list[UFComparativoItem],
    summary="Comparativo rede estadual vs rede municipal por estado",
)
def comparativo():
    """
    Returns per-student investment for both networks (state and municipal median)
    for all states. Designed for a grouped bar chart: estadual vs municipal side by side.

    razao_per_aluno > 1.0 → state invests more per student than the median municipality.
    razao_per_aluno < 1.0 → municipalities invest more per student (on average).
    """
    return svc.get_comparativo()


@router.get(
    "/{uf}",
    response_model=UFDetalhe,
    summary="Detalhes de um estado",
)
def detalhe_estado(uf: str):
    """Full state profile: FUNDEB breakdown, enrollment by network, IDEB, comparison ratios."""
    result = svc.get_estado(uf)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Estado '{uf.upper()}' não encontrado.")
    return result
