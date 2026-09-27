# Lista 01 — Redis

Todos os comandos foram executados de verdade no `redis-cli` (Redis 7.4.2), usando o **banco lógico 1** (`redis-cli -n 1`) para não mexer em nada que estivesse no banco 0. Por isso o prompt aparece como `127.0.0.1:6379[1]>`. As saídas abaixo foram copiadas do terminal (rodei com `--no-raw`, que é a formatação do modo interativo); as linhas com o prompt `127.0.0.1:6379[1]>` indicam qual comando gerou cada saída.

---

## Exercício 01 — Strings (SET / GET)

Criar a chave `sistema:nome` com o valor "DataPlatform" e recuperar o valor.

Comando:
```redis
SET sistema:nome "DataPlatform"
GET sistema:nome
```

Saída obtida:
```text
127.0.0.1:6379[1]> SET sistema:nome "DataPlatform"
OK
127.0.0.1:6379[1]> GET sistema:nome
"DataPlatform"
```

Explicação: o `SET` grava a string na chave e responde `OK`. O `GET` devolve o valor guardado. Usei `:` no nome da chave só como convenção para organizar por "namespace" (sistema, env, usuario...), para o Redis é só um nome qualquer.

---

## Exercício 02 — Strings (MSET / MGET)

Gravar várias variáveis de ambiente de uma vez e ler duas delas.

Comando:
```redis
MSET env:db "postgres" env:cache "redis" env:queue "rabbitmq"
MGET env:db env:cache
```

Saída obtida:
```text
127.0.0.1:6379[1]> MSET env:db "postgres" env:cache "redis" env:queue "rabbitmq"
OK
127.0.0.1:6379[1]> MGET env:db env:cache
1) "postgres"
2) "redis"
```

Explicação: `MSET` grava as três chaves numa única operação (atômica), o que economiza idas e voltas ao servidor. O `MGET` devolve uma lista na mesma ordem das chaves pedidas; como só pedi `env:db` e `env:cache`, o `env:queue` não aparece.

---

## Exercício 03 — Strings com expiração (SETEX / TTL)

Criar uma sessão que expira em 30 segundos e consultar o tempo restante.

Comando:
```redis
SETEX sessao:usuario:101 30 "xyz123"
TTL sessao:usuario:101
```

Saída obtida:
```text
127.0.0.1:6379[1]> SETEX sessao:usuario:101 30 "xyz123"
OK
127.0.0.1:6379[1]> TTL sessao:usuario:101
(integer) 30
```

Também testei o TTL de uma chave sem expiração e, depois de passados mais de 30 segundos, o TTL da sessão de novo:

```text
127.0.0.1:6379[1]> TTL sistema:nome
(integer) -1
127.0.0.1:6379[1]> TTL sessao:usuario:101
(integer) -2
127.0.0.1:6379[1]> EXISTS sessao:usuario:101
(integer) 0
```

Explicação: o `TTL` mostra quantos segundos faltam para a chave sumir; deu 30 porque rodei logo em seguida. `-1` quer dizer que a chave existe mas não tem expiração (caso do `sistema:nome`), e `-2` quer dizer que a chave não existe mais, ou seja, a sessão já expirou e o Redis apagou sozinho. Isso é bem útil para sessões de login e cache.

---

## Exercício 04 — Strings como contador (INCR / INCRBY / DECRBY)

Contar visualizações da página inicial.

Comando:
```redis
INCR pageviews:home
INCRBY pageviews:home 5
DECRBY pageviews:home 2
```

Saída obtida:
```text
127.0.0.1:6379[1]> INCR pageviews:home
(integer) 1
127.0.0.1:6379[1]> INCRBY pageviews:home 5
(integer) 6
127.0.0.1:6379[1]> DECRBY pageviews:home 2
(integer) 4
```

Explicação: a chave não existia, então o `INCR` considerou ela como 0 e foi para 1. Depois +5 deu 6 e -2 deu 4. Cada comando já devolve o valor novo, e como o Redis executa um comando por vez, dois clientes incrementando ao mesmo tempo não perdem contagem.

---

## Exercício 05 — Hashes (HSET)

Guardar um usuário com vários campos numa única chave.

Comando:
```redis
HSET usuario:201 nome "Carlos" email "carlos@email.com" nivel "admin"
```

Saída obtida:
```text
127.0.0.1:6379[1]> HSET usuario:201 nome "Carlos" email "carlos@email.com" nivel "admin"
(integer) 3
```

