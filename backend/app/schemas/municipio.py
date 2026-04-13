from pydantic import BaseModel
from typing import Optional


class MunicipioResumo(BaseModel):
    cod_municipio: str
    uf: str
    nome_municipio: str
    total_receitas: float
    total_receitas_per_capita: Optional[float]
    ideb_anos_iniciais_2023: Optional[float]
    ideb_anos_finais_2023: Optional[float]


class MunicipioDetalhe(MunicipioResumo):
    ano: int
    populacao: Optional[float]
    receita_contribuicao: float
    comp_vaaf: float
    comp_vaat: float
    comp_vaar: float
    comp_uniao_total: float


class RankingItem(BaseModel):
    posicao: int
    cod_municipio: str
    uf: str
    nome_municipio: str
    populacao: Optional[float]
    total_receitas: float
    total_receitas_per_capita: Optional[float]
    ideb_anos_iniciais_2023: Optional[float]


class CorrelacaoItem(BaseModel):
    cod_municipio: str
    uf: str
    nome_municipio: str
    total_receitas_per_capita: float
    ideb_anos_iniciais_2023: Optional[float]
    ideb_anos_finais_2023: Optional[float]
    populacao: Optional[float]


class ResumoDataset(BaseModel):
    total_municipios: int
    total_municipios_com_ideb: int
    total_municipios_sem_populacao: int
    ufs_disponiveis: int
    soma_total_receitas: float
    media_per_capita: float
    mediana_per_capita: float
    media_ideb_iniciais: float
    media_ideb_finais: float
    ano_fundeb: int
    ano_ideb: int


class FiltrosDisponiveis(BaseModel):
    ufs: list[str]
    ano_fundeb: int
    ano_ideb: int
    per_capita_min: float
    per_capita_max: float
    ideb_min: float
    ideb_max: float


class MediasUF(BaseModel):
    uf: str
    total_municipios: int
    media_per_capita: Optional[float]
    media_ideb_iniciais: Optional[float]
    media_ideb_finais: Optional[float]


class EficienciaItem(BaseModel):
    cod_municipio: str
    uf: str
    nome_municipio: str
    populacao: Optional[float]
    total_receitas_per_capita: float
    ideb_real: float
    ideb_esperado: float
    residuo: float
    score_eficiencia: float


class MediasUFCompleta(BaseModel):
    uf: str
    total_municipios: int
    soma_receitas: float
    media_per_capita: Optional[float]
    mediana_per_capita: Optional[float]
    media_ideb_iniciais: Optional[float]
    media_ideb_finais: Optional[float]


class PaginacaoMeta(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int


class MunicipiosResponse(BaseModel):
    meta: PaginacaoMeta
    data: list[MunicipioResumo]
