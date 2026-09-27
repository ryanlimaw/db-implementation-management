# Exercício 5 — Lista 01: Exercícios com o Redis

Resolução da **Lista 01 – Exercícios com o REDIS (Práticas de Laboratório)**, Profº Ricardo Roberto de Lima.

As respostas completas (enunciado, comando, saída real e explicação de cada exercício) estão em **[respostas.md](respostas.md)**.

## O que a lista cobre

| Parte | Tipo / tema | Exercícios | Comandos principais |
|---|---|---|---|
| 1 | Strings | 01–04 | `SET`, `GET`, `MSET`, `MGET`, `SETEX`, `TTL`, `INCR`, `INCRBY`, `DECRBY` |
| 2 | Hashes | 05–07 | `HSET`, `HGET`, `HGETALL`, `HINCRBY`, `HKEYS` |
| 3 | Lists | 08–10 | `RPUSH`, `LPOP`, `LRANGE` |
| 4 | Sets | 11–13 | `SADD`, `SCARD`, `SINTER`, `SISMEMBER` |
| 5 | Sorted Sets | 14–16 | `ZADD`, `ZREVRANGE ... WITHSCORES`, `ZINCRBY`, `ZREVRANK` |
| 6 | Pub/Sub, Transações e Administração | 17–20 | `SUBSCRIBE`, `PUBLISH`, `MULTI`/`EXEC`, `EXISTS`, `RENAME`, `DEL`, `INFO memory`, `FLUSHDB` |

## Como foi executado

- Servidor: **Redis 7.4.2** (port para Windows, github.com/redis-windows), rodando em `localhost:6379`.
- Cliente: `redis-cli` da mesma distribuição, com `--no-raw` para as respostas saírem no formato do modo interativo (`OK`, `(integer) 3`, `1) "..."`).
- **Banco lógico 1** (`redis-cli -n 1`) em todos os exercícios. Assim nada do banco 0 é afetado, e o `FLUSHDB` do Ex20 limpa só o banco 1 (em vez de rodar um `FLUSHDB` "às cegas" no banco padrão).
- Ex17 (Pub/Sub): o assinante (`SUBSCRIBE notificacoes`) foi iniciado em segundo plano em uma conexão e o `PUBLISH` foi feito em outra, com o assinante ainda conectado.
- Ex18 (Transação): os comandos `MULTI` ... `EXEC` foram enviados pela entrada padrão para **uma única** execução do `redis-cli`, garantindo que a transação acontecesse na mesma conexão. Antes foram criados saldos iniciais (`SET conta:A 100`, `SET conta:B 0`), pois sem eles o `DECRBY` deixaria a `conta:A` com -50.
- Ex19 depende da chave `sistema:nome` do Ex01, então os exercícios precisam ser feitos em ordem.

## Como reproduzir

O arquivo [comandos.redis](comandos.redis) tem todos os comandos na ordem da lista:

```bash
redis-cli -n 1 --no-raw < comandos.redis
```

Observações:

- O `redis-cli` não aceita comentários com `#` quando lê de um arquivo (testei e ele devolve `ERR unknown command '#'`). Por isso as seções do script são marcadas com `ECHO "== Ex01 ... =="`, que só imprime o texto.
- **Ex17:** o `SUBSCRIBE` bloqueia o terminal, então ele não está no script. Para testar, abra antes outro terminal com `redis-cli SUBSCRIBE notificacoes`; aí o `PUBLISH` do script retorna `1` e a mensagem aparece no outro terminal. Sem assinante, o `PUBLISH` retorna `0`.
- **Ex03:** para ver o `TTL` retornar `-2`, espere mais de 30 segundos e rode `redis-cli -n 1 TTL sessao:usuario:101` (não coloquei no script para ele não ficar parado esperando).
- O script termina com `FLUSHDB`, então pode ser rodado várias vezes seguidas com o mesmo resultado.

## Testes realizados

Todos os comandos abaixo foram executados de verdade contra o Redis 7.4.2 local; as saídas no `respostas.md` são as obtidas.

| Exercício | O que foi executado | Status |
|---|---|---|
| 01 | `SET` / `GET sistema:nome` | TESTADO E FUNCIONANDO |
| 02 | `MSET` / `MGET` | TESTADO E FUNCIONANDO |
| 03 | `SETEX` / `TTL` (30), `TTL` de chave sem expiração (-1) e após expirar (-2) | TESTADO E FUNCIONANDO |
| 04 | `INCR` / `INCRBY` / `DECRBY` (1, 6, 4) | TESTADO E FUNCIONANDO |
| 05 | `HSET usuario:201` | TESTADO E FUNCIONANDO |
| 06 | `HGET` / `HGETALL` | TESTADO E FUNCIONANDO |
| 07 | `HINCRBY` / `HKEYS` | TESTADO E FUNCIONANDO |
| 08 | `RPUSH fila:email` | TESTADO E FUNCIONANDO |
| 09 | `LPOP fila:email` | TESTADO E FUNCIONANDO |
| 10 | `LRANGE fila:email 0 -1` | TESTADO E FUNCIONANDO |
| 11 | `SADD` com duplicado / `SCARD` (3) | TESTADO E FUNCIONANDO |
| 12 | `SADD tags:post:2` / `SINTER` | TESTADO E FUNCIONANDO |
| 13 | `SISMEMBER` (0) | TESTADO E FUNCIONANDO |
| 14 | `ZADD placar:game` | TESTADO E FUNCIONANDO |
| 15 | `ZREVRANGE ... WITHSCORES` | TESTADO E FUNCIONANDO |
| 16 | `ZINCRBY` / `ZREVRANK` (0) | TESTADO E FUNCIONANDO |
| 17 | `SUBSCRIBE` em uma conexão + `PUBLISH` em outra (retornou 1, mensagem recebida) | TESTADO E FUNCIONANDO |
| 18 | Saldos iniciais + `MULTI` / `DECRBY` / `INCRBY` / `EXEC` na mesma conexão | TESTADO E FUNCIONANDO |
| 19 | `EXISTS` / `RENAME` / `DEL` | TESTADO E FUNCIONANDO |
| 20 | `INFO memory` / `FLUSHDB` (banco 1) | TESTADO E FUNCIONANDO |
| — | Script completo `redis-cli -n 1 --no-raw < comandos.redis` do início ao fim | TESTADO E FUNCIONANDO |

O comportamento de "sem rollback" do `MULTI`/`EXEC` quando um comando falha em tempo de execução está explicado no Ex18, mas não foi demonstrado com um comando com erro (não fazia parte do enunciado).

## Arquivos

- `README.md` — este arquivo.
- `respostas.md` — respostas dos 20 exercícios.
- `comandos.redis` — script com todos os comandos, na ordem.
