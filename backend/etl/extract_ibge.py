"""
Extract municipal population data from IBGE API.
Source: https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/2021/variaveis/9324
Output: data/raw/ibge_populacao.csv
"""
import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).parents[2] / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

IBGE_API = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/6579"
    "/periodos/2021/variaveis/9324?localidades=N6[all]"
)


def extract() -> pd.DataFrame:
    response = requests.get(IBGE_API, timeout=60)
    response.raise_for_status()
    data = response.json()

    rows = []
    for result in data[0]["resultados"][0]["series"]:
        cod = result["localidade"]["id"]
        nome = result["localidade"]["nome"]
        pop = list(result["serie"].values())[0]
        rows.append({"cod_municipio": cod, "nome": nome, "populacao": pop})

    df = pd.DataFrame(rows)
    output_path = RAW_DIR / "ibge_populacao.csv"
    df.to_csv(output_path, index=False)
    print(f"[ibge] populacao -> {output_path} ({len(df)} municipios)")
    return df


if __name__ == "__main__":
    extract()