Explicação: o hash funciona como um "objeto" ou uma linha de tabela: uma chave com vários pares campo/valor. O retorno 3 é a quantidade de campos **novos** criados (se eu rodasse de novo, retornaria 0, porque só atualizaria).

---

## Exercício 06 — Hashes (HGET / HGETALL)

Ler só o e-mail e depois todos os campos do usuário.

Comando:
```redis
HGET usuario:201 email
HGETALL usuario:201
```

Saída obtida:
```text
127.0.0.1:6379[1]> HGET usuario:201 email
"carlos@email.com"
127.0.0.1:6379[1]> HGETALL usuario:201
1) "nome"
2) "Carlos"
3) "email"
4) "carlos@email.com"
5) "nivel"
6) "admin"
```

Explicação: `HGET` pega um campo específico sem trazer o resto. O `HGETALL` devolve tudo numa lista intercalada campo, valor, campo, valor... por isso aparecem 6 itens para 3 campos.

---

## Exercício 07 — Hashes (HINCRBY / HKEYS)

Incrementar as tentativas de login e listar os campos do hash.

Comando:
```redis
HINCRBY usuario:201 tentativas_login 1
HKEYS usuario:201
```

Saída obtida:
```text
127.0.0.1:6379[1]> HINCRBY usuario:201 tentativas_login 1
(integer) 1
127.0.0.1:6379[1]> HKEYS usuario:201
1) "nome"
2) "email"
3) "nivel"
4) "tentativas_login"
```

Explicação: o campo `tentativas_login` não existia, então o `HINCRBY` criou ele com 0 e somou 1. Por isso o `HKEYS` agora mostra 4 campos. É o mesmo comportamento do `INCR`, só que dentro de um campo do hash.

---

## Exercício 08 — Lists (RPUSH)

Montar uma fila de e-mails para envio.

Comando:
```redis
RPUSH fila:email "email_1" "email_2" "email_3"
```

Saída obtida:
```text
127.0.0.1:6379[1]> RPUSH fila:email "email_1" "email_2" "email_3"
(integer) 3
```

Explicação: `RPUSH` insere no final (direita) da lista, na ordem em que os valores foram passados. O retorno é o tamanho da lista depois da inserção, 3.

---

## Exercício 09 — Lists (LPOP, consumidor FIFO)

Consumir o próximo e-mail da fila.

Comando:
```redis
LPOP fila:email
```

Saída obtida:
```text
127.0.0.1:6379[1]> LPOP fila:email
"email_1"
```

Explicação: como os itens entram pela direita (`RPUSH`) e saem pela esquerda (`LPOP`), o primeiro que entrou é o primeiro que sai, ou seja, FIFO. O `LPOP` também remove o item da lista, então o `email_1` foi "consumido".

---

## Exercício 10 — Lists (LRANGE)

Ver o que sobrou na fila.

Comando:
```redis
LRANGE fila:email 0 -1
```

Saída obtida:
```text
127.0.0.1:6379[1]> LRANGE fila:email 0 -1
1) "email_2"
2) "email_3"
```

Explicação: `0 -1` significa do primeiro ao último elemento (índices negativos contam a partir do fim). Sobraram só `email_2` e `email_3`, confirmando que o `LPOP` do exercício anterior tirou o `email_1`. O `LRANGE` só lê, não remove nada.

---

## Exercício 11 — Sets (SADD / SCARD)

Adicionar tags a um post (com "redis" repetido) e contar.

Comando:
```redis
SADD tags:post:1 "dados" "redis" "nosql" "redis"
SCARD tags:post:1
```

Saída obtida:
```text
127.0.0.1:6379[1]> SADD tags:post:1 "dados" "redis" "nosql" "redis"
(integer) 3
127.0.0.1:6379[1]> SCARD tags:post:1
(integer) 3
```

Explicação: passei 4 valores, mas o set não aceita duplicados, então o segundo "redis" foi ignorado. Por isso tanto o `SADD` (que retorna quantos elementos novos entraram) quanto o `SCARD` (tamanho do conjunto) dão 3.

---

## Exercício 12 — Sets (SINTER)

Criar as tags de outro post e ver as tags em comum.

Comando:
```redis
SADD tags:post:2 "redis" "python" "backend"
SINTER tags:post:1 tags:post:2
```

Saída obtida:
```text
127.0.0.1:6379[1]> SADD tags:post:2 "redis" "python" "backend"
(integer) 3
127.0.0.1:6379[1]> SINTER tags:post:1 tags:post:2
1) "redis"
```

