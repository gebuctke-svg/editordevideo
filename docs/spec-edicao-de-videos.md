# Motor de Edição de Vídeos Baseado em Script

## 1. Objetivo

Editar automaticamente um vídeo bruto usando o script escrito como fonte oficial, eliminando erros de gravação e construindo um vídeo fluido, com cortes secos, legendas padronizadas e cenas de apoio semanticamente compatíveis.

O sistema deve:

- preservar somente o conteúdo correto do script;
- remover gaguejos, repetições, correções, pigarros e ruídos de garganta;
- eliminar intervalos e silêncios desnecessários;
- usar exclusivamente cortes secos;
- gerar legendas a partir do script oficial;
- selecionar cenas de apoio somente quando houver correspondência inequívoca com a fala;
- validar o vídeo editado antes da exportação.

## 2. Entradas

O processo recebe:

1. vídeo bruto de Isis falando;
2. script oficial em texto;
3. catálogo com 208 cenas classificadas;
4. configuração de enquadramento específica do vídeo;
5. configuração de formato e resolução de saída.

## 3. Hierarquia das fontes

Quando houver qualquer divergência, respeitar esta hierarquia:

1. **Script oficial:** determina exatamente o que deve permanecer falado e escrito.
2. **Vídeo bruto:** fornece imagem, áudio e timestamps.
3. **Transcrição técnica:** localiza as ocorrências do script e identifica erros, repetições e ruídos.
4. **Catálogo de cenas:** determina quais imagens de apoio podem ser utilizadas.
5. **Configuração do vídeo:** determina enquadramento, formato e demais regras específicas.
6. **Padrão de legendas:** determina tipografia, aparência, segmentação e posição.

O script é sempre a fonte da verdade. A transcrição nunca substitui, corrige ou reescreve o script.

**Fidelidade ao script (regra rígida):** o arquivo base é sempre o script do documento.

- As legendas reproduzem somente o script, palavra por palavra.
- Frases ou trechos falados que não existem no script (com 4 ou mais palavras, delimitados por pausas) são **removidos do áudio**.
- Palavras soltas de ligação faladas dentro de uma frase fluida (ex.: "realmente", "aqui") não podem ser extirpadas sem rasgar o áudio; elas permanecem, mas **todas são listadas no relatório de autocrítica com timestamp**, para decisão de regravação.
- Toda divergência entre fala e script aparece no relatório. Nada é silenciosamente aceito.

## 4. Transcrição técnica

Transcrever integralmente o vídeo bruto com timestamp em nível de palavra.

A transcrição deve registrar fielmente:

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

## 4.1 Precisão dos timestamps (regra rígida)

- A transcrição com timestamp por palavra é feita em **janelas curtas** (áudio segmentado nas pausas, blocos de no máximo 40 segundos), nunca no arquivo inteiro de uma vez: em arquivos longos o alinhamento deriva e chega a errar segundos.
- Timestamps de legenda e de corte saem sempre dessas janelas medidas.

## 4.2 Onde a tesoura pode descer (regra rígida)

A **decisão** do que sai vem da comparação script × transcrição timestampada. O **corte físico** obedece a estas leis, nesta ordem:

1. **Pausa, respiro e silêncio**: só se cortam quando existe um vale de energia quieto (abaixo de -22dBFS, janela de 30ms, raio de 0,25s) nas **duas pontas** do corte. Sem vale quieto, o corte **não acontece**. Cortar palavra ao meio é impossibilidade de código, não recomendação.
2. **Regravação (retake)**: sai por vão inteiro, da primeira ocorrência até a segunda, **ancorado em palavra igual** (o corte emenda dois pontos com o mesmo conteúdo fonético, o que torna o erro de timestamp inaudível). Nunca palavra a palavra.
   - A cirurgia automática só age sobre repetição de **3 ou mais palavras** não sancionada pelo script. Repetição de 2 palavras é ambígua (enumerações e anáforas legítimas da fala: "ou na sua casa, ou na sua relação", "que querem entender, que querem ir até o fim") e **sempre passa por verificação de ouvido** antes de qualquer corte.
   - Repetições e desvios confirmados como legítimos entram numa **lista de aceitas** no validador, para não reprovar de novo nas próximas rodadas.
