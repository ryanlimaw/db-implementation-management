"""Conexão com o MongoDB."""

from pymongo import MongoClient
from pymongo.errors import PyMongoError

import config


def get_database():
    """Conecta no MongoDB usando MONGO_URI do .env e retorna o objeto db.

    Faz um 'ping' logo de cara para descobrir na hora se o servidor está
    inacessível, em vez de só falhar na primeira escrita.
    Lança PyMongoError (ex.: ServerSelectionTimeoutError) se não conectar.
    """
    client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=config.MONGO_TIMEOUT_MS)
    try:
        client.admin.command("ping")
    except PyMongoError:
        client.close()
        raise
    return client[config.MONGO_DB_NAME]
