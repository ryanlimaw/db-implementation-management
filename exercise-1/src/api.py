"""Requisições HTTP para a API OpenF1."""

import time

import requests

import config


def fetch_data(endpoint: str, params: dict) -> list:
    """Faz um GET em {OPENF1_BASE_URL}/{endpoint} e retorna a lista de registros.

    - usa timeout para não travar se a API não responder;
    - se vier HTTP 429 (muitas requisições), espera um pouco e tenta de novo;
    - qualquer outro erro HTTP vira exceção via raise_for_status().
    """
    url = f"{config.OPENF1_BASE_URL}/{endpoint.strip('/')}"

    for tentativa in range(config.MAX_RETRIES + 1):
        response = requests.get(url, params=params, timeout=config.REQUEST_TIMEOUT)

        if response.status_code == 429 and tentativa < config.MAX_RETRIES:
            espera = config.RETRY_WAIT_SECONDS * (tentativa + 1)
            print(f"  API retornou 429 (limite de requisições). Tentando de novo em {espera}s...")
            time.sleep(espera)
            continue

        response.raise_for_status()
        break

    data = response.json()
    # A API deveria sempre devolver uma lista; se não for, avisa com erro claro
    if not isinstance(data, list):
        raise ValueError(f"Resposta inesperada de {url}: esperado uma lista, veio {type(data).__name__}")
    return data
