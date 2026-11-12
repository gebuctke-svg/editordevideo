# Motor de Edição de Vídeos Baseado em Script — Versão Universal

Especificação para editar automaticamente qualquer vídeo de pessoa falando para a câmera, usando o script escrito como fonte oficial. Serve para qualquer apresentador, nicho, idioma e formato.

## Como usar este documento

1. Preencha a **Ficha do projeto** (seção 0). É o único trecho que muda de um projeto para outro.
2. Entregue ao agente de edição: este documento, o vídeo bruto, o script oficial e, se houver, o catálogo de cenas.
3. Não altere as seções marcadas como **regra rígida**. Elas existem para impedir erros de corte, sincronia e fidelidade.

Sempre que o texto disser **apresentador**, leia: a pessoa definida na Ficha do projeto. Sempre que citar um valor entre crases (ex.: `INTERVALO_ALVO`), o valor vem da Ficha.

---

## 0. Ficha do projeto (preencher)

### 0.1 Identificação

| Campo | Valor |
| :---- | :---- |
| `APRESENTADOR` | [nome de quem fala no vídeo] |
| `IDIOMA` | [idioma do script e da fala] |
| `FORMATO` | [ex.: vertical 9:16, horizontal 16:9, quadrado 1:1] |
| `RESOLUCAO` | [ex.: 1080×1920] |
| `ENQUADRAMENTO` | [descrição do enquadramento deste vídeo; o agente não deduz] |

### 0.2 Cenas de apoio

| Campo | Valor | Padrão |
| :---- | :---- | :---- |
| `USA_CENAS` | [sim / não] | sim |
| `CATALOGO` | [arquivo do catálogo de cenas] | — |
| `EFEITO_SONORO` | [caminho do arquivo de áudio, ou "nenhum"] | nenhum |
| `INTERVALO_CENAS` | [segundos do apresentador na tela entre uma cena e outra] | 2 a 4 s (alvo 3 s) |
| `RETORNO_MINIMO` | [tempo mínimo de retorno ao apresentador entre duas cenas] | 1,5 s |
| `TETO_CENAS` | [fatia máxima do vídeo ocupada por cenas de apoio] | 50% |

Se `USA_CENAS` = não, ignore as seções 11 a 18 e os itens de cena das seções 19 e 20. O vídeo fica inteiro na gravação principal.

### 0.3 Legendas

| Campo | Padrão |
| :---- | :---- |
| `FONTE` | Figtree |
| `PESO` | Bold |
| `TAMANHO` | 52 px |
| `CAIXA` | todas maiúsculas |
| `COR_TEXTO` | branco |
| `COR_FUNDO` | preto, 80% de opacidade |
| `MARGEM_FUNDO` | 25 |
| `RAIO_FUNDO` | 20 |
| `POSICAO` | âncora centro inferior, horizontal 0, vertical –200 |
| `PALAVRAS_POR_BLOCO` | 2 a 4 (média 3) |

> Atenção: tamanho, margem, raio e posição foram calibrados no projeto de origem deste documento, cuja resolução de referência não estava registrada. Teste no seu formato e ajuste proporcionalmente antes de fixar os valores.

### 0.4 Ritmo e tolerâncias

| Campo | Padrão |
| :---- | :---- |
| `INTERVALO_ALVO` (entre falas) | 0,10 s |
| `INTERVALO_MAXIMO` (entre falas) | 0,20 s |
| `PAUSA_REPROVADA` (gate da autocrítica) | acima de 0,30 s |
| `LIMIAR_SILENCIO` | –22 dBFS, janela de 30 ms, raio de 0,25 s |
| `TOLERANCIA_AV` (vídeo × áudio) | 0,04 s |
| `TOLERANCIA_LEGENDA` | 0,10 s |

`LIMIAR_SILENCIO` depende do nível de gravação. Se o seu áudio for mais baixo ou mais ruidoso, recalibre esse valor antes de rodar.

---

## 1. Objetivo

