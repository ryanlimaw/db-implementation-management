"""Configurações do coletor, lidas do arquivo .env (com valores padrão)."""

import os
from pathlib import Path

from dotenv import load_dotenv

# O .env fica na raiz do exercise-1 (um nível acima de src/)
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "openf1_data")
MONGO_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", "5000"))

OPENF1_BASE_URL = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Tentativas extras quando a API responde 429 (limite de requisições)
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_WAIT_SECONDS = int(os.getenv("RETRY_WAIT_SECONDS", "5"))

SESSION_KEY = int(os.getenv("SESSION_KEY", "9159"))

# Chaves únicas de cada collection (usadas no upsert e nos índices)
UNIQUE_KEYS = {
    "sessions": ["session_key"],
    "drivers": ["session_key", "driver_number"],
    "laps": ["session_key", "driver_number", "lap_number"],
}
