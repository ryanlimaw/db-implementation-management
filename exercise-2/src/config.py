"""Leitura das configurações a partir do arquivo .env / variáveis de ambiente."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Procura o .env na pasta do exercício (um nível acima de src/),
# assim o script funciona mesmo quando chamado de outro diretório (ex.: cron).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "cartola_fc_db")

CARTOLA_API_URL = os.getenv("CARTOLA_API_URL", "https://api.cartola.globo.com/atletas/mercado")
CARTOLA_STATUS_URL = os.getenv("CARTOLA_STATUS_URL", "https://api.cartola.globo.com/mercado/status")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Algumas APIs recusam requisições sem User-Agent, então enviamos um explícito.
HEADERS = {"User-Agent": "Mozilla/5.0 (cartola-etl; trabalho academico)"}
