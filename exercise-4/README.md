# Prática 04 — OpenF1 Data Explorer

## Objetivo

Aplicação em Streamlit que lê (somente leitura) os dados da Fórmula 1 salvos no MongoDB
pelo coletor do exercise-1 e permite:

- escolher um ano e uma sessão (lista montada a partir da collection `sessions`);
- ver os detalhes da sessão (país, circuito, data) em forma de métricas;
- escolher um ou mais pilotos da sessão;
- ver um gráfico de linhas interativo com o tempo de volta (`lap_duration`) por número da volta, uma linha por piloto;
- abrir o expander "Ver tabela de dados" com os dados usados no gráfico.

Fora do escopo (como pedido no enunciado): coleta/alteração de dados, análise preditiva e autenticação.

## Dependência do exercise-1

O app não coleta nada, ele só lê o banco `openf1_data` (collections `sessions`, `drivers` e `laps`).
Antes de abrir o app é preciso rodar o coletor do exercise-1 para as sessões desejadas. Para o
estudo de caso (Monza 2023), a sessão é a **9157**:

```bash
cd exercise-1
python src/f1_data_collector.py --session-key 9157
```

(veja o README do exercise-1 para os detalhes da coleta).

## Observação: sessão 9159 x 9157

O enunciado diz que a sessão 9159 é o GP da Itália de 2023, mas na API real do OpenF1 a sessão
9159 é o **Treino Livre 2 de Singapura (2023)**. A corrida de Monza de 2023 é a sessão **9157**.
Por isso o estudo de caso abaixo usa a 9157. A 9159 continua acessível no app (basta desmarcar
"Mostrar só corridas").

Outro detalhe: os documentos de `sessions` não têm um nome do tipo "Italian Grand Prix" (isso fica
no endpoint `/meetings`, que não foi coletado no exercise-1). Então o app monta um rótulo com os
campos da própria sessão, por exemplo: `Italy – Monza – Race (2023-09-03)`.

## Estrutura

```
exercise-4/
├── README.md
├── requirements.txt
├── .streamlit/
│   ├── secrets-example.toml   # modelo de configuração (versionado)
│   └── secrets.toml           # configuração local (NÃO versionar)
└── src/
    ├── streamlit_app.py       # interface (só UI, nenhuma query aqui)
    ├── services.py            # consultas: listar_anos, listar_sessoes, obter_sessao, listar_pilotos, buscar_voltas
    └── db_utils.py            # conexão com o MongoDB (cacheada com st.cache_resource)
```

## Configuração

A conexão é lida nesta ordem:

1. `st.secrets` → arquivo `exercise-4/.streamlit/secrets.toml`;
2. variáveis de ambiente `MONGO_URI` e `MONGO_DB_NAME`;
3. padrão: `mongodb://localhost:27017` e banco `openf1_data`.

Para criar o arquivo de secrets:

```bash
cd exercise-4
cp .streamlit/secrets-example.toml .streamlit/secrets.toml
```

Conteúdo:

```toml
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB_NAME = "openf1_data"
```

O `secrets.toml` não deve ir para o Git (já está no `.gitignore` da raiz). O Streamlit procura a
pasta `.streamlit/` no diretório de onde o comando é executado, por isso o app deve ser iniciado
de dentro de `exercise-4/`.

## Como executar

```bash
# na raiz do repositório
python -m venv .venv
.venv\Scripts\activate            # Windows (no Linux/Mac: source .venv/bin/activate)
pip install -r exercise-4/requirements.txt

cd exercise-4
streamlit run src/streamlit_app.py
```

O app abre em `http://localhost:8501`.

