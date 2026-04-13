from pydantic import BaseModel
from typing import Optional


class MunicipioResumo(BaseModel):
    cod_municipio: str
    uf: str
    nome_municipio: str
    total_receitas: float
    # Primary investment metric: FUNDEB per enrolled student in municipal network
    fundeb_per_aluno_municipal: Optional[float]
    # Context metric: FUNDEB per capita (total population, kept for reference)
    total_receitas_per_capita: Optional[float]
    ideb_anos_iniciais_2023: Optional[float]
    ideb_anos_finais_2023: Optional[float]


class MunicipioDetalhe(MunicipioResumo):
    ano: int
    populacao: Optional[float]
    mat_municipal_total: Optional[float]
    mat_estadual_total: Optional[float]
    mat_publica_total: Optional[float]
    fundeb_per_aluno_publica: Optional[float]
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
    total_receitas: float
    mat_municipal_total: Optional[float]
    fundeb_per_aluno_municipal: Optional[float]
    total_receitas_per_capita: Optional[float]
    populacao: Optional[float]
    ideb_anos_iniciais_2023: Optional[float]


class CorrelacaoItem(BaseModel):
    cod_municipio: str
    uf: str
    nome_municipio: str
    fundeb_per_aluno_municipal: Optional[float]
    total_receitas_per_capita: Optional[float]
    ideb_anos_iniciais_2023: Optional[float]
    ideb_anos_finais_2023: Optional[float]
    mat_municipal_total: Optional[float]
    populacao: Optional[float]


class EficienciaItem(BaseModel):
    cod_municipio: str
    uf: str
    nome_municipio: str
    populacao: Optional[float]
    mat_municipal_total: Optional[float]
    fundeb_per_aluno_municipal: float
    total_receitas_per_capita: Optional[float]
    ideb_real: float
    ideb_esperado: float
    residuo: float
    score_eficiencia: float


class ResumoDataset(BaseModel):
    total_municipios: int
    total_municipios_com_ideb: int
    total_municipios_sem_matriculas: int
    ufs_disponiveis: int
    soma_total_receitas: float
    # Per-student metrics (primary)
    media_per_aluno_municipal: float
    mediana_per_aluno_municipal: float
    # Per-capita metrics (context)
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
    per_aluno_min: float
    per_aluno_max: float
    per_capita_min: float
    per_capita_max: float
    ideb_min: float
    ideb_max: float


class MediasUF(BaseModel):
    uf: str
    total_municipios: int
    media_per_aluno_municipal: Optional[float]
    media_per_capita: Optional[float]
    media_ideb_iniciais: Optional[float]
    media_ideb_finais: Optional[float]


class MediasUFCompleta(BaseModel):
    uf: str
    total_municipios: int
    soma_receitas: float
    media_per_aluno_municipal: Optional[float]
    mediana_per_aluno_municipal: Optional[float]
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
