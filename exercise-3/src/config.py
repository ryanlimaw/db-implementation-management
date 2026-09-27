"""Configurações lidas do .env (com valores padrão)."""
import os
from pathlib import Path

from dotenv import load_dotenv

# .env fica na raiz do exercise-3
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "ubs_geo")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "ubs")

UBS_API_URL = os.getenv(
    "UBS_API_URL",
    "https://apidadosabertos.saude.gov.br/assistencia-a-saude/unidade-basicas-de-saude",
)
UBS_PAGE_SIZE = int(os.getenv("UBS_PAGE_SIZE", "1000"))
UBS_MAX_REGISTROS = int(os.getenv("UBS_MAX_REGISTROS", "0"))  # 0 = tudo
UBS_PAUSA = float(os.getenv("UBS_PAUSA", "0.3"))
