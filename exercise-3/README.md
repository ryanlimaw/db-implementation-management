# Exercício 03 – Georreferência com MongoDB e GeoJSON

## Objetivo

Baixar dados georreferenciados de uma fonte aberta do Governo Federal (Unidades Básicas de Saúde – UBS),
tratar latitude/longitude com pandas e geopandas, gravar cada unidade como um *Feature* GeoJSON no MongoDB
e criar um índice geoespacial `2dsphere` para permitir consultas por proximidade.

Tecnologias: Python 3.12, requests, pandas, geopandas/shapely, pymongo, python-dotenv e MongoDB 8.0.4
(versão portátil rodando localmente no Windows).

## Fonte dos dados

**Link sugerido no enunciado (desatualizado):**
`http://dados.gov.br/dataset/unidades-basicas-de-saude-ubs/resource/e8a10748-423c-433a-9523-14c1c2eba6cf`

Testei esse link em 27/09/2026: ele redireciona (301) para `https://dados.gov.br/...` e a resposta final é
**HTTP 401** (não autorizado). O portal dados.gov.br mudou de estrutura e a API dele
(`/dados/api/publico/...` e a antiga `/api/3/action/package_show`) também devolve 401 sem token de acesso.
Por isso não usei esse caminho.

**Fonte usada (oficial, Ministério da Saúde):**
API de Dados Abertos do Ministério da Saúde – endpoint de UBS:

```
https://apidadosabertos.saude.gov.br/assistencia-a-saude/unidade-basicas-de-saude
```

Motivos da escolha:

- é do próprio Ministério da Saúde (mesma origem dos dados de UBS que eram publicados no dados.gov.br);
- é pública, sem autenticação, e responde em JSON;
- já traz `latitude` e `longitude` de cada estabelecimento, junto com CNES, nome, UF, código IBGE do município,
  logradouro e bairro;
- é paginada com `limit` e `offset`, com a lista de registros na chave `"ubs"`.

Exemplo de registro bruto da API (repare na vírgula decimal e nas coordenadas como texto):

```json
{"ibge": "260290", "bairro": "PONTE DOS CARVALHOS", "logradouro": "RUA DO CEMITERIO", "cnes": "0000302",
 "uf": "26", "latitude": "-8,21811", "longitude": "-35,22944", "nome": "USF SANTO ESTEVAO"}
```

### Coleta paginada

O `src/coleta.py` percorre a API página por página:

- a API devolve no máximo **1000 registros por requisição** (testei `limit=5000` e `limit=20000` e veio 1000);
- a cada página o `offset` avança e o laço **para quando vem uma página vazia**;
- `timeout` de 60 s, até 3 tentativas por página e uma pausa de 0,3 s entre páginas (para não sobrecarregar a API);
- `UBS_MAX_REGISTROS` no `.env` limita a quantidade; o padrão `0` baixa **a base inteira**.

A base completa tem 46.848 registros e foi baixada em cerca de 30 segundos (47 páginas), então não foi
necessário limitar.

## Tratamento dos dados (`src/tratamento.py`)

1. Os registros viram um `DataFrame` do pandas.
2. `latitude` e `longitude` são convertidas para número: texto → `strip` → troca de `,` por `.` →
   `pd.to_numeric(errors="coerce")`. O que não converte (nulo, vazio, texto inválido) vira `NaN`.
3. São descartados, nessa ordem, e cada motivo é contado:
   - registro sem CNES;
   - latitude ou longitude nula/inválida;
   - coordenada `(0, 0)`;
   - fora da faixa válida (latitude fora de -90..90 ou longitude fora de -180..180);
   - fora de um retângulo que cobre o Brasil (lat -34 a 5,5; lon -74,5 a -28,5, incluindo ilhas oceânicas);
   - CNES repetido (fica só a primeira ocorrência).
4. Com o geopandas, os pontos são criados com `gpd.points_from_xy(longitude, latitude)`.

**Sobre o CRS:** o GeoDataFrame é criado em **EPSG:4674 (SIRGAS 2000)**, que é o referencial geodésico
oficial do Brasil e o usado pelos órgãos do governo. Em seguida é convertido com `to_crs("EPSG:4326")` para
**WGS 84**, que é o sistema que o MongoDB assume para GeoJSON no índice `2dsphere`. Na prática as duas
referências coincidem na casa dos centímetros, então as coordenadas não mudam (dá para ver no exemplo abaixo),
mas deixei explícito para ficar claro de onde vem e para onde vai o dado.

5. Cada linha vira um *Feature* GeoJSON. Os valores são convertidos para tipos nativos do Python
   (nada de `numpy.float64`/`pd.NA` indo para o BSON). Também acrescentei `uf_sigla`
   (a API só traz o código IBGE da UF, ex.: `"26"` → `"PE"`).

## Formato GeoJSON gravado

```json
{
  "type": "Feature",
  "geometry": {"type": "Point", "coordinates": [-35.22944, -8.21811]},
  "properties": {"cnes": "0000302", "nome": "USF SANTO ESTEVAO", "uf": "26", "uf_sigla": "PE",
                 "ibge": "260290", "logradouro": "RUA DO CEMITERIO", "bairro": "PONTE DOS CARVALHOS"}
}
```