Explicação: `SINTER` faz a interseção dos conjuntos, igual na matemática. O post 1 tem {dados, redis, nosql} e o post 2 tem {redis, python, backend}; o único em comum é "redis". Isso poderia ser usado, por exemplo, para sugerir posts relacionados.

---

## Exercício 13 — Sets (SISMEMBER)

Verificar se o post 1 tem a tag "python".

Comando:
```redis
SISMEMBER tags:post:1 "python"
```

Saída obtida:
```text
127.0.0.1:6379[1]> SISMEMBER tags:post:1 "python"
(integer) 0
```

Explicação: o retorno é 1 se o elemento pertence ao conjunto e 0 se não pertence. Deu 0 porque "python" está só no `tags:post:2`. Essa verificação é O(1), bem rápida mesmo com conjuntos grandes.

---

## Exercício 14 — Sorted Sets (ZADD)

Criar um placar de jogo com pontuações.

Comando:
```redis
ZADD placar:game 1500 "alice" 2200 "bob" 1800 "carol"
```

Saída obtida:
```text
127.0.0.1:6379[1]> ZADD placar:game 1500 "alice" 2200 "bob" 1800 "carol"
(integer) 3
```

Explicação: no sorted set cada membro tem um score, e o Redis mantém os membros ordenados por esse score automaticamente. Repare que no `ZADD` o score vem **antes** do membro. O retorno 3 são os membros novos adicionados.

---

## Exercício 15 — Sorted Sets (ZREVRANGE)

Mostrar o ranking do maior para o menor, com as pontuações.

Comando:
```redis
ZREVRANGE placar:game 0 -1 WITHSCORES
```

Saída obtida:
```text
127.0.0.1:6379[1]> ZREVRANGE placar:game 0 -1 WITHSCORES
1) "bob"
2) "2200"
3) "carol"
4) "1800"
5) "alice"
6) "1500"
```

Explicação: `ZRANGE` ordena do menor para o maior, e o `ZREVRANGE` faz o contrário, que é o que se quer num placar. O `WITHSCORES` faz aparecer a pontuação logo depois de cada nome. Ficou bob em 1º, carol em 2º e alice em 3º.

---

## Exercício 16 — Sorted Sets (ZINCRBY / ZREVRANK)

Dar 800 pontos para a alice e ver a posição dela no ranking.

Comando:
```redis
ZINCRBY placar:game 800 "alice"
ZREVRANK placar:game "alice"
```

Saída obtida:
```text
127.0.0.1:6379[1]> ZINCRBY placar:game 800 "alice"
"2300"
127.0.0.1:6379[1]> ZREVRANK placar:game "alice"
(integer) 0
```

Para conferir, rodei o ranking de novo:

```text
127.0.0.1:6379[1]> ZREVRANGE placar:game 0 -1 WITHSCORES
1) "alice"
2) "2300"
3) "bob"
4) "2200"
5) "carol"
6) "1800"
```

Explicação: a alice foi de 1500 para 2300 e passou o bob (2200). O `ZREVRANK` retornou 0 porque a posição começa em zero, então 0 significa 1º lugar. O score volta como string ("2300") porque o Redis devolve o score como texto no protocolo.

---

## Exercício 17 — Pub/Sub (SUBSCRIBE / PUBLISH)

Um terminal assina o canal `notificacoes` e outro publica uma mensagem.

Comando:
```redis
-- Terminal 1
SUBSCRIBE notificacoes

-- Terminal 2
PUBLISH notificacoes "Novo relatorio disponivel"
```

Saída obtida:

Terminal 1 (assinante, rodando em segundo plano):
```text
1) "subscribe"
2) "notificacoes"
3) (integer) 1
1) "message"
2) "notificacoes"
3) "Novo relatorio disponivel"
```

Terminal 2 (publicador):
```text
127.0.0.1:6379[1]> PUBLISH notificacoes "Novo relatorio disponivel"
(integer) 1
```

Explicação: ao assinar, o terminal 1 recebe a confirmação (`subscribe`, nome do canal e quantos canais ele assina) e fica bloqueado esperando mensagens. O `PUBLISH` retornou 1, que é o número de clientes que receberam a mensagem. A mensagem não fica guardada: se ninguém estiver inscrito naquele momento ela se perde (o `PUBLISH` retorna 0). Os canais também não dependem do banco lógico, valem para o servidor inteiro.

---

## Exercício 18 — Transações (MULTI / EXEC)

Transferir R$ 50 da `conta:A` para a `conta:B` de forma atômica.

Antes da transação eu defini saldos iniciais, porque as chaves não existiam (o `EXISTS` retornou 0). Sem isso, o `DECRBY` trataria a conta:A como 0 e ela ficaria com **-50**, o que não faz sentido para uma transferência.

