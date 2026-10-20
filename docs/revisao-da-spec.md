# Revisão da spec: contradições e lacunas

Revisão de `docs/spec-edicao-de-videos.md`. Antes de virar código, cada item abaixo precisa de uma decisão. Um motor feito em cima de regras que se contradizem reprova vídeo bom ou deixa passar vídeo ruim.

Em cada item vai a recomendação e o texto pronto para substituir na spec.

---

## A. Contradições (bloqueiam a implementação)

### 1. Frequência das cenas de apoio: 2–4 s ou 10–15 s?

- §13: uma cena a cada **2 a 4 s** de Isis (alvo 3 s), com correspondência **clara**, e a unidade é a **oração**.
- §18 ("regra definitiva"): uma cena a cada **10 a 15 s**, com correspondência **inequívoca**, e a unidade é a **frase completa**.
- §20: "respeitar o intervalo preferencial de 10 a 15 segundos".
- §12: "relação semântica inequívoca".

O §13 diz "passa de inequívoca para clara", ou seja, é a revisão mais nova. Os §12, §18 e §20 ficaram desatualizados.

**Recomendação:** manter o §13 e alinhar os outros três. Justificativa: é a regra mais recente e é a única que entrega o ritmo de vídeo curto.

Texto para o §12 (2º parágrafo):
> As demais cenas funcionam como imagens de apoio e só podem ser inseridas quando houver correspondência clara com o trecho (ver §13).

Texto para a "regra definitiva" do §18:
> Depois de 2 a 4 segundos de Isis falando, procurar o próximo trecho de sentido completo que tenha correspondência clara no catálogo. Exibir uma única cena durante todo esse trecho e voltar para Isis por no mínimo 1,5 s. Se não houver correspondência clara, não realizar a troca.

Texto para o §20:
> - respeitar o intervalo de 2 a 4 segundos de Isis entre cenas, sem forçar trocas;
> - iniciar e finalizar cada cena de apoio nos limites de um único trecho de sentido;

### 2. A unidade da cena é a frase ou a oração?

O §13 manda cobrir uma **oração** (trecho entre vírgulas e conjunções). O §14 fala só em **frase**: "começar no início de uma frase", "limite absoluto: uma frase completa", "se a frase tiver menos de 2 segundos, manter Isis", "uma frase não recebe duas cenas".

Do jeito que está, uma oração de 3 s dentro de uma frase de 8 s é permitida pelo §13 e proibida pelo §14 ("a cena não entra no meio da frase").

**Recomendação:** trocar "frase" por "trecho de sentido" em todo o §14 e definir o termo uma vez.

Texto para abrir o §14:
> **Trecho de sentido:** oração ou segmento delimitado por vírgula, ponto ou conjunção, com começo, meio e fim semanticamente completos. Uma frase pode conter vários trechos. Todas as regras abaixo valem para o trecho.

### 3. Pausa máxima: 0,20 s ou 0,30 s?

- §7: alvo de **0,10 s**, máximo de **0,20 s**.
- §19.1, item 5: reprova silêncio interno acima de **0,30 s**.

Um vídeo com pausa de 0,25 s viola o §7 e passa na autocrítica.

**Recomendação:** a montagem mira 0,10 s com teto de 0,20 s, e a autocrítica reprova acima de 0,20 s. O gate final tem que ser igual à regra, senão não serve como gate.

Texto para o §19.1, item 5:
> 5. **Pausas**: nenhum silêncio interno acima de 0,20 s.

### 4. Tolerância de sincronia da legenda: 0,10 s ou 0,12 s?

- §10.6: desvio acima de **0,1 s** reprova.
- §19.1, item 3: tolerância de **0,12 s**.

**Recomendação:** 0,10 s nas duas seções. Justificativa: é a regra mais rígida, e 20 ms de folga não mudam a percepção mas criam duas réguas diferentes.

Texto para o §19.1, item 3:
> 3. **Sincronia de legenda**: início de cada bloco contra o ataque real da primeira palavra, arbitrado por retranscrição de janela curta (tolerância 0,10 s);

### 5. "Sem conteúdo adicional" contra "palavras de ligação ficam no áudio"

- §3: palavras soltas de ligação ("realmente", "aqui") **permanecem no áudio** e entram no relatório.
- §4.2.4: improvisos da fala fluida ficam no áudio.
- §8: o vídeo só avança se "não houver conteúdo adicional".
- §20: só exporta se "reproduzir integralmente o script".

Do jeito que está, qualquer vídeo com um "realmente" a mais é reprovado no §8. O motor nunca exporta.

**Recomendação:** o §8 passa a distinguir desvio tolerado de desvio que reprova.

Texto para o §8, 3º item:
> - não houver conteúdo adicional, exceto palavras soltas de ligação dentro de frase fluida (§3), que ficam no áudio e são listadas no relatório com timestamp; trecho fora do script com 4 ou mais palavras reprova.