Atenção à ordem: no GeoJSON (e no MongoDB) é **`[longitude, latitude]`**, ou seja, primeiro o X (leste/oeste)
e depois o Y (norte/sul). É o contrário do costume de falar "lat, long". No Brasil a longitude é sempre
negativa e bem maior em módulo (entre -74 e -29), o que ajuda a conferir se a ordem está certa.

O campo `ibge` é o código do município no IBGE (a API não traz o nome do município).

## Carga no MongoDB e índices (`src/db.py`)

- Banco `ubs_geo`, coleção `ubs` (configuráveis no `.env`).
- **Carga idempotente com upsert por CNES**: para cada Feature é feito um `ReplaceOne({"properties.cnes": ...},
  feature, upsert=True)`, enviado em lotes de 1000 com `bulk_write`. Escolhi upsert em vez de apagar e inserir
  tudo de novo porque o CNES identifica o estabelecimento de forma única: rodar o script de novo não duplica nada,
  só atualiza os dados, e a coleção nunca fica vazia no meio da carga.
- Índices criados pelo código:
  - `geometry_2dsphere` em `geometry` (índice geoespacial);
  - `cnes_unico` em `properties.cnes` (único, deixa o upsert rápido e impede duplicatas).

## Validação (`src/validacao.py`)

Depois da carga o script mostra: total baixado, válidos, descartados (por motivo), quantidade de documentos na
coleção, lista de índices, um documento de exemplo, as 5 UBS mais próximas da **Praça da Sé (São Paulo)**
usando `$geoNear` (que devolve a distância em metros) e a quantidade de UBS num raio de 2 km usando
`$geoWithin` + `$centerSphere`.

## Estrutura

```
exercise-3/
├── README.md
├── requirements.txt
├── .env.example
└── src/
    ├── main.py         # orquestra: coleta -> tratamento -> MongoDB -> validação
    ├── config.py       # leitura do .env
    ├── coleta.py       # download paginado da API
    ├── tratamento.py   # pandas/geopandas e montagem dos Features GeoJSON
    ├── db.py           # conexão, índices e upsert
    └── validacao.py    # contagens, índices, exemplo e consultas geoespaciais
```

## Como configurar e executar

1. Ter um MongoDB rodando (usei o MongoDB 8.0.4 portátil no Windows, em `mongodb://localhost:27017`, sem
   autenticação). Também funciona com Atlas, basta trocar o `MONGO_URI`.
2. Instalar as dependências (de dentro de `exercise-3`):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows (no Linux/Mac: source .venv/bin/activate)
   pip install -r requirements.txt
   ```

3. Copiar o `.env.example` para `.env` e ajustar se precisar:

   ```bash
   copy .env.example .env         # Windows (no Linux/Mac: cp .env.example .env)
   ```

4. Executar:

   ```bash
   python src/main.py
   ```

Para um teste rápido dá para limitar a coleta, por exemplo `UBS_MAX_REGISTROS=2500` no `.env`.

## Testes realizados

Ambiente: Windows 11, Python 3.12.10, MongoDB 8.0.4 portátil local. Testes feitos em 27/09/2026.

### 1. Link antigo do dados.gov.br – TESTADO E FALHOU

`http://dados.gov.br/dataset/unidades-basicas-de-saude-ubs/resource/e8a10748-423c-433a-9523-14c1c2eba6cf`
→ 301 para HTTPS → **HTTP 401**. A API do novo portal (`https://dados.gov.br/dados/api/publico/conjuntos-dados/unidades-basicas-de-saude-ubs`)
também respondeu 401. Por isso a fonte usada foi a API do Ministério da Saúde.

### 2. Carga limitada (`UBS_MAX_REGISTROS=2500`, banco de teste) – TESTADO E FUNCIONANDO

3 páginas (1000 + 1000 + 500), 2500 registros baixados, 2456 válidos, 44 descartados (coordenada nula),
índices criados e consultas executadas. O banco de teste foi apagado depois.

### 3. Carga completa – TESTADO E FUNCIONANDO

Saída real (resumida, sem as linhas de progresso de cada página). Esta saída é da primeira versão do `main.py`, que conectava ao MongoDB só depois do download. A versão atual conecta primeiro (veja o teste 7).

```
1) Baixando UBS de https://apidadosabertos.saude.gov.br/assistencia-a-saude/unidade-basicas-de-saude
   (UBS_MAX_REGISTROS=0; 0 = base inteira)
   46848 registros baixados em 29s
2) Tratando dados com pandas/geopandas
   44682 válidos / 2166 descartados
3) Gravando em ubs_geo.ubs
   upsert: 44682 novos, 0 já existiam (atualizados)

=== Validação ===
Registros baixados : 46848
Válidos            : 44682
Descartados        : 2166
   - sem_cnes: 0
   - coord_nula_ou_invalida: 2166
   - coord_zero_zero: 0
   - fora_da_faixa_valida: 0
   - fora_do_brasil: 0
   - cnes_duplicado: 0
Documentos na coleção: 44682

Índices da coleção:
   _id_: [('_id', 1)]
   geometry_2dsphere: [('geometry', '2dsphere')]
   cnes_unico: [('properties.cnes', 1)]
```

