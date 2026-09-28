"""ETL do Cartola FC -> MongoDB. Pensado para rodar via cron/Agendador de Tarefas."""
import logging
import sys

import requests
from pymongo.errors import PyMongoError

from carga import processar_e_gravar_dados
from db import conectar_mongodb
from extracao import buscar_dados_mercado

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("cartola_etl")


def main():
    db = conectar_mongodb()
    dados = buscar_dados_mercado()
    processar_e_gravar_dados(db, dados)
    log.info("Finalizado com sucesso.")


if __name__ == "__main__":
    # Em qualquer falha o script para com código != 0 (o cron consegue detectar).
    try:
        main()
    except requests.exceptions.RequestException as erro:
        log.error("Falha ao acessar a API do Cartola: %s", erro)
        sys.exit(1)
    except PyMongoError as erro:
        log.error("Falha no MongoDB: %s", erro)
        sys.exit(1)
    except Exception:
        # Erro inesperado: registra o traceback completo para investigar.
        log.exception("Falha inesperada na execução do ETL.")
        sys.exit(1)