Editar automaticamente um vídeo bruto usando o script escrito como fonte oficial, eliminando erros de gravação e construindo um vídeo fluido, com cortes secos, legendas padronizadas e cenas de apoio semanticamente compatíveis.

O sistema deve:

- preservar somente o conteúdo correto do script;
- remover gaguejos, repetições, correções, pigarros e ruídos de garganta;
- eliminar intervalos e silêncios desnecessários;
- usar exclusivamente cortes secos;
- gerar legendas a partir do script oficial;
- selecionar cenas de apoio somente quando houver correspondência clara com a fala;
- validar o vídeo editado antes da exportação.

## 2. Entradas

1. vídeo bruto do apresentador falando;
2. script oficial em texto;
3. catálogo de cenas classificadas (se `USA_CENAS` = sim);
4. Ficha do projeto preenchida (seção 0).

## 3. Hierarquia das fontes

Quando houver qualquer divergência, respeitar esta hierarquia:

1. **Script oficial:** determina exatamente o que deve permanecer falado e escrito.
2. **Vídeo bruto:** fornece imagem, áudio e timestamps.
3. **Transcrição técnica:** localiza as ocorrências do script e identifica erros, repetições e ruídos.
4. **Catálogo de cenas:** determina quais imagens de apoio podem ser utilizadas.
5. **Ficha do projeto:** determina enquadramento, formato e demais regras específicas.
6. **Padrão de legendas:** determina tipografia, aparência, segmentação e posição.

O script é sempre a fonte da verdade. A transcrição nunca substitui, corrige ou reescreve o script.

**Fidelidade ao script (regra rígida):**

- As legendas reproduzem somente o script, palavra por palavra.
- Frases ou trechos falados que não existem no script (com 4 ou mais palavras, delimitados por pausas) são **removidos do áudio**.
- Palavras soltas de ligação faladas dentro de uma frase fluida (ex.: "realmente", "aqui") não podem ser extirpadas sem rasgar o áudio; elas permanecem, mas **todas são listadas no relatório de autocrítica com timestamp**, para decisão de regravação.
- Toda divergência entre fala e script aparece no relatório. Nada é silenciosamente aceito.

## 4. Transcrição técnica

Transcrever integralmente o vídeo bruto com timestamp em nível de palavra, registrando fielmente:

- palavras completas;
- palavras e sílabas interrompidas;
- gaguejos;
- repetições;
- vícios de linguagem;
- falsos começos;
- frases abandonadas;
- autocorreções;
- pigarros e ruídos de garganta;
- respirações muito evidentes;
- comentários fora do script;
- tentativas anteriores à versão correta;
- intervalos e silêncios.

Nada deve ser omitido nesta etapa. A transcrição técnica representa o material bruto e serve para localizar precisamente o que será mantido ou descartado.

### 4.1 Precisão dos timestamps (regra rígida)

- A transcrição com timestamp por palavra é feita em **janelas curtas** (áudio segmentado nas pausas, blocos de no máximo 40 segundos), nunca no arquivo inteiro de uma vez: em arquivos longos o alinhamento deriva e chega a errar segundos.
- Timestamps de legenda e de corte saem sempre dessas janelas medidas.

### 4.2 Onde a tesoura pode descer (regra rígida)

A **decisão** do que sai vem da comparação script × transcrição com timestamp. O **corte físico** obedece a estas leis, nesta ordem:

1. **Pausa, respiro e silêncio:** só se cortam quando existe um vale de energia quieto (conforme `LIMIAR_SILENCIO`) nas **duas pontas** do corte. Sem vale quieto, o corte **não acontece**. Cortar palavra ao meio é impossibilidade de código, não recomendação.
2. **Regravação (retake):** sai por vão inteiro, da primeira ocorrência até a segunda, **ancorado em palavra igual** (o corte emenda dois pontos com o mesmo conteúdo fonético, o que torna o erro de timestamp inaudível). Nunca palavra a palavra.
   - A cirurgia automática só age sobre repetição de **3 ou mais palavras** não sancionada pelo script. Repetição de 2 palavras é ambígua (enumerações e anáforas legítimas da fala: "ou na sua casa, ou na sua relação", "que querem entender, que querem ir até o fim") e **sempre passa por verificação de ouvido** antes de qualquer corte.
   - Repetições e desvios confirmados como legítimos entram numa **lista de aceitas** no validador, para não reprovar de novo nas próximas rodadas.