Os 2166 descartes são todos registros que vieram da API sem latitude/longitude (valor `NaN`). Nenhum registro
válido caiu em `(0,0)`, fora da faixa ou fora do Brasil, e não houve CNES repetido — mas as regras ficam no
código caso a base mude.

Documento de exemplo (`find_one`, sem o `_id`):

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-35.22944, -8.21811]
  },
  "properties": {
    "cnes": "0000302",
    "nome": "USF SANTO ESTEVAO",
    "uf": "26",
    "uf_sigla": "PE",
    "ibge": "260290",
    "logradouro": "RUA DO CEMITERIO",
    "bairro": "PONTE DOS CARVALHOS"
  }
}
```

### 4. Consulta geoespacial ao redor da Praça da Sé (SP) – TESTADO E FUNCIONANDO

Ponto de referência `[-46.6339, -23.5503]` (lon, lat).

```
5 UBS mais próximas da Praça da Sé (SP) [-46.6339, -23.5503]:
        330 m | 2787466 | UBS JARDIM ICARAI BRASILANDIA DR DANIEL ALVES GRANGEIRO | RUA ALMIR DEHAR - BRASILANDIA | [-46.636, -23.54805]
        334 m | 0087297 | GMT | R LUIZ DOS SANTOS CABRAL - JARDIM ANALIA FRANCO | [-46.636, -23.548]
        334 m | 2774828 | AMA UBS JARDIM TRES MARIAS DR MAURICIO ZAMIJOVSKY | RUA BRENO ACCIOLI - VILA SAO FRANCISCO | [-46.636, -23.548]
        334 m | 2789264 | UBS VILA TEREZINHA | RUA DOMINGOS FRANCISCO DE MEDEIROS - VILA TERESINHA | [-46.636, -23.548]
        334 m | 9750371 | ELUDICAR SERVICOS MEDICOS | RUA PROFESSOR CARLOS REIS - PINHEIROS | [-46.636, -23.548]

UBS num raio de 2 km da Praça da Sé ($geoWithin/$centerSphere): 37
```

A consulta funciona (o `$geoNear` usa o índice 2dsphere e devolve a distância), mas o resultado mostra uma
**limitação da própria base**: vários estabelecimentos de bairros diferentes (Brasilândia, Pinheiros,
Vila Teresinha...) aparecem com a mesma coordenada `[-46.636, -23.548]`, que é praticamente o ponto central
do município de São Paulo, e não o endereço real. Contando no banco, 32 dos 5387 registros de SP estão
exatamente nesse ponto. O mesmo acontece em outras cidades (ex.: 96 registros em `[-67.81, -9.975]`, centro de
Rio Branco/AC). Ou seja, parte das coordenadas da fonte é aproximada pelo município. Também aparecem alguns
estabelecimentos que não são UBS propriamente ditas (clínicas particulares), porque é assim que vêm na API.
Não removi esses casos porque são coordenadas válidas dentro do Brasil; só registrei a observação.

### 5. Idempotência (rodar o script duas vezes) – TESTADO E FUNCIONANDO

Na segunda execução:

```
   upsert: 0 novos, 44682 já existiam (atualizados)
Documentos na coleção: 44682
```

A coleção continuou com 44682 documentos, sem duplicar.

### 6. MongoDB Atlas – NÃO FOI POSSÍVEL TESTAR

Só testei com o MongoDB local. Com Atlas deveria bastar trocar o `MONGO_URI`, mas isso não foi testado.

### 7. Falhas e regressão após a auditoria – TESTADO E FUNCIONANDO

Na auditoria, a conexão com o MongoDB passou a ser o primeiro passo. Antes, com o Mongo fora do ar, o script baixava a base inteira (cerca de 30 s) e só então falhava. Os erros esperados agora mostram uma mensagem curta em vez de traceback:

| Situação | Mensagem | Código de saída |
|---|---|---|
| `MONGO_URI=mongodb://localhost:27999` | `ERRO no MongoDB: localhost:27999: [WinError 10061] ...` (logo no passo 1) | 1 |
| `UBS_API_URL=https://apidadosabertos.invalid/x` | 3 tentativas com o motivo e `ERRO: Não foi possível baixar a página offset=0` | 1 |
| API sem registros (simulado substituindo `baixar_ubs` por uma lista vazia) | `ERRO: a API não retornou nenhum registro de UBS` | 1 |

Depois disso rodei a carga completa de novo no banco `ubs_geo`: `46848 registros baixados`, `44682 válidos / 2166 descartados`, `upsert: 0 novos, 44682 já existiam`, índice `geometry_2dsphere` presente e 37 UBS no raio de 2 km da Praça da Sé. São os mesmos números de antes, sem duplicar.
