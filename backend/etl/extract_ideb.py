"""
Extract IDEB data from INEP.
Source: https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb/resultados
Output: data/raw/ideb_municipios_<year>.csv
"""
import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# TODO: replace with actual INEP download URLs per edition
IDEB_URLS: dict[int, str] = {
    # 2021: "https://...",
    # 2023: "https://...",
}


def extract(year: int) -> pd.DataFrame:
    url = IDEB_URLS[year]
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    output_path = RAW_DIR / f"ideb_municipios_{year}.xlsx"
    output_path.write_bytes(response.content)
    print(f"[ideb] {year} -> {output_path}")

    return pd.read_excel(output_path, skiprows=9)


if __name__ == "__main__":
    for year in IDEB_URLS:
        extract(year)