3. **Som alto sem transcrição:** NUNCA se corta automaticamente. Pode ser fala real com timestamp deslocado. Fica no vídeo e entra no relatório para decisão humana.
4. **Improvisos da fala fluida ficam no áudio.** A fidelidade ao script se garante nas legendas e no relatório de desvios com timestamp, nunca com tesoura no meio da frase.

### 4.3 Sincronia audiovisual (regra rígida)

- Renderização em **passada única**, sem seek por pedaço; janelas de vídeo meio-abertas para que o número de frames corresponda exatamente à duração do áudio.
- Gate obrigatório: a duração da trilha de vídeo e da trilha de áudio do arquivo final não podem divergir mais que `TOLERANCIA_AV`. Divergiu, não exporta.

## 5. Alinhamento entre transcrição e script

Comparar a transcrição integral com o script oficial em nível de palavra. Para cada frase do script, o agente deve:

1. localizar todas as ocorrências correspondentes no vídeo;
2. identificar as diferentes tentativas gravadas;
3. escolher a tentativa mais completa, clara e fluida;
4. preservar somente as palavras que formam a versão correta;
5. descartar qualquer conteúdo que não pertença ao script;
6. recorrer a partes de tentativas diferentes apenas quando necessário e quando a montagem permanecer natural e sincronizada.

Se uma frase tiver sido iniciada, interrompida e depois regravada corretamente, deve permanecer apenas a versão correta.

Exemplo de gravação bruta:

> "Você... você consegue... cof... você consegue transformar aquilo que deseja... Não, de novo. Você consegue transformar aquilo que deseja em realidade."

Resultado:

> "Você consegue transformar aquilo que deseja em realidade."

## 6. Remoções obrigatórias

Eliminar:

- gaguejos;
- sílabas repetidas;
- palavras repetidas acidentalmente;
- falsos começos;
- frases abandonadas;
- tentativas malsucedidas;
- autocorreções;
- pigarros;
- estalos e barulhos usados para ajustar a voz;
- respirações longas ou isoladas;
- comentários fora do script;
- silêncios desnecessários;
- intervalos gerados pela junção das tomadas.

Toda remoção respeita as leis de corte da seção 4.2.

## 7. Regras de corte e ritmo

- Utilizar exclusivamente **cortes secos**.
- Não usar fades, dissoluções, transições, sobreposições ou efeitos entre tomadas.
- Uma tomada deve começar imediatamente após o término da anterior.
- Não preservar pausas dramáticas.
- O alvo de intervalo entre falas é `INTERVALO_ALVO`.
- O intervalo máximo permitido é `INTERVALO_MAXIMO`.
- Nunca cortar o início ou o final de uma palavra ou fonema.
- Se o intervalo-alvo tornar a fala artificial, preservar o tempo mínimo necessário, sem ultrapassar o máximo.
- Não deixar silêncio antes da primeira fala nem depois da última.
- A montagem deve parecer uma fala contínua, mesmo quando formada por tomadas diferentes.

## 8. Validação textual após a montagem

Depois dos cortes, gerar uma nova transcrição do vídeo editado e compará-la com o script oficial. O vídeo só pode avançar quando:

- todas as frases do script estiverem presentes;
- as frases estiverem na sequência correta;
- não houver conteúdo adicional (exceto palavras de ligação listadas no relatório, conforme seção 3);
- não houver gaguejos, repetições ou autocorreções;
- nenhuma palavra ou sílaba estiver cortada;
- os intervalos obedecerem aos limites definidos.

## 9. Validação audiovisual

Realizar uma segunda verificação para detectar:

- cortes no meio de fonemas;
- mudanças abruptas de volume;
- pigarros ou ruídos remanescentes;
- respirações isoladas;
- pausas irregulares;
- frames congelados;
- boca parada enquanto o áudio continua;
- perda de sincronização entre áudio e vídeo;
- cortes visuais tecnicamente inválidos.