### 6. Pigarros: remoção obrigatória ou nunca cortar sem transcrição?

- §6: eliminar pigarros, estalos e ruídos de garganta.
- §4.2.3: som alto sem transcrição **nunca** se corta automaticamente.

Pigarro é exatamente "som alto sem transcrição". A remoção obrigatória e a proibição de cortar batem de frente.

**Recomendação:** pigarro sai só quando a transcrição técnica o marcou como ruído (§4 manda registrar pigarros) **e** há vale quieto nas duas pontas (§4.2.1). Som alto que a transcrição não classificou continua indo para decisão humana.

Texto para o §4.2, item 3:
> 3. **Som alto sem transcrição**: só é cortado se a transcrição técnica o classificou como pigarro, estalo ou ruído de garganta **e** existe vale quieto nas duas pontas. Som alto sem classificação nunca se corta automaticamente: fica no vídeo e entra no relatório para decisão humana.

### 7. Duração da cena: máximo de 6 s contra "trecho inteiro"

- §14: máximo preferencial de **6 s**, mas, se a frase passar de 6 s, usa a cena inteira se o arquivo for longo o suficiente.
- §13: as cenas ocupam no máximo **metade do tempo total**.

Não chega a ser contradição, mas falta dizer o que acontece quando o arquivo da cena é mais curto que o trecho. O §14 proíbe repetir, desacelerar ou congelar, então a única saída é não usar aquela cena.

Texto para acrescentar ao §14:
> - se a duração do arquivo for menor que a do trecho, a cena não pode ser usada nesse trecho.

---

## B. Lacunas (o motor precisa do número, a spec não dá)

| # | Onde | O que falta |
| --- | --- | --- |
| 8 | §10.1 e §10.3 | **Resolução de referência.** 52 px e posição –200 só fazem sentido para uma resolução fixa (1080×1920?). Definir a referência e dizer que os valores escalam proporcionalmente. |
| 9 | §10.3 | **Sentido do –200.** É 200 px acima da borda inferior? Medido até a base ou até o centro do bloco? |
| 10 | §10.2 | **Unidade de "expansão 25" e "arredondamento 20".** Pixels na resolução de referência? |
| 11 | §10.5 | **Bloco que não cabe em uma linha.** Quatro palavras longas em 52 px podem passar da largura útil no vertical. Definir a largura máxima e o que fazer (cair para 3 ou 2 palavras). |
| 12 | §10.5 | **Frase com uma palavra só** ("Sim."). A regra "nunca uma palavra isolada" não tem saída. Recomendo juntar com o bloco anterior se o total não passar de 4 palavras, senão com o seguinte. |
| 13 | §4.2.2 e §19.1 | **Verificação de ouvido.** O motor não tem ouvido. Isso vira etapa humana com fila de revisão, e a spec precisa dizer se o vídeo fica parado esperando ou se exporta com pendência marcada. |
| 14 | §2 | **Formato do catálogo e da configuração.** Planilha? CSV? JSON? Nomes das colunas? Sem isso o motor não lê as 208 cenas. |
| 15 | §11 e §16 | **Arquivo duplicado.** Como a observação marca duplicata e como aponta o original? |
| 16 | §18 | **Whoosh no início do vídeo.** Se o pico do whoosh vier depois do começo do áudio do efeito, uma cena logo no começo empurraria o efeito para antes de 0 s. Como o vídeo sempre começa em Isis (§13) isso só acontece se a primeira cena entrar muito cedo; definir que a primeira cena não entra antes do pico do whoosh caber. |
| 17 | §4.2.1 | **Limiar de -22 dBFS** é alto para vale de silêncio (respiração costuma ficar por volta de -35 a -45 dBFS). Confirmar se o número é esse mesmo ou se é relativo ao pico da fala. |
| 18 | §4 | **Ferramenta de transcrição.** Qual motor (Whisper, outro) e qual idioma. Afeta precisão de timestamp e detecção de pigarro. |

---

## C. Duplicidade (não quebra, mas confunde)

- O §19 lista a ordem de execução e o §19.1 lista a autocrítica, mas os gates do §8, §9, §10.6 e §19.1 se repetem com números diferentes (itens 3 e 4 acima). Depois de resolver as contradições, vale manter os números **num lugar só** (uma tabela de gates) e as outras seções apontarem para ela.

---

## Próximo passo

Fechadas as decisões de A1 a A7 e os números de B8 a B14, dá para começar o motor. Ordem sugerida, do que destrava mais para o que destrava menos:

1. transcrição em janelas curtas + alinhamento com o script (§4, §4.1, §5);
2. corte com vale quieto + montagem em passada única + gate de sincronia (§4.2, §4.3, §7);
3. legendas a partir do script, retranscrição do editado e gate de 0,10 s (§10);
4. autocrítica e relatório (§19.1);
5. seleção semântica de cenas + whoosh (§13 a §18).