> **Windows:** o pacote do Streamlit 1.64 tem arquivos com caminho interno muito longo. Se o projeto estiver numa pasta muito funda (ex.: dentro de `OneDrive\Documentos\Faculdade\...`), o `pip install` pode falhar com `WinError 206` (nome de arquivo muito grande). Nesse caso, clone o projeto num caminho mais curto (ex.: `C:\projetos\`) ou [ative o suporte a caminhos longos](https://learn.microsoft.com/windows/win32/fileio/maximum-file-path-limitation).

## Como usar (estudo de caso)

1. Na barra lateral, escolha o ano **2023**.
2. Com "Mostrar só corridas (Race)" marcado, escolha a sessão **Italy – Monza – Race (2023-09-03)**.
3. As métricas mostram País: **Italy**, Circuito: **Monza**, Data: **2023-09-03**.
4. No campo "Pilotos", selecione **Charles Leclerc (16) – Ferrari** e **Carlos Sainz (55) – Ferrari**.
5. O gráfico mostra os tempos de volta: a grande maioria fica entre 85 e 95 segundos, e as paradas
   nos boxes aparecem como picos (volta 21 do Leclerc com 105,8 s e volta 20 do Sainz com 106,8 s,
   ambas marcadas como `is_pit_out_lap = true`).
6. Abra "Ver tabela de dados" para ver as voltas usadas no gráfico.

Voltas com `lap_duration` nulo não entram no gráfico (não dá para plotar um ponto sem valor), mas
continuam na tabela; o app mostra uma legenda com quantas foram descartadas.

## Testes realizados

Ambiente: MongoDB local com as sessões 9157 e 9159 coletadas pelo exercise-1, Streamlit 1.64.0.

**1. Funções de consulta chamadas direto pelo Python — TESTADO E FUNCIONANDO**

- `listar_anos()` → `[2023]`
- `listar_sessoes(2023)` → `Italy – Monza – Race (2023-09-03)` e `Singapore – Singapore – Practice 2 (2023-09-15)`
- `listar_sessoes(2023, somente_corridas=True)` → só a de Monza
- `listar_pilotos(9157)` → 20 pilotos (inclui `Charles Leclerc (16) – Ferrari` e `Carlos Sainz (55) – Ferrari`)
- `buscar_voltas(9157, [16, 55])` → 104 voltas (52 de cada); 2 sem `lap_duration` (volta 52 de ambos)
- Tempos (s): Leclerc mín 85,580 / máx 105,842 / mediana 86,483; Sainz mín 85,501 / máx 106,762 / mediana 86,408
- 100 das 102 voltas com tempo ficam entre 85 e 95 s; as 2 acima são as voltas de saída dos boxes.

**2. Interação com os widgets via `streamlit.testing.v1.AppTest` — TESTADO E FUNCIONANDO**

Script que roda o app, escolhe 2023 → Monza → Leclerc + Sainz e confere o resultado:
métricas `País=Italy`, `Circuito=Monza`, `Data=2023-09-03`; 1 gráfico plotly com 2 linhas
(51 pontos cada); 1 expander "Ver tabela de dados" com dataframe de 104 linhas; mensagem
`st.info` quando nenhum piloto está selecionado; ao desmarcar "Mostrar só corridas" a sessão 9159
aparece e pode ser aberta (Singapore / Practice 2). Nenhuma exceção.

**3. Servidor Streamlit em modo headless — TESTADO E FUNCIONANDO**

`streamlit run src/streamlit_app.py --server.headless true --server.port 8599`:
`/_stcore/health` respondeu `ok` e `/` respondeu HTTP 200. O processo foi encerrado depois.

**4. Uso no Google Chrome (DevTools: Console, Network e Issues) — TESTADO E FUNCIONANDO**

O app rodou com `streamlit run src/streamlit_app.py` e foi aberto no Google Chrome, automatizado com Playwright. O script registrou o console, os erros de JavaScript, as requisições de rede e o painel *Issues* do DevTools (via protocolo do Chrome), passando por: carregamento inicial → Leclerc + Sainz → "Ver tabela de dados" → hover no gráfico → desmarcar "Mostrar só corridas" → sessão 9159 → "Select all" (20 pilotos no gráfico) → voltar para Monza → recarregar a página (F5).

- Console: nenhuma mensagem de erro ou warning. Nenhum erro de JavaScript.
- Rede: 140 respostas, todas HTTP 200. Nenhum 4xx/5xx, nenhum asset ou fonte quebrada, nenhuma requisição pendente.
- Tela: nenhum traceback, nenhum loading infinito. Os screenshots conferem com o estudo de caso: dois tons de azul para Leclerc e Sainz, picos nas voltas 20 e 21.
- Não conferido: zoom e pan do gráfico (ferramentas do Plotly).

**Avisos que aparecem no painel *Issues* do Chrome (não são erros do app):**

| Aviso | Qtde | Origem | Precisa corrigir? |
|---|---|---|---|
| `PerformanceIssue: DocumentCookie` | 58 | JS interno do Streamlit (`index.js`, `loglevel.js`, `getColors.js`) lendo `document.cookie` | Não. É do Streamlit, fora do nosso código. |
| `FormLabelHasNeitherForNorNestedInput` ("No label associated with a form field") | 31 | `<label>` gerados pelo Streamlit (`stWidgetLabel` e `stMetricLabel`) para "Ano", "Sessão", "Pilotos" e as métricas | Não. Nosso código só passa o texto do rótulo. |

Na aba *Network* aparecem também chamadas para `webhooks.fivetran.com` e `data.streamlit.io`. É a coleta de estatísticas de uso do próprio Streamlit (o terminal avisa: *"Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false"*). Não é erro. Se quiser desligar, rode com `--browser.gatherUsageStats false`.

**5. Falhas e estados vazios no navegador — TESTADO E FUNCIONANDO**

Cada caso foi aberto no Chrome com uma configuração diferente, pelas variáveis `MONGO_URI` e `MONGO_DB_NAME`, sem `secrets.toml`:

| Situação | O que o usuário vê |
|---|---|
| MongoDB desligado | "Não foi possível conectar ao MongoDB. Verifique se o servidor está rodando e o MONGO_URI em .streamlit/secrets.toml.", com o erro técnico dentro de "Detalhes técnicos" |
| MongoDB cai com o app aberto (servidor derrubado depois de escolher um piloto) | a mesma mensagem acima na próxima interação |
| Banco vazio | "Nenhuma sessão no banco. Rode antes o coletor do exercise-1." |
| Sessão sem pilotos | "Não há pilotos salvos para essa sessão." |
| Pilotos sem voltas | "Não há voltas salvas para os pilotos selecionados." |

Em nenhum caso apareceu traceback. Antes da auditoria, a mensagem de MongoDB desligado mostrava o erro inteiro do driver (`TopologyDescription`...) direto na tela. Agora esse texto fica dentro de "Detalhes técnicos".