3. **Som alto sem transcrição**: NUNCA se corta automaticamente. Pode ser fala real com timestamp deslocado. Fica no vídeo e entra no relatório para decisão humana.
4. **Improvisos da fala fluida ficam no áudio.** A fidelidade ao script se garante nas legendas e no relatório de desvios com timestamp, nunca com tesoura no meio da frase.

## 4.3 Sincronia audiovisual (regra rígida)

- Renderização em **passada única**, sem seek por pedaço; janelas de vídeo meio-abertas para que o número de frames corresponda exatamente à duração do áudio.
- Gate obrigatório: a duração da trilha de vídeo e da trilha de áudio do arquivo final não podem divergir mais de **0,04 segundo**. Divergiu, não exporta.

## 5. Alinhamento entre transcrição e script

Comparar a transcrição integral com o script oficial em nível de palavra.

Para cada frase do script, o agente deve:

1. localizar todas as ocorrências correspondentes no vídeo;
2. identificar as diferentes tentativas gravadas;
3. escolher a tentativa mais completa, clara e fluida;
4. preservar somente as palavras que formam a versão correta;
5. descartar qualquer conteúdo que não pertença ao script;
6. recorrer a partes de tentativas diferentes apenas quando necessário e quando a montagem permanecer natural e sincronizada.

Se uma frase tiver sido iniciada, interrompida e depois regravada corretamente, deve permanecer apenas a versão correta.

Exemplo de gravação bruta:

> “Você... você consegue... cof... você consegue transformar aquilo que deseja... Não, de novo. Você consegue transformar aquilo que deseja em realidade.”

Resultado:

> “Você consegue transformar aquilo que deseja em realidade.”

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

## 7. Regras de corte e ritmo

- Utilizar exclusivamente **cortes secos**.
- Não usar fades, dissoluções, transições, sobreposições ou efeitos entre tomadas.
- Uma tomada deve começar imediatamente após o término da anterior.
- Não preservar pausas dramáticas.
- O alvo de intervalo entre falas é **0,10 segundo**.
- O intervalo máximo permitido é **0,20 segundo**.
- Nunca cortar o início ou o final de uma palavra ou fonema.
- Se 0,10 segundo tornar a fala artificial, preservar o tempo mínimo necessário, sem ultrapassar 0,20 segundo.
- Não deixar silêncio antes da primeira fala nem depois da última.
- A montagem deve parecer uma fala contínua, mesmo quando formada por tomadas diferentes.

## 8. Validação textual após a montagem

Depois dos cortes, gerar uma nova transcrição do vídeo editado e compará-la com o script oficial.

O vídeo só pode avançar quando:

- todas as frases do script estiverem presentes;
- as frases estiverem na sequência correta;
- não houver conteúdo adicional;
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

- Fonte: **Figtree**
- Peso: **Bold (negrito)**
- Tamanho: **52 px**
- Capitalização: **todas as letras em maiúsculas**
- Cor: **branco**
- Alinhamento: **centralizado**
- Espaçamento entre caracteres: **0**
- Espaçamento entre linhas: **0**
- Traçado ou contorno: **desativado**
- Sombra: **desativada**

### 10.2 Fundo

- Cor: **preto**
- Opacidade: **80%** (20% de transparência)
- Expansão ou margem interna: **25**
- Arredondamento dos cantos: **20**
- O fundo deve acompanhar automaticamente o tamanho de cada bloco.
- Não utilizar caixa de fundo com largura fixa.
- Não adicionar elementos decorativos.

### 10.3 Posicionamento

- Âncora: **centro inferior**
- Posição horizontal: **0**, centralizada
- Posição vertical: **–200**
- Manter a mesma posição durante todo o vídeo.
- O enquadramento será informado separadamente em cada projeto e não deve ser deduzido pelo agente.

### 10.4 Fonte textual

As legendas devem ser geradas a partir do **script oficial**, nunca da transcrição bruta.

A transcrição serve apenas para sincronizar as palavras do script com o áudio. Assim, a legenda nunca deve reproduzir gaguejos, tentativas descartadas, repetições ou erros de gravação.

Reproduzir literalmente:

- palavras;
- grafia;
- acentuação;
- sequência das frases.

Pontuação nas legendas: **remover toda a pontuação** (vírgula, ponto, exclamação, dois-pontos, ponto e vírgula, travessão). **Manter somente o ponto de interrogação (?)**. O hífen interno de palavras compostas (ex.: vale-presente) é grafia, não pontuação, e permanece.

