# Exercício 2 - Coletar e Armazenar Dados do Cartola FC

## Objetivo

Montar um pequeno ETL (Extração, Transformação e Carga) que busca os dados da API não oficial do Cartola FC e grava no MongoDB. O script é modular, trata erros de forma controlada (loga o erro e sai com código diferente de zero) e pode ser agendado no cron (ou no Agendador de Tarefas do Windows).

- Banco: `cartola_fc_db`
- Coleções:
  - `clubes_rodada_atual`: um documento por clube (upsert pelo id do clube)
  - `atletas_rodada_atual`: lista completa de atletas da coleta mais recente
  - `mercado_rodada_atual`: status do mercado da coleta mais recente

## Estrutura do JSON observada (coleta de 27/09/2026)

`GET https://api.cartola.globo.com/atletas/mercado` retornou HTTP 200 com as chaves:

| Chave | Tipo | Conteúdo observado |
|---|---|---|
| `clubes` | objeto (dicionário) | 20 clubes, a chave é o id em texto (`"2305"`) e o valor tem `id`, `nome`, `abreviacao`, `slug`, `apelido`, `nome_fantasia`, `escudos` (`60x60`, `45x45`, `30x30`), `url_editoria`, `disponivel` |
| `posicoes` | objeto | 6 posições (`1` Goleiro, `2` Lateral, `3` Zagueiro, `4` Meia, `5` Atacante, `6` Técnico) |
| `status` | objeto | 5 status **de atleta**: `2` Dúvida, `3` Suspenso, `5` Contundido, `6` Nulo, `7` Provável |
| `atletas` | lista | 779 atletas, com `atleta_id`, `nome`, `apelido`, `foto`, `preco_num`, `variacao_num`, `clube_id`, `posicao_id`, `status_id`, `jogos_num`, `pontos_num`, `media_num`, `scout{...}`, além de `rodada_id`, `slug`, `apelido_abreviado`, `entrou_em_campo`, `craque` |

`GET https://api.cartola.globo.com/mercado/status` retornou HTTP 200 com `rodada_atual` (29), `status_mercado` (1 = aberto), `fechamento{dia, mes, ano, hora, minuto, timestamp}`, `temporada`, `nome_rodada`, `rodada_final`, `times_escalados`, `bola_rolando` e vários limites de ligas.

## Diferenças entre o enunciado e a API atual

1. **Status do mercado**: o enunciado descreve que o objeto `status` de `/atletas/mercado` traz o status do mercado (`rodada_atual`, `status_mercado`, `fechamento`...), mas a resposta atual da API apresenta em `status` apenas o dicionário de status dos atletas (Provável, Dúvida, etc.). O status do mercado de verdade está em `/mercado/status`. Solução: `buscar_dados_mercado()` faz as duas requisições e guarda o retorno de `/mercado/status` em `dados["status_mercado"]`; é esse objeto que vai para `mercado_rodada_atual`.
2. **Campo `aviso`**: o enunciado mostra `aviso` no documento de status, mas a resposta atual de `/mercado/status` não tem esse campo. O documento é gravado com os campos que a API devolve (sem inventar o `aviso`).
3. **Nome do clube**: o enunciado sugere `nome` como o nome do clube, mas a resposta atual traz `nome` e `nome_fantasia` iguais à sigla (ex.: `"FLA"`). O nome por extenso aparece em `apelido` (ex.: `"Flamengo"`). Mantive os campos pedidos no enunciado (`nome`, `abreviacao`, `escudos`, `nome_fantasia`) exatamente como a API manda.
4. **Chave dos clubes**: no JSON os clubes vêm num dicionário cuja chave é o id em texto; cada clube também tem o campo `id` numérico. Uso o `id` numérico como `_id` (igual ao exemplo `"_id": 293`).
5. **Mercado vazio**: na coleta realizada o mercado estava aberto (rodada 29) e vieram 779 atletas. Não peguei o mercado fechado/entressafra, mas o código já trata lista vazia (o `insert_many([])` daria erro, então ele é pulado e fica só o aviso no log).

Não foi preciso header especial (a API respondeu 200 mesmo sem User-Agent), mas o script envia um User-Agent por segurança.

## Estrutura do projeto

```
exercise-2/
├── README.md
├── requirements.txt
├── .env.example
└── src/
    ├── main.py       # orquestração: conectar -> buscar -> processar
    ├── config.py     # leitura do .env
    ├── db.py         # conectar_mongodb()
    ├── extracao.py   # buscar_dados_mercado()
    └── carga.py      # processar_e_gravar_dados() + gravar_clubes/atletas/status
```

## Configuração

```bash
# na raiz do repositório (venv compartilhado)
python -m venv .venv
.venv/Scripts/pip install -r exercise-2/requirements.txt   # Windows
# source .venv/bin/activate && pip install -r exercise-2/requirements.txt   # Linux

cp exercise-2/.env.example exercise-2/.env   # e ajuste se precisar
```

Variáveis do `.env`:

| Variável | Padrão | Uso |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | string de conexão (pode ter usuário/senha) |
| `MONGO_DB_NAME` | `cartola_fc_db` | nome do banco |
| `CARTOLA_API_URL` | `https://api.cartola.globo.com/atletas/mercado` | atletas, clubes, posições |
| `CARTOLA_STATUS_URL` | `https://api.cartola.globo.com/mercado/status` | status do mercado |
| `REQUEST_TIMEOUT` | `30` | timeout das requisições (segundos) |

## Execução

```bash
cd exercise-2
../.venv/Scripts/python.exe src/main.py      # Windows
# ../.venv/bin/python src/main.py            # Linux
```

Exemplo de agendamento no cron (a cada hora):

```
0 * * * * cd /caminho/exercise-2 && ../.venv/bin/python src/main.py >> etl.log 2>&1
```

