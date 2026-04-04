from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.municipio import (
    CorrelacaoItem,
    FiltrosDisponiveis,
    MediasUF,
    MunicipioDetalhe,
    MunicipiosResponse,
    RankingItem,
    ResumoDataset,
)
from app.services import municipio_service as svc

router = APIRouter(prefix="/api", tags=["municipios"])


@router.get("/resumo", response_model=ResumoDataset, summary="Visão geral do dataset")
def resumo():
    """Retorna estatísticas agregadas de toda a base."""
    return svc.get_resumo()


@router.get("/filtros", response_model=FiltrosDisponiveis, summary="Opções disponíveis para filtros")
def filtros():
    """Retorna os valores disponíveis para popular os controles do frontend."""
    return svc.get_filtros()


@router.get("/municipios", response_model=MunicipiosResponse, summary="Lista municípios com filtros")
def listar_municipios(
    uf: Optional[str] = Query(None, description="Sigla do estado (ex: SP)"),
    nome: Optional[str] = Query(None, description="Busca parcial pelo nome do município"),
    pagina: int = Query(1, ge=1, description="Página"),
    por_pagina: int = Query(50, ge=1, le=200, description="Itens por página"),
):
    return svc.list_municipios(uf=uf, nome=nome, pagina=pagina, por_pagina=por_pagina)


@router.get(
    "/municipios/{cod_municipio}",
    response_model=MunicipioDetalhe,
    summary="Detalhes de um município",
)
def detalhe_municipio(cod_municipio: str):
    """Retorna todos os dados de um município pelo código IBGE (7 dígitos)."""
    result = svc.get_municipio(cod_municipio)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Município '{cod_municipio}' não encontrado.")
    return result


@router.get("/ranking", response_model=list[RankingItem], summary="Ranking por receita FUNDEB per capita")
def ranking(
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    limite: int = Query(20, ge=1, le=100, description="Número de municípios no ranking"),
    ordem: str = Query("desc", pattern="^(asc|desc)$", description="'desc' = maior primeiro"),
):
    """
    Retorna os municípios ordenados por receita FUNDEB per capita.
    Use `ordem=asc` para os menores (bottom ranking).
    """
    return svc.get_ranking(uf=uf, limite=limite, ordem=ordem)


@router.get("/uf/{uf}", response_model=MediasUF, summary="Médias da UF para comparação")
def medias_uf(uf: str):
    """Retorna médias de per capita e IDEB para todos os municípios de uma UF."""
    result = svc.get_medias_uf(uf)
    if result is None:
        raise HTTPException(status_code=404, detail=f"UF '{uf}' não encontrada.")
    return result


@router.get(
    "/correlacao",
    response_model=list[CorrelacaoItem],
    summary="Dados para gráfico de correlação FUNDEB per capita × IDEB",
)
def correlacao(
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    per_capita_max: Optional[float] = Query(
        None, description="Limitar per capita máximo (remove outliers extremos)"
    ),
):
    """
    Retorna pontos para o scatter chart de investimento vs desempenho.
    Recomenda-se usar `per_capita_max=5000` para excluir outliers extremos na visualização.
    """
    return svc.get_correlacao(uf=uf, per_capita_max=per_capita_max)
