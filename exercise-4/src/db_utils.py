"""Conexão com o MongoDB (somente leitura).

A string de conexão vem, nesta ordem:
1. st.secrets (arquivo .streamlit/secrets.toml)
2. variável de ambiente MONGO_URI / MONGO_DB_NAME
3. padrão local (mongodb://localhost:27017, banco openf1_data)
"""

import os

import streamlit as st
from pymongo import MongoClient

URI_PADRAO = "mongodb://localhost:27017"
BANCO_PADRAO = "openf1_data"


def _ler_config(chave, padrao):
    """Procura a chave no st.secrets; se não houver secrets, usa o ambiente."""
    try:
        if chave in st.secrets:
            return st.secrets[chave]
    except Exception:
        # Sem arquivo secrets.toml o Streamlit lança erro ao acessar st.secrets
        pass
    return os.getenv(chave, padrao)


@st.cache_resource
def get_client():
    """Cria o MongoClient uma única vez (reaproveitado entre os reruns)."""
    uri = _ler_config("MONGO_URI", URI_PADRAO)
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")  # falha logo se o servidor estiver fora
    return client


def get_database():
    return get_client()[_ler_config("MONGO_DB_NAME", BANCO_PADRAO)]
