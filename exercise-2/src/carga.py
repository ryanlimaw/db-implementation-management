"""Transformação e carga dos dados no MongoDB."""
import logging
from datetime import datetime, timezone

from pymongo.operations import UpdateOne

log = logging.getLogger(__name__)


def _agora_iso():
    """Timestamp da coleta em ISO 8601 (UTC)."""
    return datetime.now(timezone.utc).isoformat()


def gravar_clubes(db, clubes):
    """Upsert de cada clube em clubes_rodada_atual, usando o id do clube como _id."""
    log.info("Gravando dados dos clubes...")
    operacoes = []
    for chave, clube in (clubes or {}).items():
        clube_id = int(clube.get("id", chave))  # a chave do dicionário também é o id
        documento = {
            "nome": clube.get("nome"),
            "abreviacao": clube.get("abreviacao"),
            "escudos": clube.get("escudos"),
            "nome_fantasia": clube.get("nome_fantasia"),
        }
        operacoes.append(UpdateOne({"_id": clube_id}, {"$set": documento}, upsert=True))

    if not operacoes:
        log.warning("Nenhum clube retornado pela API; nada a gravar.")
        return
    resultado = db.clubes_rodada_atual.bulk_write(operacoes)
    log.info(
        "Clubes: %d inseridos (upsert), %d atualizados, %d sem alteração.",
        resultado.upserted_count,
        resultado.modified_count,
        resultado.matched_count - resultado.modified_count,
    )


def gravar_atletas(db, atletas, timestamp):
    """Substitui a coleção atletas_rodada_atual pela lista da coleta atual."""
    log.info("Gravando atletas...")
    atletas = atletas or []
    for atleta in atletas:
        atleta["timestamp_coleta"] = timestamp

    removidos = db.atletas_rodada_atual.delete_many({}).deleted_count
    # insert_many([]) gera erro no pymongo, então só insere se houver atletas.
    if atletas:
        db.atletas_rodada_atual.insert_many(atletas)
    else:
        log.warning("A API retornou 0 atletas (mercado fechado/entressafra?). Coleção ficou vazia.")
    log.info("Atletas: %d removidos, %d inseridos.", removidos, len(atletas))


def gravar_status(db, status, timestamp):
    """Mantém em mercado_rodada_atual apenas o status mais recente."""
    log.info("Gravando status...")
    if not status:
        log.warning("Status do mercado vazio; nada a gravar.")
        return
    documento = dict(status)
    documento["timestamp_coleta"] = timestamp
    db.mercado_rodada_atual.delete_many({})
    db.mercado_rodada_atual.insert_one(documento)
    log.info(
        "Status: rodada_atual=%s, status_mercado=%s.",
        documento.get("rodada_atual"),
        documento.get("status_mercado"),
    )


def processar_e_gravar_dados(db, dados_mercado):
    """Orquestra a gravação das três coleções com o mesmo timestamp de coleta."""
    timestamp = _agora_iso()
    gravar_clubes(db, dados_mercado.get("clubes"))
    gravar_atletas(db, dados_mercado.get("atletas"), timestamp)
    gravar_status(db, dados_mercado.get("status_mercado"), timestamp)
