# Nomenclatura de arquivos

Um padrão só, para achar qualquer vídeo em 5 segundos. É o mesmo da descrição do projeto.

## O padrão
```
reel-AAAA-MM-DD-tema.mp4
```
- `reel`: o tipo da peça. Também vale `story`, `aula`, `anuncio`, `capa`.
- `AAAA-MM-DD`: a data de gravação.
- `tema`: 1 a 4 palavras do assunto, sem acento.

Tudo minúsculo, sem acento, sem espaço, com hífen entre as palavras.

## Exemplos
```
brutos/aula-2026-11-12-reuniao-online.mp4
prontos/reel-2026-11-12-present-perfect.mp4
prontos/reel-2026-11-12-present-perfect-v2.mp4
prontos/capa-2026-11-12-present-perfect.png
prontos/reel-2026-11-12-present-perfect-legenda.txt
```

## Versões e cortes
- **Ajuste depois da primeira versão:** acrescente `-v2`, `-v3`. Nunca sobrescreva a versão anterior.
- **Vários cortes da mesma aula:** acrescente `-corte1`, `-corte2`: `reel-2026-11-12-reuniao-online-corte1.mp4`.
- **Lote de ganchos:** acrescente `-g1`, `-g2`: `reel-2026-11-12-present-perfect-g1.mp4`.

## Regras
- `brutos/` nunca é alterada. Tudo o que a IA gera vai para `prontos/`.
- Postou? Se quiser, crie `prontos/postados/` e mova o arquivo para lá.