Comando:
```redis
EXISTS conta:A conta:B
SET conta:A 100
SET conta:B 0

MULTI
DECRBY conta:A 50
INCRBY conta:B 50
EXEC

MGET conta:A conta:B
```

Saída obtida (todos os comandos enviados na mesma conexão do redis-cli):
```text
127.0.0.1:6379[1]> EXISTS conta:A conta:B
(integer) 0
127.0.0.1:6379[1]> SET conta:A 100
OK
127.0.0.1:6379[1]> SET conta:B 0
OK
127.0.0.1:6379[1]> MULTI
OK
127.0.0.1:6379[1]> DECRBY conta:A 50
QUEUED
127.0.0.1:6379[1]> INCRBY conta:B 50
QUEUED
127.0.0.1:6379[1]> EXEC
1) (integer) 50
2) (integer) 50
127.0.0.1:6379[1]> MGET conta:A conta:B
1) "50"
2) "50"
```

Explicação: depois do `MULTI` os comandos não rodam na hora, só entram numa fila (`QUEUED`). No `EXEC` o Redis executa tudo de uma vez, sem nenhum outro cliente conseguir intercalar comandos no meio, então ninguém vê o dinheiro "saindo de A e ainda não chegando em B". O resultado do `EXEC` é a lista com a resposta de cada comando: A ficou com 50 e B com 50. Um detalhe importante é que o Redis **não faz rollback**: se um comando falhar durante a execução (por exemplo, `INCRBY` numa chave que não é número), os outros continuam executados; só se houver erro de sintaxe antes do `EXEC` a transação inteira é descartada.

---

## Exercício 19 — Administração de chaves (EXISTS / RENAME / DEL)

Verificar a chave do Exercício 01, renomear e apagar.

Obs.: esse exercício depende da chave `sistema:nome` criada no Ex01 ainda existir (ela não tem TTL, então continuava lá).

Comando:
```redis
EXISTS sistema:nome
RENAME sistema:nome sistema:app
DEL sistema:app
```

Saída obtida (com algumas verificações extras):
```text
127.0.0.1:6379[1]> EXISTS sistema:nome
(integer) 1
127.0.0.1:6379[1]> RENAME sistema:nome sistema:app
OK
127.0.0.1:6379[1]> EXISTS sistema:nome
(integer) 0
127.0.0.1:6379[1]> GET sistema:app
"DataPlatform"
127.0.0.1:6379[1]> DEL sistema:app
(integer) 1
127.0.0.1:6379[1]> EXISTS sistema:app
(integer) 0
```

Explicação: `EXISTS` retorna quantas das chaves informadas existem (1). O `RENAME` troca o nome mas mantém o valor, tanto que o `GET sistema:app` ainda devolve "DataPlatform". O `DEL` retorna quantas chaves foram apagadas. Se o `sistema:nome` não existisse, o `RENAME` daria erro `ERR no such key`.

---

## Exercício 20 — Administração do servidor (INFO memory / FLUSHDB)

Consultar o uso de memória e limpar o banco.

Comando:
```redis
DBSIZE
INFO memory
FLUSHDB
DBSIZE
```

Saída obtida (o `INFO memory` devolve dezenas de linhas; deixei só as principais):
```text
127.0.0.1:6379[1]> DBSIZE
(integer) 11
127.0.0.1:6379[1]> INFO memory
# Memory
used_memory:1552442
used_memory_human:1.48M
used_memory_rss:1518110
used_memory_rss_human:1.45M
used_memory_peak:1552442
used_memory_peak_human:1.48M
maxmemory:0
maxmemory_human:0B
maxmemory_policy:noeviction
mem_fragmentation_ratio:1.00
mem_allocator:libc
...
127.0.0.1:6379[1]> FLUSHDB
OK
127.0.0.1:6379[1]> DBSIZE
(integer) 0
```

Explicação: o `INFO memory` mostra quanto de memória o Redis está usando (`used_memory_human` = 1.48M), o pico de uso e a política quando a memória acaba (`maxmemory 0` = sem limite, `noeviction` = não descarta chaves, dá erro de escrita). Antes do `FLUSHDB` havia 11 chaves no banco 1 (o `sistema:nome` já tinha sido apagado e a sessão tinha expirado). O `FLUSHDB` apaga todas as chaves **só do banco selecionado**, por isso usei o banco 1; o `FLUSHALL` é que apagaria todos os bancos. O comando foi dado com `-n 1`, então o banco 0 não foi afetado.