O `.env` é procurado na pasta `exercise-2/`, então o script funciona mesmo quando o cron roda de outro diretório. Em caso de erro (API fora, HTTP 4xx/5xx, MongoDB indisponível) o traceback vai para o log e o processo sai com código 1.

## Estratégia de gravação por coleção

| Coleção | Estratégia | Por quê |
|---|---|---|
| `clubes_rodada_atual` | `bulk_write` com `UpdateOne({"_id": id}, {"$set": ...}, upsert=True)` | os clubes quase não mudam; o upsert atualiza o que existe e cria o que falta, sem duplicar |
| `atletas_rodada_atual` | `delete_many({})` + `insert_many(atletas)` | a coleção deve refletir só a coleta atual; cada atleta ganha `timestamp_coleta` (ISO 8601, UTC) |
| `mercado_rodada_atual` | `delete_many({})` + `insert_one(status)` | guarda só o status mais recente, com `timestamp_coleta` |

As requisições à API são feitas **antes** de qualquer escrita. Se a API falhar, nada é apagado no banco e os dados da última coleta boa continuam lá.

## Testes realizados

Ambiente: Windows 11, Python 3.12.10, MongoDB 8.0.4 portable local (`mongodb://localhost:27017`, sem autenticação), pymongo 4.18.2, requests 2.34.2. Data da coleta: 27/09/2026 (rodada 29, mercado aberto).

**TESTADO E FUNCIONANDO - 1ª execução** (banco vazio):

```
[INFO] Conectando ao MongoDB...
[INFO] Conectado ao banco 'cartola_fc_db'.
[INFO] Buscando dados na API...
[INFO] API respondeu: 20 clubes, 779 atletas.
[INFO] Gravando dados dos clubes...
[INFO] Clubes: 20 inseridos (upsert), 0 atualizados, 0 sem alteração.
[INFO] Gravando atletas...
[INFO] Atletas: 0 removidos, 779 inseridos.
[INFO] Gravando status...
[INFO] Status: rodada_atual=29, status_mercado=1.
[INFO] Finalizado com sucesso.
```

**TESTADO E FUNCIONANDO - 2ª execução** (logo em seguida):

```
[INFO] Clubes: 0 inseridos (upsert), 0 atualizados, 20 sem alteração.
[INFO] Atletas: 779 removidos, 779 inseridos.
[INFO] Status: rodada_atual=29, status_mercado=1.
[INFO] Finalizado com sucesso.
```

**TESTADO E FUNCIONANDO - contagens depois das duas execuções:**

| Coleção | Documentos |
|---|---|
| `clubes_rodada_atual` | 20 (não duplicou) |
| `atletas_rodada_atual` | 779 (779 `atleta_id` distintos, um único `timestamp_coleta` = o da 2ª execução) |
| `mercado_rodada_atual` | 1 (só o da 2ª execução) |

**TESTADO E FUNCIONANDO - URL inválida** (`CARTOLA_API_URL=https://api.cartola.globo.com/rota-inexistente`): `requests.exceptions.HTTPError: 404 Client Error`, log com `[ERROR] Falha na execução do ETL.`, código de saída 1, dados do banco preservados.

**TESTADO E FUNCIONANDO - MongoDB indisponível** (`MONGO_URI=mongodb://localhost:27999`): `ServerSelectionTimeoutError` (conexão recusada, `serverSelectionTimeoutMS=5000`), log com `[ERROR]`, código de saída 1.

**TESTADO E FUNCIONANDO - dados vazios** (chamando `processar_e_gravar_dados` direto com `clubes={}`, `atletas=[]`, status vazio, num banco temporário apagado depois): sem exceção, só avisos no log e as coleções ficaram com 0 documentos.

**NÃO FOI POSSÍVEL TESTAR** a API de verdade com o mercado fechado ou na entressafra (0 atletas), porque na data da coleta o mercado estava aberto.

Observação: no Git Bash do Windows os acentos dos logs aparecem trocados (problema de codificação do terminal, os dados no MongoDB ficam corretos em UTF-8).

### Exemplos de documentos gravados (reais, resumidos)

`clubes_rodada_atual`:

```json
{
  "_id": 262,
  "abreviacao": "FLA",
  "escudos": {
    "60x60": "https://s3.glbimg.com/v1/AUTH_58d78b787ec34892b5aaa0c7a146155f/clubes_2026/escudos/FLA/60x60.png",
    "45x45": "...", "30x30": "..."
  },
  "nome": "FLA",
  "nome_fantasia": "FLA"
}
```

`atletas_rodada_atual`:

```json
{
  "scout": {"CA": 3, "DE": 67, "FS": 2, "GS": 30, "PC": 1, "SG": 2},
  "jogos_num": 21,
  "atleta_id": 51413,
  "rodada_id": 28,
  "clube_id": 2305,
  "posicao_id": 1,
  "status_id": 7,
  "pontos_num": 10.2,
  "media_num": 3.05,
  "variacao_num": 1.24,
  "preco_num": 6.3,
  "apelido": "Walter",
  "nome": "Walter Leandro Capeloza Artune",
  "foto": "https://s3.glbimg.com/.../clubes_2026/silhuetas/MIR/FORMATO.png",
  "timestamp_coleta": "2026-09-27T23:38:08.183527+00:00"
}
```

`mercado_rodada_atual` (só alguns campos):

```json
{
  "rodada_atual": 29,
  "status_mercado": 1,
  "temporada": 2026,
  "fechamento": {"dia": 7, "mes": 10, "ano": 2026, "hora": 19, "minuto": 29, "timestamp": 1791412140},
  "nome_rodada": "Rodada 29",
  "timestamp_coleta": "2026-09-27T23:38:08.183527+00:00"
}
```
