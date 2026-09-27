"""Persistência dos dados no MongoDB (upsert idempotente)."""

from pymongo import ASCENDING


def create_unique_index(db, collection_name: str, unique_keys: list) -> None:
    """Cria (se ainda não existir) um índice único nas chaves da collection.

    Além de acelerar o upsert, garante no próprio banco que não haverá duplicatas.
    """
    db[collection_name].create_index(
        [(key, ASCENDING) for key in unique_keys], unique=True
    )


def save_to_collection(data: list, collection_name: str, unique_keys: list, db) -> dict:
    """Insere ou atualiza cada documento conforme a chave única.

    Para cada registro monta um filtro com os campos de unique_keys e chama
    update_one(filtro, {"$set": doc}, upsert=True). Assim, rodar de novo
    só atualiza o que já existe, sem duplicar.
    O parâmetro db (vindo de get_database) fica por último para manter a
    assinatura pedida no enunciado nos três primeiros argumentos.
    Retorna um resumo com quantos foram inseridos e quantos já existiam.
    """
    collection = db[collection_name]
    stats = {"inseridos": 0, "ja_existiam": 0, "modificados": 0, "ignorados": 0}

    for doc in data:
        # Registro sem alguma das chaves não dá para identificar -> ignora
        if any(doc.get(key) is None for key in unique_keys):
            stats["ignorados"] += 1
            continue

        filtro = {key: doc[key] for key in unique_keys}
        result = collection.update_one(filtro, {"$set": doc}, upsert=True)

        if result.upserted_id is not None:
            stats["inseridos"] += 1
        else:
            stats["ja_existiam"] += 1
            stats["modificados"] += result.modified_count

    return stats