O agente não pode corrigir, resumir, completar, interpretar ou reescrever o texto.

### 10.5 Divisão dos blocos

- Cada legenda deve ocupar **obrigatoriamente uma única linha**.
- Cada bloco deve conter **de duas a quatro palavras**.
- A média desejada é de **três palavras por bloco**.
- Nunca exibir apenas uma palavra isolada.
- Nunca ultrapassar quatro palavras.
- Priorizar blocos de três palavras sempre que isso preservar o sentido e a naturalidade.
- Não separar artigos, preposições ou pronomes da palavra à qual estão ligados.
- Não quebrar expressões que formam uma unidade de sentido.
- A divisão deve acompanhar o ritmo da fala e formar pequenos blocos semanticamente completos.
- Se houver conflito entre a média de três palavras e a unidade de sentido, podem ser usadas duas ou quatro palavras, respeitando sempre o limite de uma linha.

Evitar:

```text
PARA
```

Preferir:

```text
PARA VOCÊ
```

### 10.6 Sincronização

- Recalcular todos os timestamps depois da edição dos cortes.
- Não reutilizar os timestamps do vídeo bruto.
- É proibido derivar os tempos das legendas da transcrição do bruto mapeada pelos cortes: o vídeo editado deve ser retranscrito com timestamp por palavra e as legendas sincronizam com esses tempos medidos no próprio vídeo final.
- Validação automática de sincronia: o início de cada bloco é comparado com o ataque da primeira palavra do bloco no áudio editado; desvio acima de 0,1 segundo reprova o bloco e exige correção antes da exportação.
- A legenda entra no início da primeira palavra do bloco.
- A legenda sai ao final da última palavra do bloco.
- A legenda não pode permanecer depois que a fala correspondente terminar.
- A legenda seguinte não pode aparecer antes do início da fala correspondente.
- Não deixar legendas atravessarem cortes quando o áudio tiver sido remontado.
- Não criar intervalo visual entre blocos quando a fala for contínua.
- Durante um silêncio real, a legenda anterior deve desaparecer ao final da fala.

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

O catálogo contém **208 cenas organizadas em 15 classes**. Cada registro possui:

- arquivo;
- classe;
- descrição da cena;
- indicação de quando usar;
- duração;
- formato;
- orientação;
- observação, incluindo a marcação de arquivos duplicados.

| Classe | Quantidade | Função principal |
| --- | ---: | --- |
| Espiral e portais | 24 | Espirais, túneis, escadarias, concha e samambaia; assinatura do mecanismo das 7 Voltas |
| Escrita e método | 25 | Caderno, mãos escrevendo, checklist e calendário; blocos de “como funciona” |
| Símbolos e metáforas | 32 | Ursinho, moedas, botão de saída, borboletas e interrogação cósmica; ideias abstratas |
| Transformação e leveza | 23 | Praia, meditação, banheira e sono tranquilo; estado desejado |
| Identidade e autoconhecimento | 17 | Espelhos, olhos e perfis; identidade, reflexão e Life Codex |
| Dor e cansaço | 9 | Exaustão, insônia e preocupação; bloco de dor |
| Cosmos e universo | 14 | Universo, manifestação e amplitude |
| Natureza e caminhos | 15 | Caminhos, ciclos, escolhas e evolução |
| Luz dourada e céu | 11 | Elevação, bênção, revelação e esperança |
| Tempo e urgência | 2 | Prazo, passagem do tempo e urgência |
| Tecnologia e acesso | 12 | Plataforma, celular, acesso e entrega |
| Conexão e apoio | 6 | Acolhimento, relacionamento, comunidade e suporte |
| Lifestyle Isis | 14 | Clipes @Gqrozz: snowboard, Egito, cruzeiro, resort e aquário |
| Prova e autoridade | 3 | Livro ACORDA!, placas de 7 dígitos e evento DONA DAY |
| Isis falando | 1 | Gravação principal no sofá e base narrativa |

## 12. Fonte visual principal

A gravação de **Isis falando** é a imagem principal do vídeo.

As demais cenas funcionam como imagens de apoio e só podem ser inseridas quando houver relação semântica inequívoca com a frase.

Na ausência de uma cena comprovadamente adequada, manter Isis falando. É preferível permanecer na gravação principal a inserir uma cena bonita, mas desconectada da fala.

