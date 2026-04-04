-- Dimension: municipalities
CREATE TABLE IF NOT EXISTS dim_municipio (
    cod_municipio   CHAR(7)      PRIMARY KEY,
    nome            VARCHAR(100) NOT NULL,
    uf              CHAR(2)      NOT NULL,
    regiao          VARCHAR(20)  NOT NULL,
    populacao       INTEGER,
    area_km2        NUMERIC(12, 2)
);

-- Dimension: years
CREATE TABLE IF NOT EXISTS dim_ano (
    ano SMALLINT PRIMARY KEY
);

-- Fact: FUNDEB transfers
CREATE TABLE IF NOT EXISTS fato_fundeb (
    id              SERIAL       PRIMARY KEY,
    cod_municipio   CHAR(7)      NOT NULL REFERENCES dim_municipio(cod_municipio),
    ano             SMALLINT     NOT NULL REFERENCES dim_ano(ano),
    valor_total     NUMERIC(18, 2),
    valor_per_capita NUMERIC(12, 2),
    UNIQUE (cod_municipio, ano)
);

-- Fact: IDEB performance
CREATE TABLE IF NOT EXISTS fato_ideb (
    id              SERIAL       PRIMARY KEY,
    cod_municipio   CHAR(7)      NOT NULL REFERENCES dim_municipio(cod_municipio),
    ano             SMALLINT     NOT NULL REFERENCES dim_ano(ano),
    etapa           VARCHAR(20)  NOT NULL, -- 'anos_iniciais' | 'anos_finais'
    nota_ideb       NUMERIC(4, 2),
    UNIQUE (cod_municipio, ano, etapa)
);
