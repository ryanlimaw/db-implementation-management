"""Exercício 03 - UBS georreferenciadas: coleta -> tratamento -> MongoDB (GeoJSON)."""
import sys
import time

from pymongo.errors import PyMongoError

import config
from coleta import baixar_ubs
from db import conectar, criar_indices, salvar_features
from tratamento import para_features, tratar
from validacao import validar


def main():
    inicio = time.time()
    # Conecta primeiro: se o Mongo estiver fora, falha na hora (e não depois do download)
    print(f"1) Conectando ao MongoDB ({config.MONGO_DB}.{config.MONGO_COLLECTION})")
    cliente, colecao = conectar()

    print(f"2) Baixando UBS de {config.UBS_API_URL}")
    print(f"   (UBS_MAX_REGISTROS={config.UBS_MAX_REGISTROS}; 0 = base inteira)")
    registros = baixar_ubs()
    print(f"   {len(registros)} registros baixados em {time.time() - inicio:.0f}s")
    if not registros:
        raise RuntimeError("a API não retornou nenhum registro de UBS")

    print("3) Tratando dados com pandas/geopandas")
    gdf, stats = tratar(registros)
    features = para_features(gdf)
    print(f"   {stats['validos']} válidos / {stats['descartados']} descartados")

    print("4) Gravando no MongoDB")
    criar_indices(colecao)
    inseridos, atualizados = salvar_features(colecao, features)
    print(f"   upsert: {inseridos} novos, {atualizados} já existiam (atualizados)")

    validar(colecao, stats)
    cliente.close()
    print(f"\nConcluído em {time.time() - inicio:.0f}s")


if __name__ == "__main__":
    try:
        main()
    except PyMongoError as erro:
        print(f"\nERRO no MongoDB: {erro}")
        sys.exit(1)
    except RuntimeError as erro:
        print(f"\nERRO: {erro}")
        sys.exit(1)
