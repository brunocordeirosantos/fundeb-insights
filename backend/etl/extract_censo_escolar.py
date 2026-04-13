"""
Extract municipal enrollment data from INEP Censo Escolar (Sinopse Estatística).
Source: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/educacao-basica

Output:
    data/raw/censo_escolar_<year>.zip
    data/processed/matriculas_municipios_<year>.csv

Columns produced (one row per municipality):
    ano_censo              — year of the Censo Escolar
    cod_municipio          — 7-digit IBGE code
    uf                     — state abbreviation
    nome_municipio         — municipality name
    mat_federal_total      — enrollments in federal schools (urbana + rural)
    mat_estadual_total     — enrollments in state schools (urbana + rural)
    mat_municipal_total    — enrollments in municipal schools (urbana + rural)
    mat_privada_total      — enrollments in private schools (urbana + rural)
    mat_publica_total      — federal + estadual + municipal (all public networks)
    mat_total              — all networks combined

Key metric for FUNDEB analysis:
    mat_municipal_total  →  denominator for fundeb_per_aluno_municipal
        The municipal FUNDEB share finances municipal schools directly.
        Using this as the denominator gives the true per-student investment
        and avoids distortion from municipalities where the state absorbed
        most enrollment into the rede estadual.

Sheet parsed: '1.2' (Matrículas por Localização e Dependência Administrativa por Município)
Column layout (0-indexed, fixed across 2022/2023):
    col 0  Região Geográfica
    col 1  Unidade da Federação
    col 2  Município
    col 3  Código do Município  ← 7-digit IBGE code
    col 4  Total (all networks, all locations)
    col 5  Urbana Total
    col 6  Urbana Federal
    col 7  Urbana Estadual
    col 8  Urbana Municipal
    col 9  Urbana Privada
    col 10 Rural Total
    col 11 Rural Federal
    col 12 Rural Estadual
    col 13 Rural Municipal
    col 14 Rural Privada

NOTE: If the download fails (INEP URLs change occasionally), download the ZIP manually
from the link above, save to data/raw/censo_escolar_<year>.zip, and re-run.
"""

import io
import sys
import zipfile

import pandas as pd
import requests
import urllib3
from pathlib import Path

# Windows console may default to cp1252; force UTF-8 for filenames with accents
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RAW_DIR = Path(__file__).parents[2] / "data" / "raw"
PROCESSED_DIR = Path(__file__).parents[2] / "data" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

CENSO_URLS: dict[int, str] = {
    2023: (
        "https://download.inep.gov.br/dados_abertos/sinopses_estatisticas"
        "/sinopses_estatisticas_censo_escolar_2023.zip"
    ),
    2022: (
        "https://download.inep.gov.br/dados_abertos/sinopses_estatisticas"
        "/sinopses_estatisticas_censo_escolar_2022.zip"
    ),
}

# Sheet '1.2': Matrículas por Localização e Dependência Administrativa
SHEET_NAME = "1.2"
DATA_START_ROW = 9  # first row with actual data (row 9 = Brasil total, row 12+ = municipalities)

# Fixed column indices in the sheet
COL_REGIAO = 0
COL_UF = 1
COL_MUNICIPIO = 2
COL_COD = 3
COL_TOTAL = 4
COL_URB_FEDERAL = 6
COL_URB_ESTADUAL = 7
COL_URB_MUNICIPAL = 8
COL_URB_PRIVADA = 9
COL_RUR_FEDERAL = 11
COL_RUR_ESTADUAL = 12
COL_RUR_MUNICIPAL = 13
COL_RUR_PRIVADA = 14


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

def extract(year: int) -> Path:
    """Download sinopse ZIP from INEP. Skips if file already exists."""
    raw_zip = RAW_DIR / f"censo_escolar_{year}.zip"

    if raw_zip.exists():
        print(f"[censo] raw zip ja existe -> {raw_zip}")
        return raw_zip

    if year not in CENSO_URLS:
        raise ValueError(
            f"Ano {year} nao mapeado. Adicione a URL em CENSO_URLS ou baixe "
            f"manualmente e salve em {raw_zip}."
        )

    url = CENSO_URLS[year]
    print(f"[censo] baixando {url} ...")
    response = requests.get(url, timeout=120, verify=False)
    response.raise_for_status()

    raw_zip.write_bytes(response.content)
    size_mb = len(response.content) / 1024 / 1024
    print(f"[censo] raw zip -> {raw_zip} ({size_mb:.1f} MB)")
    return raw_zip


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def _find_xlsx(zf: zipfile.ZipFile) -> str:
    """Return the first .xlsx member in the ZIP."""
    xlsx_files = [f for f in zf.namelist() if f.lower().endswith(".xlsx")]
    if not xlsx_files:
        raise FileNotFoundError(f"Nenhum .xlsx encontrado no ZIP. Membros: {zf.namelist()}")
    return xlsx_files[0]