## 13. Frequência das cenas de apoio

- Manter Isis falando como base.
- Procurar uma oportunidade de inserir uma cena de apoio a cada **2 a 4 segundos** de Isis na tela (alvo: uma inserção a cada **3 segundos** de retorno).
- A unidade ilustrável passa a ser a **oração ou trecho de sentido completo** (segmentos entre vírgulas e conjunções), não apenas a frase inteira. A cena cobre esse trecho do início ao fim.
- A correspondência exigida passa de "inequívoca" para **clara**: a classe e a descrição da cena precisam representar a ideia central do trecho. Continua proibido escolher cena por coincidência de uma palavra solta, por estética ou para cumprir a frequência.
- Nunca interromper um trecho no meio apenas para obedecer ao intervalo.
- Não emendar duas cenas de apoio: entre uma cena e a seguinte há sempre retorno a Isis por **no mínimo 1,5 segundo**.
- Nenhuma cena se repete dentro do mesmo vídeo.
- O vídeo nunca termina em cena de apoio: a última fala é sempre de Isis.
- Se não houver correspondência clara, continuar com Isis (Isis permanece a base; as cenas ocupam no máximo metade do tempo total).

Fluxo padrão:

```text
Isis falando por 2–4 segundos
→ trecho de sentido ilustrável
→ uma cena do catálogo durante todo esse trecho
→ retorno para Isis por pelo menos 1,5s
→ reinício da contagem
```

## 14. Duração das cenas de apoio

Cada cena de apoio deve:

- começar exatamente no início de uma frase;
- permanecer durante o desenvolvimento dessa frase;
- terminar exatamente no final da mesma frase;
- apresentar começo, meio e fim semanticamente completos;
- durar somente o tempo necessário para ilustrar aquela unidade de sentido.

Limites:

- duração mínima preferencial: **2 segundos**;
- duração máxima preferencial: **6 segundos**;
- limite absoluto: **uma frase completa**;
- a cena nunca começa ou termina no meio de uma palavra;
- a cena não entra no meio da frase;
- a cena não permanece durante a frase seguinte;
- uma cena não ilustra duas frases diferentes;
- uma frase não recebe duas cenas diferentes;
- se a frase tiver menos de 2 segundos, manter Isis falando;
- se a frase ultrapassar 6 segundos, usar a cena apenas quando o arquivo tiver duração suficiente e permanecer semanticamente relevante durante toda a frase;
- não acelerar, desacelerar, congelar ou repetir o arquivo para preencher a duração.

## 15. Processo de decisão semântica

Para cada frase elegível, analisar:

1. **Sentido literal:** o que está sendo dito?
2. **Função narrativa:** é dor, explicação, transformação, prova, mecanismo, urgência ou acesso?
3. **Conceito dominante:** qual é a ideia central da frase?
4. **Classe compatível:** qual classe representa melhor essa ideia?
5. **Cena específica:** qual descrição e indicação de uso têm maior correspondência?
6. **Compatibilidade técnica:** duração, formato e orientação servem para o vídeo?
7. **Continuidade:** a cena funciona entre os trechos de Isis falando?

A escolha deve considerar simultaneamente:

- sentido completo da frase;
- função narrativa;
- classe;
- descrição da cena;
- coluna “quando usar”;
- duração disponível;
- formato e orientação;
- histórico de cenas já utilizadas.

## 16. Hierarquia para seleção da cena

Quando houver mais de uma possibilidade:

1. escolher a cena cuja coluna **“quando usar”** corresponda diretamente à frase;
2. escolher a descrição visual mais específica;
3. priorizar duração compatível;
4. priorizar formato e orientação compatíveis;
5. priorizar cenas ainda não utilizadas;
6. evitar arquivos marcados como duplicados quando o original estiver disponível;
7. em caso de dúvida semântica, manter Isis falando.

O agente não pode escolher uma cena somente por:

- coincidência de uma palavra;
- estética;
- cor;
- presença de movimento;
- necessidade de cumprir a frequência;
- associação abstrata não prevista no catálogo.

Exemplo: a palavra “caminho” não autoriza automaticamente uma cena de estrada. A frase precisa efetivamente tratar de direção, processo, escolha ou trajetória.

## 17. Correspondência por função narrativa