## 10. Legendas

### 10.1 Fonte e formatação

- Fonte, peso, tamanho, caixa e cor: conforme Ficha (seção 0.3).
- Alinhamento: **centralizado**.
- Espaçamento entre caracteres: **0**.
- Espaçamento entre linhas: **0**.
- Traçado ou contorno: **desativado**.
- Sombra: **desativada**.

### 10.2 Fundo

- Cor, opacidade, margem interna e arredondamento: conforme Ficha.
- O fundo acompanha automaticamente o tamanho de cada bloco.
- Não utilizar caixa de fundo com largura fixa.
- Não adicionar elementos decorativos.

### 10.3 Posicionamento

- Posição conforme `POSICAO` na Ficha.
- Manter a mesma posição durante todo o vídeo.
- O enquadramento é informado na Ficha e não deve ser deduzido pelo agente.

### 10.4 Fonte textual

As legendas são geradas a partir do **script oficial**, nunca da transcrição bruta. A transcrição serve apenas para sincronizar as palavras do script com o áudio. A legenda nunca reproduz gaguejos, tentativas descartadas, repetições ou erros de gravação.

Reproduzir literalmente:

- palavras;
- grafia;
- acentuação;
- sequência das frases.

Pontuação nas legendas: **remover toda a pontuação** (vírgula, ponto, exclamação, dois-pontos, ponto e vírgula, travessão). **Manter somente o ponto de interrogação (?)**. O hífen interno de palavras compostas (ex.: vale-presente) é grafia, não pontuação, e permanece. Em idiomas com sinais próprios (ex.: ¿ em espanhol, apóstrofo em inglês e francês), o que faz parte da grafia da palavra permanece.

O agente não pode corrigir, resumir, completar, interpretar, traduzir ou reescrever o texto.

### 10.5 Divisão dos blocos

- Cada legenda ocupa **obrigatoriamente uma única linha**.
- Cada bloco contém **de duas a quatro palavras**.
- A média desejada é de **três palavras por bloco**.
- Nunca exibir apenas uma palavra isolada.
- Nunca ultrapassar quatro palavras.
- Priorizar blocos de três palavras sempre que isso preservar o sentido e a naturalidade.
- Não separar artigos, preposições ou pronomes da palavra à qual estão ligados.
- Não quebrar expressões que formam uma unidade de sentido.
- A divisão acompanha o ritmo da fala e forma pequenos blocos semanticamente completos.
- Se houver conflito entre a média de três palavras e a unidade de sentido, podem ser usadas duas ou quatro palavras, respeitando sempre o limite de uma linha.

Evitar:

```
PARA
```

Preferir:

```
PARA VOCÊ
```

### 10.6 Sincronização

- Recalcular todos os timestamps depois da edição dos cortes.
- Não reutilizar os timestamps do vídeo bruto.
- É proibido derivar os tempos das legendas da transcrição do bruto mapeada pelos cortes: o vídeo editado deve ser retranscrito com timestamp por palavra e as legendas sincronizam com esses tempos medidos no próprio vídeo final.
- Validação automática de sincronia: o início de cada bloco é comparado com o ataque da primeira palavra do bloco no áudio editado; desvio acima de `TOLERANCIA_LEGENDA` reprova o bloco e exige correção antes da exportação.
- A legenda entra no início da primeira palavra do bloco.
- A legenda sai ao final da última palavra do bloco.
- A legenda não pode permanecer depois que a fala correspondente terminar.
- A legenda seguinte não pode aparecer antes do início da fala correspondente.
- Não deixar legendas atravessarem cortes quando o áudio tiver sido remontado.
- Não criar intervalo visual entre blocos quando a fala for contínua.
- Durante um silêncio real, a legenda anterior desaparece ao final da fala.

### 10.7 Animações

- Entrada instantânea.
- Saída instantânea.
- Sem fade.
- Sem movimento.
- Sem zoom.
- Sem efeito de digitação.
- Sem destaque palavra por palavra.
- Sem mudança de cor.
- Sem transição entre blocos.

