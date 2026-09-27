"""Conferências depois da carga: contagens, índices e consulta geoespacial."""
import json

# Ponto de referência: Praça da Sé, São Paulo (lon, lat)
PRACA_DA_SE = [-46.6339, -23.5503]


def validar(colecao, stats):
    print("\n=== Validação ===")
    print(f"Registros baixados : {stats['total']}")
    print(f"Válidos            : {stats['validos']}")
    print(f"Descartados        : {stats['descartados']}")
    for k in ["sem_cnes", "coord_nula_ou_invalida", "coord_zero_zero",
              "fora_da_faixa_valida", "fora_do_brasil", "cnes_duplicado"]:
        print(f"   - {k}: {stats[k]}")
    print(f"Documentos na coleção: {colecao.count_documents({})}")

    print("\nÍndices da coleção:")
    for nome, info in colecao.index_information().items():
        print(f"   {nome}: {info['key']}")

    print("\nExemplo de documento:")
    doc = colecao.find_one({}, {"_id": 0})
    print(json.dumps(doc, ensure_ascii=False, indent=2))

    # $geoNear precisa do índice 2dsphere e devolve a distância em metros
    print(f"\n5 UBS mais próximas da Praça da Sé (SP) {PRACA_DA_SE}:")
    pipeline = [
        {"$geoNear": {
            "near": {"type": "Point", "coordinates": PRACA_DA_SE},
            "distanceField": "distancia_m",
            "spherical": True,
        }},
        {"$limit": 5},
        {"$project": {"_id": 0, "properties.cnes": 1, "properties.nome": 1,
                      "properties.logradouro": 1, "properties.bairro": 1,
                      "geometry.coordinates": 1, "distancia_m": 1}},
    ]
    for d in colecao.aggregate(pipeline):
        p = d["properties"]
        print(f"   {d['distancia_m']:8.0f} m | {p['cnes']} | {p['nome']} | "
              f"{p.get('logradouro')} - {p.get('bairro')} | {d['geometry']['coordinates']}")

    # $geoWithin + $centerSphere: raio em radianos (km / raio da Terra 6378.1 km)
    raio_km = 2
    qtd = colecao.count_documents({"geometry": {"$geoWithin": {
        "$centerSphere": [PRACA_DA_SE, raio_km / 6378.1]}}})
    print(f"\nUBS num raio de {raio_km} km da Praça da Sé ($geoWithin/$centerSphere): {qtd}")