| Função da frase | Classes prioritárias |
| --- | --- |
| Explicação das 7 Voltas | Espiral e portais |
| Orientação prática | Escrita e método |
| Ideia abstrata | Símbolos e metáforas |
| Resultado ou estado desejado | Transformação e leveza |
| Identidade e reflexão pessoal | Identidade e autoconhecimento |
| Problema, sofrimento ou exaustão | Dor e cansaço |
| Universo e manifestação | Cosmos e universo |
| Jornada, escolha ou evolução | Natureza e caminhos |
| Esperança, bênção ou revelação | Luz dourada e céu |
| Prazo ou urgência | Tempo e urgência |
| Acesso ao produto | Tecnologia e acesso |
| Comunidade ou acolhimento | Conexão e apoio |
| História e vida da Isis | Lifestyle Isis |
| Conquista e credibilidade | Prova e autoridade |
| Frase sem correspondência clara | Isis falando |

Esta tabela é apenas um filtro inicial. A descrição individual e o campo **“quando usar”** continuam sendo decisivos.

## 18. Inserção das cenas de apoio

- Todas as entradas e saídas são feitas por **corte seco**.
- Não usar fade, transição, zoom ou sobreposição.
- A cada inserção de cena de apoio, tocar o efeito sonoro `AUDIO/EFEITOS SONOROS AVULSOS/Whoosh_10.wav` **no volume original (0dB)**. O **pico do efeito deve coincidir exatamente com o corte de entrada da cena** (o áudio começa antes do corte, o quanto for necessário para o pico cair na transição).
- A cena entra no início da frase e sai no final da mesma frase.
- O áudio original de Isis continua normalmente.
- O áudio das cenas catalogadas permanece desativado.
- As legendas permanecem visíveis e seguem o mesmo padrão durante as cenas de apoio.
- A inserção visual não pode modificar o ritmo nem os cortes já realizados no áudio.

Regra definitiva:

> A cada 10 a 15 segundos de Isis falando, procurar a próxima frase completa que tenha correspondência inequívoca no catálogo. Exibir uma única cena durante toda essa frase e retornar para Isis ao final dela. Se não houver correspondência segura, não realizar a troca.

## 19. Ordem completa de execução

1. Receber vídeo bruto, script, catálogo e configuração específica.
2. Transcrever integralmente o vídeo com timestamps por palavra.
3. Comparar a transcrição com o script oficial.
4. Localizar e selecionar as melhores tentativas de cada frase.
5. Remover erros, repetições, ruídos e conteúdo fora do script.
6. Montar a fala final exclusivamente com cortes secos.
7. Recalcular os timestamps do vídeo editado.
8. Transcrever novamente e validar o conteúdo contra o script.
9. Realizar a validação audiovisual.
10. Gerar as legendas a partir do script oficial.
11. Sincronizar e formatar as legendas.
12. Analisar semanticamente as frases elegíveis para cenas de apoio.
13. Consultar o catálogo e selecionar somente correspondências seguras.
14. Inserir as cenas de apoio respeitando frequência, duração e cortes secos.
15. Realizar a revisão final do vídeo completo.
16. Exportar no formato e enquadramento definidos para o projeto.

## 19.1 Autocrítica obrigatória (regra rígida)

Antes de qualquer entrega, o vídeo final passa por autocrítica automática, e é **reprovado** se qualquer item falhar:

1. **Varredura de repetições**: nenhum trigrama de palavras pode se repetir em até 8 segundos, em qualquer distância (pega regravações separadas por outras palavras, não só adjacentes);
2. **Sincronia labial**: duração de vídeo e áudio iguais (tolerância 0,04s);
3. **Sincronia de legenda**: início de cada bloco contra o ataque real da palavra, arbitrado por retranscrição de janela curta (tolerância 0,12s);
4. **Cobertura do script**: todas as frases presentes, na ordem;
5. **Pausas**: nenhum silêncio interno acima de 0,30s.

O relatório da autocrítica acompanha a entrega, com timestamps de tudo que foi verificado e descartado.

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
- utilizar cenas de apoio somente em frases semanticamente compatíveis;
- respeitar o intervalo preferencial de 10 a 15 segundos sem forçar trocas;
- iniciar e finalizar cada cena de apoio nos limites de uma única frase;
- retornar para Isis falando após cada cena de apoio;
- não utilizar transições, efeitos ou animações não autorizados;
- obedecer ao enquadramento e ao formato definidos para o vídeo.
