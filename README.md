# Implementação e Gerenciamento de Bancos de Dados NoSQL

Atividades práticas da disciplina de Bancos de Dados NoSQL. Os exercícios 1 a 4 usam Python e MongoDB. O 5 é uma lista de comandos Redis.

| # | Atividade | O que faz |
|---|---|---|
| 1 | [Coletor OpenF1](exercise-1/README.md) | Busca sessões, pilotos e voltas na API OpenF1 e grava no banco `openf1_data` com `update_one(..., upsert=True)`, sem duplicar ao rodar de novo. |
| 2 | [ETL Cartola FC](exercise-2/README.md) | Extrai clubes, atletas e status do mercado da API do Cartola e grava no banco `cartola_fc_db`: upsert nos clubes e substituição da coleta anterior nos atletas e no status. |
| 3 | [UBS com GeoJSON](exercise-3/README.md) | Baixa as UBS da API de dados abertos do Ministério da Saúde, trata as coordenadas com pandas/geopandas e grava como `Feature` GeoJSON, com índice `2dsphere`. |
| 4 | [OpenF1 Data Explorer](exercise-4/README.md) | App em Streamlit que só lê os dados do exercício 1: escolhe ano, sessão e pilotos e mostra um gráfico de tempo de volta. |
| 5 | [Lista 01 — Redis](exercise-5/README.md) | Os 20 exercícios (strings, hashes, lists, sets, sorted sets, pub/sub, transações e administração) com a saída real de cada comando em [respostas.md](exercise-5/respostas.md). |

## Estrutura

```text
db-implementation-management/
├── exercise-1/   # coletor OpenF1
├── exercise-2/   # ETL Cartola FC
├── exercise-3/   # UBS + GeoJSON
├── exercise-4/   # Streamlit (depende dos dados do exercise-1)
└── exercise-5/   # Redis
```

Cada pasta tem seu próprio `README.md`, `requirements.txt` e um exemplo de configuração (`.env.example` ou `secrets-example.toml`). Os arquivos com credenciais (`.env` e `.streamlit/secrets.toml`) ficam fora do Git.

## Como rodar

Requisitos: Python 3.9+ e um MongoDB acessível (local ou Atlas). O exercício 5 também precisa de um Redis.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate  |  Linux/Mac: source .venv/bin/activate
pip install -r exercise-1/requirements.txt   # repita para o exercício que for rodar
```

Depois é só copiar o `.env.example` do exercício para `.env`, ajustar a `MONGO_URI` e seguir o README da pasta.

Ordem sugerida: rodar o **exercise-1** antes do **exercise-4**, porque o app só lê o que o coletor gravou.

No Windows, clone o repositório num caminho curto (ex.: `C:\projetos\`). O Streamlit 1.64 tem arquivos com caminho interno muito longo, e numa pasta muito funda o `pip install` do exercício 4 falha com `WinError 206`.

## Observações importantes

- **Sessão 9159:** o enunciado do exercício 1 diz que a sessão 9159 é o GP da Itália de 2023. A API OpenF1 retorna 9159 como *Singapore – Practice 2*. A corrida de Monza em 2023 é a **9157**. O coletor continua com 9159 como padrão, como pede o enunciado, mas também coletei a 9157, que é a sessão usada no estudo de caso do exercício 4.
- **Cartola FC:** na API atual, o campo `status` de `/atletas/mercado` traz os status dos atletas (Provável, Dúvida...) e não o status do mercado. O status do mercado foi buscado em `/mercado/status`. Os detalhes estão no README do exercício 2.
- **UBS:** o link antigo do dados.gov.br citado no enunciado não abre mais (retorna 401). Usei a API oficial de dados abertos do Ministério da Saúde. Os detalhes estão no README do exercício 3.

## Ambiente de teste

Todos os testes descritos nos READMEs rodaram em 27/09/2026 no Windows 11, com Python 3.12.10, MongoDB Community 8.0.4 local (versão portátil em zip) e Redis 7.4.2 (port para Windows). Cada README tem uma seção **Testes realizados**. Nela, cada item está marcado como *TESTADO E FUNCIONANDO*, *TESTADO E FALHOU* ou *NÃO FOI POSSÍVEL TESTAR*, com os números obtidos de verdade.
