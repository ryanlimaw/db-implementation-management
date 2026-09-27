"""Exercício 03 - UBS georreferenciadas: coleta -> tratamento -> MongoDB (GeoJSON)."""
import time

import config
from coleta import baixar_ubs
from db import conectar, criar_indices, salvar_features
from tratamento import para_features, tratar
from validacao import validar


def main():
    inicio = time.time()
    print(f"1) Baixando UBS de {config.UBS_API_URL}")
    print(f"   (UBS_MAX_REGISTROS={config.UBS_MAX_REGISTROS}; 0 = base inteira)")
    registros = baixar_ubs()
    print(f"   {len(registros)} registros baixados em {time.time() - inicio:.0f}s")

    print("2) Tratando dados com pandas/geopandas")
    gdf, stats = tratar(registros)
    features = para_features(gdf)
    print(f"   {stats['validos']} válidos / {stats['descartados']} descartados")

    print(f"3) Gravando em {config.MONGO_DB}.{config.MONGO_COLLECTION}")
    cliente, colecao = conectar()
    criar_indices(colecao)
    inseridos, atualizados = salvar_features(colecao, features)
    print(f"   upsert: {inseridos} novos, {atualizados} já existiam (atualizados)")

    validar(colecao, stats)
    cliente.close()
    print(f"\nConcluído em {time.time() - inicio:.0f}s")


if __name__ == "__main__":
    main()
