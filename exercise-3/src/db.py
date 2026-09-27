"""Conexão com o MongoDB, carga idempotente e índice 2dsphere."""
from pymongo import GEOSPHERE, MongoClient, ReplaceOne

import config


def conectar():
    cliente = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
    cliente.admin.command("ping")  # falha logo se o Mongo não estiver no ar
    return cliente, cliente[config.MONGO_DB][config.MONGO_COLLECTION]


def criar_indices(colecao):
    # índice geoespacial no campo geometry (GeoJSON)
    colecao.create_index([("geometry", GEOSPHERE)], name="geometry_2dsphere")
    # índice único no CNES, usado pelo upsert
    colecao.create_index("properties.cnes", unique=True, name="cnes_unico")


def salvar_features(colecao, features, lote=1000):
    """Upsert por CNES (ReplaceOne): rodar de novo não duplica, só substitui."""
    inseridos = atualizados = 0
    for i in range(0, len(features), lote):
        ops = [
            ReplaceOne({"properties.cnes": f["properties"]["cnes"]}, f, upsert=True)
            for f in features[i:i + lote]
        ]
        res = colecao.bulk_write(ops, ordered=False)
        inseridos += res.upserted_count
        atualizados += res.matched_count
    return inseridos, atualizados