def _to_int(value: str) -> int:
    """Convert string cell to int; '-', empty, or non-numeric → 0."""
    v = str(value).strip()
    if v in ("-", "", "nan", "–"):
        return 0
    try:
        return int(float(v))
    except ValueError:
        return 0


def transform(raw_zip: Path, year: int) -> pd.DataFrame:
    """
    Parse sheet '1.2' from the sinopse XLSX.

    Municipality rows are identified by having a 7-digit numeric code in col 3.
    All other rows (region totals, state totals) are discarded.
    """
    with zipfile.ZipFile(raw_zip, "r") as zf:
        xlsx_member = _find_xlsx(zf)
        print(f"[censo] lendo {xlsx_member} ...")
        with zf.open(xlsx_member) as f:
            xls = pd.ExcelFile(io.BytesIO(f.read()))

    print(f"[censo] sheet selecionada: '{SHEET_NAME}'")
    df_raw = pd.read_excel(
        xls, sheet_name=SHEET_NAME, header=None, dtype=str
    )

    rows = []
    for _, row in df_raw.iterrows():
        cod = str(row.iloc[COL_COD]).strip().replace(".0", "")

        # Municipality rows have a 7-digit numeric IBGE code
        if len(cod) != 7 or not cod.isnumeric():
            continue

        uf_val = str(row.iloc[COL_UF]).strip()
        nome_val = str(row.iloc[COL_MUNICIPIO]).strip().title()

        fed = _to_int(row.iloc[COL_URB_FEDERAL]) + _to_int(row.iloc[COL_RUR_FEDERAL])
        est = _to_int(row.iloc[COL_URB_ESTADUAL]) + _to_int(row.iloc[COL_RUR_ESTADUAL])
        mun = _to_int(row.iloc[COL_URB_MUNICIPAL]) + _to_int(row.iloc[COL_RUR_MUNICIPAL])
        priv = _to_int(row.iloc[COL_URB_PRIVADA]) + _to_int(row.iloc[COL_RUR_PRIVADA])
        total = _to_int(row.iloc[COL_TOTAL])

        rows.append({
            "cod_municipio": cod,
            "uf": uf_val,
            "nome_municipio": nome_val,
            "mat_federal_total": fed,
            "mat_estadual_total": est,
            "mat_municipal_total": mun,
            "mat_privada_total": priv,
            "mat_publica_total": fed + est + mun,
            "mat_total": total,
        })

    df = pd.DataFrame(rows)
    df.insert(0, "ano_censo", year)
    df = df.reset_index(drop=True)

    print(f"[censo] municipios parseados: {len(df):,}")
    return df


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load(df: pd.DataFrame, year: int) -> Path:
    out_path = PROCESSED_DIR / f"matriculas_municipios_{year}.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[censo] processed -> {out_path} ({len(df):,} municipios)")
    return out_path


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run(year: int) -> pd.DataFrame:
    raw_zip = extract(year)
    df = transform(raw_zip, year)
    load(df, year)
    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
    df = run(year)

    print("\n=== COLUNAS FINAIS ===")
    for col in df.columns:
        non_null = (df[col] != 0).sum() if df[col].dtype in ("int64", "float64") else df[col].notna().sum()
        print(f"  {col:<30} {non_null:,} registros com valor > 0")

    print("\n=== AMOSTRA (5 linhas) ===")
    print(df.head(5).to_string())

    print("\n=== ESTATISTICAS (rede municipal) ===")
    col = df["mat_municipal_total"]
    print(f"  Municipios com matriculas:  {(col > 0).sum():,}")
    print(f"  Total matriculas municipal: {col.sum():,.0f}")
    print(f"  Media por municipio:        {col.mean():,.0f}")
    print(f"  Minimo:                     {col.min():,.0f}")
    print(f"  Maximo:                     {col.max():,.0f}")

    print("\n=== DISTRIBUICAO ENTRE REDES (Brasil) ===")
    for rede in ["federal", "estadual", "municipal", "privada"]:
        total = df[f"mat_{rede}_total"].sum()
        pct = total / df["mat_total"].sum() * 100
        print(f"  {rede:<12} {total:>12,.0f}  ({pct:.1f}%)")
