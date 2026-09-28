# Exercício 01 — Coletor de dados da OpenF1 para MongoDB

## Objetivo

Script em Python 3 que busca dados da [API OpenF1](https://openf1.org) (sessão, pilotos e voltas de uma `session_key`) e grava no MongoDB, no banco `openf1_data`, nas collections `sessions`, `drivers` e `laps`. O script pode ser executado várias vezes sem duplicar dados (usa `update_one(..., upsert=True)`).

Caso de uso do enunciado: `session_key = 9159`, `meeting_key = 1219`.

> **Observação sobre a sessão 9159:** o enunciado indica 9159 como GP da Itália, mas a API retorna 9159 = Singapore Practice 2 (Marina Bay, 2023-09-15, `meeting_key` 1219); a corrida de Monza 2023 é 9157 (`session_name` "Race", `meeting_key` 1218, 2023-09-03). O padrão do script continua sendo 9159, como pede o enunciado. Para coletar a corrida de Monza:
>
> ```bash
> python src/f1_data_collector.py --session-key 9157
> ```

## Estrutura

```
exercise-1/
├── README.md
├── requirements.txt       # requests, pymongo, python-dotenv
├── .env.example           # modelo de configuração
└── src/
    ├── f1_data_collector.py  # ponto de entrada (main + argparse)
    ├── config.py             # lê o .env e define os valores padrão
    ├── db.py                 # get_database(): conexão com o MongoDB
    ├── api.py                # fetch_data(endpoint, params): GET na OpenF1
    └── storage.py            # save_to_collection(...): upsert nas collections
```

Cada arquivo tem uma responsabilidade só: configuração, conexão, requisição HTTP, persistência e fluxo principal.

## Como configurar

1. Instale as dependências (de preferência num ambiente virtual):

   ```bash
   pip install -r requirements.txt
   ```

2. Copie o `.env.example` para `.env` e ajuste se precisar:

   ```bash
   cp .env.example .env
   ```

   | Variável | Padrão | Para que serve |
   |---|---|---|
   | `MONGO_URI` | `mongodb://localhost:27017` | endereço do MongoDB |
   | `MONGO_DB_NAME` | `openf1_data` | nome do banco |
   | `OPENF1_BASE_URL` | `https://api.openf1.org/v1` | URL base da API |
   | `REQUEST_TIMEOUT` | `30` | timeout (s) de cada requisição |
   | `SESSION_KEY` | `9159` | sessão coletada por padrão |

   Opcionais (têm padrão em `config.py`): `MONGO_TIMEOUT_MS` (5000), `MAX_RETRIES` (3), `RETRY_WAIT_SECONDS` (5).

   Variáveis de ambiente já definidas no terminal têm prioridade sobre o `.env`.

## Como executar

A partir da pasta `exercise-1`:

```bash
python src/f1_data_collector.py                     # usa SESSION_KEY do .env (9159)
python src/f1_data_collector.py --session-key 9158  # outra sessão
```

O fluxo é: conecta no MongoDB (com `ping`) → busca `/sessions` → salva → busca `/drivers` → salva → busca `/laps` → salva. Para cada collection o script mostra quantos documentos foram inseridos e quantos já existiam.

## Como funciona a idempotência

Cada documento é gravado com `update_one(filtro, {"$set": doc}, upsert=True)`, onde o filtro é a chave única da collection:

| Collection | Chave única |
|---|---|
| `sessions` | `session_key` |
| `drivers` | `session_key` + `driver_number` |
| `laps` | `session_key` + `driver_number` + `lap_number` |

Se o documento não existe, ele é inserido (`upserted_id` preenchido); se já existe, é só atualizado. Além disso, o script cria um **índice único** com essas mesmas chaves em cada collection, então o próprio MongoDB impede duplicatas.

## Tratamento de erros

- **API:** toda requisição tem `timeout` e chama `response.raise_for_status()`. Timeout, erro HTTP e erro de conexão são capturados e mostram uma mensagem clara.
- **Consulta sem resultados:** a OpenF1 não devolve lista vazia quando não encontra nada. Ela responde `404` com `{"detail": "No results found."}`. O `fetch_data` trata esse caso como lista vazia. Se a própria sessão não existir, o script avisa `session_key=... não encontrada na API OpenF1` e para. Se só faltarem pilotos ou voltas, ele avisa "Nada para salvar" e continua.
- **Limite de requisições (HTTP 429):** a OpenF1 pode limitar requisições. Nesse caso o script espera alguns segundos e tenta de novo (até `MAX_RETRIES` vezes). Nos nossos testes não recebemos 429.
- **MongoDB:** a conexão usa `serverSelectionTimeoutMS` e um `ping`; erros do `pymongo` (`ServerSelectionTimeoutError`, `PyMongoError`) na conexão ou na gravação são capturados.
- Em qualquer erro o script **não segue em silêncio**: imprime a mensagem e sai com código `1`.

## Testes realizados

Ambiente: Windows 11, Python 3.12, MongoDB **8.0.4** (versão portátil) rodando localmente em `mongodb://localhost:27017`, sem autenticação. Banco `openf1_data` vazio antes do primeiro teste.

### 1. Primeira execução (session_key 9159) — TESTADO E FUNCIONANDO

```bash
python src/f1_data_collector.py
```

Saída (resumo real):

```
'sessions': 1 inserido(s), 0 já existia(m) ...   Total para session_key=9159: 1
'drivers': 20 inserido(s), 0 já existia(m) ...   Total para session_key=9159: 20
'laps': 475 inserido(s), 0 já existia(m) ...     Total para session_key=9159: 475
Coleta finalizada.   (código de saída 0)
```

Contagem no MongoDB depois da execução: `sessions` = 1, `drivers` = 20, `laps` = 475.

### 2. Segunda execução (idempotência) — TESTADO E FUNCIONANDO

Mesmo comando, rodado de novo:

```
'sessions': 0 inserido(s), 1 já existia(m) (0 com alteração) ...   Total: 1
'drivers': 0 inserido(s), 20 já existia(m) (0 com alteração) ...    Total: 20
'laps': 0 inserido(s), 475 já existia(m) (0 com alteração) ...      Total: 475
```

As contagens não aumentaram (continuam 1 / 20 / 475) e todos os registros entraram como "já existia". Os índices únicos foram criados: `session_key_1`, `session_key_1_driver_number_1` e `session_key_1_driver_number_1_lap_number_1`.

### 2b. Corrida de Monza 2023 (session_key 9157), duas execuções — TESTADO E FUNCIONANDO

```bash
python src/f1_data_collector.py --session-key 9157
```

Primeira execução:

```
'sessions': 1 inserido(s), 0 já existia(m) ...   Total para session_key=9157: 1
'drivers': 20 inserido(s), 0 já existia(m) ...   Total para session_key=9157: 20
'laps': 968 inserido(s), 0 já existia(m) ...     Total para session_key=9157: 968
```

Segunda execução (mesmo comando):

```
'sessions': 0 inserido(s), 1 já existia(m) (0 com alteração) ...   Total: 1
'drivers': 0 inserido(s), 20 já existia(m) (0 com alteração) ...    Total: 20
'laps': 0 inserido(s), 968 já existia(m) (0 com alteração) ...      Total: 968
```

As contagens não aumentaram. O documento salvo em `sessions` confirma `session_name` "Race", `circuit_short_name` "Monza" e `meeting_key` 1218.

Totais no banco depois dos testes (9159 + 9157): `sessions` = 2, `drivers` = 40, `laps` = 1443 (475 + 968).

### 3. MongoDB inacessível — TESTADO E FUNCIONANDO

```bash
MONGO_URI="mongodb://localhost:27999" MONGO_TIMEOUT_MS=3000 python src/f1_data_collector.py
```

Saída (início da mensagem):

```
ERRO: não foi possível conectar ao MongoDB: localhost:27999: [WinError 10061] Nenhuma conexão pôde ser feita porque a máquina de destino as recusou ativamente ... Timeout: 3.0s ...
```

Código de saída: `1`.

### 4. Erro HTTP na API — TESTADO E FUNCIONANDO

```bash
OPENF1_BASE_URL="https://api.openf1.org/v1/naoexiste" python src/f1_data_collector.py
```

```
ERRO HTTP ao buscar /sessions: 400 Client Error: Bad Request for url: https://api.openf1.org/v1/naoexiste/sessions?session_key=9159
```

Código de saída: `1`.

### 4b. session_key inexistente — TESTADO E FUNCIONANDO

```bash
python src/f1_data_collector.py --session-key 1
```

```
  0 registro(s) recebido(s).
ERRO: session_key=1 não encontrada na API OpenF1.
```

Código de saída: `1`. Antes dessa correção, o script mostrava `ERRO HTTP ... 404 Not Found`, o que parecia um problema de URL. Também conferi que `fetch_data("laps", {"session_key": 9159, "driver_number": 999})` retorna `[]` em vez de erro.

### 5. Retry em HTTP 429 — NÃO FOI POSSÍVEL TESTAR

A API não devolveu 429 durante os testes, então o trecho de nova tentativa não chegou a ser executado de verdade.

### Observação

No terminal do Windows (Git Bash) os acentos das mensagens apareceram trocados na primeira execução por causa da codificação do console. Rodando com `PYTHONIOENCODING=utf-8` a saída aparece correta. Não afeta os dados gravados.
