"""Coletor de dados da API OpenF1 para MongoDB.

Busca a sessão, os pilotos e as voltas de uma session_key e grava nas
collections sessions, drivers e laps do banco openf1_data, usando upsert
(pode rodar várias vezes sem duplicar dados).

Uso:
    python src/f1_data_collector.py                  # usa SESSION_KEY do .env (padrão 9159)
    python src/f1_data_collector.py --session-key 9158
"""

import argparse
import sys

import requests
from pymongo.errors import PyMongoError

import config
from api import fetch_data
from db import get_database
from storage import create_unique_index, save_to_collection

# Ordem da coleta: (endpoint da API, collection de destino)
ENDPOINTS = [
    ("sessions", "sessions"),
    ("drivers", "drivers"),
    ("laps", "laps"),
]


def parse_args():
    """Lê os argumentos de linha de comando (só a session_key, por enquanto)."""
    parser = argparse.ArgumentParser(description="Coleta dados da OpenF1 e salva no MongoDB.")
    parser.add_argument(
        "--session-key",
        type=int,
        default=config.SESSION_KEY,
        help=f"session_key da OpenF1 (padrão: {config.SESSION_KEY})",
    )
    return parser.parse_args()


def main():
    """Fluxo principal: conecta, busca sessão/pilotos/voltas e salva cada conjunto."""
    args = parse_args()
    params = {"session_key": args.session_key}

    # 1) Conexão com o MongoDB
    print(f"Conectando ao MongoDB ({config.MONGO_URI}) ...")
    try:
        db = get_database()
    except PyMongoError as e:
        print(f"ERRO: não foi possível conectar ao MongoDB: {e}")
        sys.exit(1)
    print(f"Conectado. Banco: {db.name}")

    # 2) Para cada endpoint: busca na API e salva na collection
    for endpoint, collection_name in ENDPOINTS:
        unique_keys = config.UNIQUE_KEYS[collection_name]
        print(f"\nBuscando /{endpoint} (session_key={args.session_key}) ...")

        try:
            data = fetch_data(endpoint, params)
        except requests.exceptions.Timeout:
            print(f"ERRO: a API demorou mais de {config.REQUEST_TIMEOUT}s para responder em /{endpoint}.")
            sys.exit(1)
        except requests.exceptions.HTTPError as e:
            print(f"ERRO HTTP ao buscar /{endpoint}: {e}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            print(f"ERRO de conexão com a API em /{endpoint}: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"ERRO ao ler a resposta de /{endpoint}: {e}")
            sys.exit(1)

        print(f"  {len(data)} registro(s) recebido(s).")
        if not data:
            # Sessão sem dados nesse endpoint: não é erro, só avisa
            print("  Nada para salvar.")
            continue

        try:
            create_unique_index(db, collection_name, unique_keys)
            stats = save_to_collection(data, collection_name, unique_keys, db)
            total = db[collection_name].count_documents({"session_key": args.session_key})
        except PyMongoError as e:
            print(f"ERRO ao salvar em '{collection_name}': {e}")
            sys.exit(1)

        print(
            f"  '{collection_name}': {stats['inseridos']} inserido(s), "
            f"{stats['ja_existiam']} já existia(m) ({stats['modificados']} com alteração), "
            f"{stats['ignorados']} ignorado(s)."
        )
        print(f"  Total na collection para session_key={args.session_key}: {total}")

    print("\nColeta finalizada.")


if __name__ == "__main__":
    main()