## 11. Catálogo de cenas

O catálogo é a lista de todas as imagens de apoio disponíveis para o projeto. Pode ter qualquer quantidade de cenas e de classes. Cada registro precisa ter:

- arquivo;
- classe;
- descrição da cena;
- indicação de **quando usar**;
- duração;
- formato;
- orientação;
- observação, incluindo a marcação de arquivos duplicados.

Sem os campos **descrição** e **quando usar** o agente não tem como decidir com segurança. Catálogo incompleto significa menos cenas inseridas, não escolha no chute.

### 11.1 Como montar as classes

Agrupe as cenas pela **função que cumprem na narrativa**, não pela aparência. Modelo de partida (adapte, renomeie, exclua ou crie classes conforme o seu nicho):

| Classe | Função principal |
| :---- | :---- |
| Mecanismo ou método próprio | Imagens-assinatura do seu método, framework ou conceito central |
| Passo a passo e prática | Mãos trabalhando, caderno, checklist, calendário; blocos de "como funciona" |
| Símbolos e metáforas | Objetos e imagens que representam ideias abstratas |
| Estado desejado | Resultado, alívio, conquista; como a vida fica depois |
| Identidade e reflexão | Espelhos, olhares, perfis; autoconhecimento e decisão pessoal |
| Dor e problema | Cansaço, frustração, preocupação; bloco de dor |
| Jornada e escolha | Caminhos, ciclos, bifurcações; processo e evolução |
| Tempo e urgência | Relógio, prazo, passagem do tempo |
| Tecnologia e acesso | Plataforma, celular, tela; entrega e acesso ao produto |
| Conexão e apoio | Acolhimento, comunidade, suporte |
| Bastidores do apresentador | Vida real, rotina, viagens, trabalho de quem fala |
| Prova e autoridade | Resultados, prêmios, eventos, livros, depoimentos |
| Gravação principal | O apresentador falando; base narrativa |

## 12. Fonte visual principal

A gravação do **apresentador falando** é a imagem principal do vídeo.

As demais cenas funcionam como imagens de apoio e só podem ser inseridas quando houver relação semântica clara com o trecho falado.

Na ausência de uma cena comprovadamente adequada, manter o apresentador. É preferível permanecer na gravação principal a inserir uma cena bonita, mas desconectada da fala.

## 13. Frequência das cenas de apoio

- Manter o apresentador falando como base.
- Procurar uma oportunidade de inserir uma cena de apoio a cada `INTERVALO_CENAS` do apresentador na tela.
- A unidade ilustrável é a **oração ou trecho de sentido completo** (segmentos entre vírgulas e conjunções), não apenas a frase inteira. A cena cobre esse trecho do início ao fim.
- A correspondência exigida é **clara**: a classe e a descrição da cena precisam representar a ideia central do trecho. É proibido escolher cena por coincidência de uma palavra solta, por estética ou para cumprir a frequência.
- Nunca interromper um trecho no meio apenas para obedecer ao intervalo.
- Não emendar duas cenas de apoio: entre uma cena e a seguinte há sempre retorno ao apresentador por no mínimo `RETORNO_MINIMO`.
- Nenhuma cena se repete dentro do mesmo vídeo.
- O vídeo nunca termina em cena de apoio: a última fala é sempre do apresentador.
- Se não houver correspondência clara, continuar com o apresentador. As cenas ocupam no máximo `TETO_CENAS` do tempo total.

Fluxo padrão:

```
Apresentador falando por INTERVALO_CENAS
→ trecho de sentido ilustrável
→ uma cena do catálogo durante todo esse trecho
→ retorno ao apresentador por pelo menos RETORNO_MINIMO
→ reinício da contagem
```

## 14. Duração das cenas de apoio

Neste documento, **trecho** significa a unidade ilustrável definida na seção 13.

Cada cena de apoio deve:

- começar exatamente no início de um trecho;
- permanecer durante o desenvolvimento desse trecho;
- terminar exatamente no final do mesmo trecho;
- apresentar começo, meio e fim semanticamente completos;
- durar somente o tempo necessário para ilustrar aquela unidade de sentido.

