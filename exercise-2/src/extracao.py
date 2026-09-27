"""Extração: chamadas HTTP à API não oficial do Cartola FC."""
import logging

import requests

import config

log = logging.getLogger(__name__)


def _get_json(url):
    """GET simples com timeout; levanta exceção em erro HTTP ou de rede."""
    resposta = requests.get(url, headers=config.HEADERS, timeout=config.REQUEST_TIMEOUT)
    resposta.raise_for_status()
    return resposta.json()


def buscar_dados_mercado():
    """Busca /atletas/mercado e também /mercado/status.

    Na API atual, a chave "status" de /atletas/mercado é o dicionário de status
    dos atletas (Provável, Dúvida...), e não o status do mercado. Por isso o
    status do mercado é buscado no endpoint próprio e guardado em "status_mercado".
    """
    log.info("Buscando dados na API...")
    dados = _get_json(config.CARTOLA_API_URL)
    dados["status_mercado"] = _get_json(config.CARTOLA_STATUS_URL)
    log.info(
        "API respondeu: %d clubes, %d atletas.",
        len(dados.get("clubes") or {}),
        len(dados.get("atletas") or []),
    )
    return dados
