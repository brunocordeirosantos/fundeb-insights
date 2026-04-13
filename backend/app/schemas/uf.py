from pydantic import BaseModel
from typing import Optional


class UFResumo(BaseModel):
    uf: str
    nome_estado: str
    regiao: str
    total_municipios: int
    # FUNDEB totals
    fundeb_estadual_total: float       # received by state government (rede estadual)
    fundeb_municipal_total: float      # sum of all municipalities in the state
    fundeb_total_uf: float             # estadual + municipal
    # Enrollment
    mat_estadual_total: Optional[float]
    mat_municipal_total_uf: Optional[float]
    mat_publica_total_uf: Optional[float]
    pct_mat_estadual: Optional[float]  # % of public enrollment managed by state
    # Per-student investment
    fundeb_per_aluno_estadual: Optional[float]
    mediana_per_aluno_municipal: Optional[float]
    razao_per_aluno: Optional[float]   # estadual ÷ mediana municipal (>1 = state invests more)
    # IDEB (from municipal averages)
    media_ideb_iniciais: Optional[float]
    media_ideb_finais: Optional[float]


class UFDetalhe(UFResumo):
    ano_fundeb: int
    cod_ibge_estado: str
    receita_contribuicao: float
    comp_vaaf: float
    comp_vaat: float
    comp_vaar: float
    comp_uniao_total: float
    media_per_aluno_municipal: Optional[float]
    media_per_capita: Optional[float]
    municipios_com_ideb: Optional[int]


class UFRankingItem(BaseModel):
    posicao: int
    uf: str
    nome_estado: str
    regiao: str
    fundeb_per_aluno_estadual: Optional[float]
    mediana_per_aluno_municipal: Optional[float]
    razao_per_aluno: Optional[float]
    mat_estadual_total: Optional[float]
    fundeb_estadual_total: float
    media_ideb_iniciais: Optional[float]


class UFComparativoItem(BaseModel):
    """Side-by-side comparison of state vs municipal investment per student."""
    uf: str
    nome_estado: str
    regiao: str
    fundeb_per_aluno_estadual: Optional[float]
    mediana_per_aluno_municipal: Optional[float]
    razao_per_aluno: Optional[float]
    pct_mat_estadual: Optional[float]
    media_ideb_iniciais: Optional[float]
    media_ideb_finais: Optional[float]
