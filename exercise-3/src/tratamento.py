"""Limpeza com pandas e conversão para GeoJSON com geopandas/shapely."""
import geopandas as gpd
import pandas as pd

# Retângulo aproximado que cobre o Brasil (inclui ilhas oceânicas)
BRASIL_LAT = (-34.0, 5.5)
BRASIL_LON = (-74.5, -28.5)

# Código IBGE da UF -> sigla (a API só traz o código)
UF_SIGLA = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

COLUNAS = ["cnes", "nome", "uf", "uf_sigla", "ibge", "logradouro", "bairro"]


def para_numero(serie):
    """Texto -> float: troca vírgula por ponto; o que não converter vira NaN."""
    texto = serie.astype("string").str.strip().str.replace(",", ".", regex=False)
    return pd.to_numeric(texto, errors="coerce")


def tratar(registros):
    df = pd.DataFrame(registros)
    stats = {"total": len(df)}

    df["latitude"] = para_numero(df["latitude"])
    df["longitude"] = para_numero(df["longitude"])
    for col in ["cnes", "nome", "uf", "ibge", "logradouro", "bairro"]:
        df[col] = df[col].astype("string").str.strip()

    # motivos de descarte (na ordem em que são testados)
    sem_cnes = df["cnes"].isna() | (df["cnes"] == "")
    nulas = df["latitude"].isna() | df["longitude"].isna()
    zero = (df["latitude"] == 0) & (df["longitude"] == 0)
    fora_faixa = ~df["latitude"].between(-90, 90) | ~df["longitude"].between(-180, 180)
    fora_brasil = ~df["latitude"].between(*BRASIL_LAT) | ~df["longitude"].between(*BRASIL_LON)

    stats["sem_cnes"] = int(sem_cnes.sum())
    stats["coord_nula_ou_invalida"] = int((nulas & ~sem_cnes).sum())
    ruins = sem_cnes | nulas
    stats["coord_zero_zero"] = int((zero & ~ruins).sum())
    ruins |= zero
    stats["fora_da_faixa_valida"] = int((fora_faixa & ~ruins).sum())
    ruins |= fora_faixa
    stats["fora_do_brasil"] = int((fora_brasil & ~ruins).sum())
    ruins |= fora_brasil

    df = df[~ruins].copy()

    # CNES repetido: fica só a primeira ocorrência
    antes = len(df)
    df = df.drop_duplicates(subset="cnes", keep="first")
    stats["cnes_duplicado"] = antes - len(df)

    df["uf_sigla"] = df["uf"].map(UF_SIGLA)

    # Pontos em SIRGAS 2000 (EPSG:4674, datum oficial do Brasil) e
    # conversão para WGS 84 (EPSG:4326), que é o que o 2dsphere do MongoDB usa
    gdf = gpd.GeoDataFrame(
        df[COLUNAS + ["latitude", "longitude"]],
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4674",
    ).to_crs("EPSG:4326")

    stats["validos"] = len(gdf)
    stats["descartados"] = stats["total"] - stats["validos"]
    return gdf, stats


def valor_nativo(v):
    """Converte tipos numpy/pandas para tipos nativos do Python (BSON aceita)."""
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return None
    if hasattr(v, "item"):  # numpy.int64, numpy.float64...
        return v.item()
    return str(v) if not isinstance(v, (int, float, str)) else v


def para_features(gdf):
    """Cada linha vira um Feature GeoJSON; coordinates = [longitude, latitude]."""
    features = []
    for linha in gdf.itertuples(index=False):
        ponto = linha.geometry
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(ponto.x), float(ponto.y)]},
            "properties": {c: valor_nativo(getattr(linha, c)) for c in COLUNAS},
        })
    return features