Limites:

- duração mínima preferencial: **2 segundos**;
- duração máxima preferencial: **6 segundos**;
- limite absoluto: **um trecho completo**;
- a cena nunca começa ou termina no meio de uma palavra;
- a cena não entra no meio do trecho;
- a cena não permanece durante o trecho seguinte;
- uma cena não ilustra dois trechos diferentes;
- um trecho não recebe duas cenas diferentes;
- se o trecho tiver menos de 2 segundos, manter o apresentador;
- se o trecho ultrapassar 6 segundos, usar a cena apenas quando o arquivo tiver duração suficiente e permanecer semanticamente relevante durante todo o trecho;
- não acelerar, desacelerar, congelar ou repetir o arquivo para preencher a duração.

## 15. Processo de decisão semântica

Para cada trecho elegível, analisar:

1. **Sentido literal:** o que está sendo dito?
2. **Função narrativa:** é dor, explicação, transformação, prova, mecanismo, urgência ou acesso?
3. **Conceito dominante:** qual é a ideia central do trecho?
4. **Classe compatível:** qual classe representa melhor essa ideia?
5. **Cena específica:** qual descrição e indicação de uso têm maior correspondência?
6. **Compatibilidade técnica:** duração, formato e orientação servem para o vídeo?
7. **Continuidade:** a cena funciona entre os trechos do apresentador falando?

A escolha considera simultaneamente:

- sentido completo do trecho;
- função narrativa;
- classe;
- descrição da cena;
- coluna "quando usar";
- duração disponível;
- formato e orientação;
- histórico de cenas já utilizadas.

## 16. Hierarquia para seleção da cena

Quando houver mais de uma possibilidade:

1. escolher a cena cuja coluna **"quando usar"** corresponda diretamente ao trecho;
2. escolher a descrição visual mais específica;
3. priorizar duração compatível;
4. priorizar formato e orientação compatíveis;
5. priorizar cenas ainda não utilizadas;
6. evitar arquivos marcados como duplicados quando o original estiver disponível;
7. em caso de dúvida semântica, manter o apresentador.

O agente não pode escolher uma cena somente por:

- coincidência de uma palavra;
- estética;
- cor;
- presença de movimento;
- necessidade de cumprir a frequência;
- associação abstrata não prevista no catálogo.

Exemplo: a palavra "caminho" não autoriza automaticamente uma cena de estrada. O trecho precisa efetivamente tratar de direção, processo, escolha ou trajetória.

## 17. Correspondência por função narrativa

Tabela-modelo, alinhada às classes da seção 11.1. Reescreva com as classes do seu catálogo.

| Função do trecho | Classes prioritárias |
| :---- | :---- |
| Explicação do método ou mecanismo | Mecanismo ou método próprio |
| Orientação prática | Passo a passo e prática |
| Ideia abstrata | Símbolos e metáforas |
| Resultado ou estado desejado | Estado desejado |
| Identidade e reflexão pessoal | Identidade e reflexão |
| Problema, sofrimento ou exaustão | Dor e problema |
| Jornada, escolha ou evolução | Jornada e escolha |
| Prazo ou urgência | Tempo e urgência |
| Acesso ao produto | Tecnologia e acesso |
| Comunidade ou acolhimento | Conexão e apoio |
| História e vida do apresentador | Bastidores do apresentador |
| Conquista e credibilidade | Prova e autoridade |
| Trecho sem correspondência clara | Gravação principal |

Esta tabela é apenas um filtro inicial. A descrição individual e o campo **"quando usar"** continuam sendo decisivos.

## 18. Inserção das cenas de apoio

