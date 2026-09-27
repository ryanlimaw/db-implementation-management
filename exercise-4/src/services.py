"""Consultas usadas pelo app. Toda leitura do MongoDB fica aqui."""

import pandas as pd

from db_utils import get_database


def listar_anos():
    """Anos que aparecem na collection sessions (mais recente primeiro)."""
    anos = get_database().sessions.distinct("year")
    return sorted((a for a in anos if a is not None), reverse=True)


def listar_sessoes(ano, somente_corridas=False):
    """Sessões de um ano, ordenadas por data."""
    filtro = {"year": ano}
    if somente_corridas:
        filtro["session_type"] = "Race"
    projecao = {"_id": 0, "session_key": 1, "session_name": 1, "session_type": 1,
                "country_name": 1, "location": 1, "circuit_short_name": 1, "date_start": 1}
    return list(get_database().sessions.find(filtro, projecao).sort("date_start", 1))


def rotulo_sessao(sessao):
    """Texto legível, ex.: 'Italy – Monza – Race (2023-09-03)'."""
    data = (sessao.get("date_start") or "")[:10]
    return (f"{sessao.get('country_name', '?')} – {sessao.get('circuit_short_name', '?')}"
            f" – {sessao.get('session_name', '?')} ({data})")


def obter_sessao(session_key):
    return get_database().sessions.find_one({"session_key": session_key}, {"_id": 0})


def nome_piloto(piloto):
    """'Charles Leclerc (16) – Ferrari' (a API manda o sobrenome em maiúsculas)."""
    if piloto.get("first_name") and piloto.get("last_name"):
        nome = f"{piloto['first_name']} {piloto['last_name'].title()}"
    else:
        nome = (piloto.get("full_name") or piloto.get("name_acronym") or "?").title()
    equipe = piloto.get("team_name") or "sem equipe"
    return f"{nome} ({piloto['driver_number']}) – {equipe}"


def listar_pilotos(session_key):
    projecao = {"_id": 0, "driver_number": 1, "full_name": 1, "first_name": 1,
                "last_name": 1, "name_acronym": 1, "team_name": 1}
    cursor = get_database().drivers.find({"session_key": session_key}, projecao)
    return list(cursor.sort("driver_number", 1))


def buscar_voltas(session_key, numeros_pilotos):
    """Voltas dos pilotos escolhidos em um DataFrame (inclui voltas sem tempo)."""
    colunas = ["driver_number", "lap_number", "lap_duration", "duration_sector_1",
               "duration_sector_2", "duration_sector_3", "is_pit_out_lap", "date_start"]
    if not numeros_pilotos:
        return pd.DataFrame(columns=colunas)
    filtro = {"session_key": session_key, "driver_number": {"$in": list(numeros_pilotos)}}
    projecao = {"_id": 0, **{c: 1 for c in colunas}}
    docs = get_database().laps.find(filtro, projecao).sort([("driver_number", 1), ("lap_number", 1)])
    return pd.DataFrame(list(docs), columns=colunas)
