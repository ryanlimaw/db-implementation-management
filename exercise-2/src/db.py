"""Conexão com o MongoDB."""
import logging

from pymongo import MongoClient

import config

log = logging.getLogger(__name__)


def conectar_mongodb():
    """Conecta usando as credenciais do ambiente e retorna o objeto do banco."""
    log.info("Conectando ao MongoDB...")
    cliente = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
    # O MongoClient é "preguiçoso"; o ping força a conexão e já falha aqui se o servidor não estiver no ar.
    cliente.admin.command("ping")
    log.info("Conectado ao banco '%s'.", config.MONGO_DB_NAME)
    return cliente[config.MONGO_DB_NAME]