- Todas as entradas e saídas são feitas por **corte seco**.
- Não usar fade, transição, zoom ou sobreposição.
- Se `EFEITO_SONORO` estiver definido, tocá-lo a cada inserção de cena **no volume original (0 dB)**. O **pico do efeito deve coincidir exatamente com o corte de entrada da cena** (o áudio começa antes do corte, o quanto for necessário para o pico cair na transição). Se estiver como "nenhum", a entrada é silenciosa.
- A cena entra no início do trecho e sai no final do mesmo trecho.
- O áudio original do apresentador continua normalmente.
- O áudio das cenas catalogadas permanece desativado.
- As legendas permanecem visíveis e seguem o mesmo padrão durante as cenas de apoio.
- A inserção visual não pode modificar o ritmo nem os cortes já realizados no áudio.

Regra definitiva:

> A cada `INTERVALO_CENAS` do apresentador na tela, procurar o próximo trecho de sentido completo que tenha correspondência clara no catálogo. Exibir uma única cena durante todo esse trecho e retornar ao apresentador ao final dele. Se não houver correspondência segura, não realizar a troca.

## 19. Ordem completa de execução

1. Receber vídeo bruto, script, catálogo e Ficha do projeto.
2. Transcrever integralmente o vídeo com timestamps por palavra, em janelas curtas.
3. Comparar a transcrição com o script oficial.
4. Localizar e selecionar as melhores tentativas de cada frase.
5. Remover erros, repetições, ruídos e conteúdo fora do script.
6. Montar a fala final exclusivamente com cortes secos.
7. Recalcular os timestamps do vídeo editado.
8. Transcrever novamente e validar o conteúdo contra o script.
9. Realizar a validação audiovisual.
10. Gerar as legendas a partir do script oficial.
11. Sincronizar e formatar as legendas.
12. Analisar semanticamente os trechos elegíveis para cenas de apoio.
13. Consultar o catálogo e selecionar somente correspondências seguras.
14. Inserir as cenas de apoio respeitando frequência, duração e cortes secos.
15. Realizar a revisão final do vídeo completo e a autocrítica (19.1).
16. Exportar no formato e enquadramento definidos na Ficha.

Com `USA_CENAS` = não, pular os passos 12 a 14.

### 19.1 Autocrítica obrigatória (regra rígida)

Antes de qualquer entrega, o vídeo final passa por autocrítica automática e é **reprovado** se qualquer item falhar:

1. **Varredura de repetições:** nenhum trigrama de palavras pode se repetir em até 8 segundos, em qualquer distância (pega regravações separadas por outras palavras, não só adjacentes). Repetições da lista de aceitas (seção 4.2) não reprovam.
2. **Sincronia labial:** duração de vídeo e áudio iguais, dentro de `TOLERANCIA_AV`.
3. **Sincronia de legenda:** início de cada bloco contra o ataque real da palavra, arbitrado por retranscrição de janela curta, dentro de `TOLERANCIA_LEGENDA`.
4. **Cobertura do script:** todas as frases presentes, na ordem.
5. **Pausas:** nenhum silêncio interno acima de `PAUSA_REPROVADA`.

O relatório da autocrítica acompanha a entrega, com timestamps de tudo que foi verificado e descartado, incluindo:

- palavras de ligação fora do script que permaneceram no áudio;
- sons altos sem transcrição que não foram cortados;
- repetições de 2 palavras pendentes de verificação de ouvido;
- trechos sem cena por falta de correspondência clara.

## 20. Critérios finais de aprovação

O vídeo só pode ser exportado quando:

- reproduzir integralmente o script oficial;
- não contiver gaguejos, correções, pigarros ou tentativas descartadas;
- não contiver pausas acima do limite;
- utilizar somente cortes secos;
- não apresentar palavras ou fonemas cortados;
- mantiver áudio e vídeo sincronizados;
- apresentar legendas literais, sincronizadas e padronizadas;
- não apresentar legendas oriundas de erros da transcrição;
- utilizar cenas de apoio somente em trechos semanticamente compatíveis;
- respeitar `INTERVALO_CENAS` sem forçar trocas;
- iniciar e finalizar cada cena de apoio nos limites de um único trecho;
- retornar ao apresentador após cada cena de apoio;
- terminar com o apresentador na tela;
- não utilizar transições, efeitos ou animações não autorizados;
- obedecer ao enquadramento e ao formato definidos na Ficha.
