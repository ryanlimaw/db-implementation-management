"""ETL do Cartola FC -> MongoDB. Pensado para rodar via cron/Agendador de Tarefas."""
import logging
import sys

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
    try:
        main()
    except Exception:
        # Registra o erro completo e encerra com código != 0 (o cron consegue detectar a falha).
        log.exception("Falha na execução do ETL.")
        sys.exit(1)
