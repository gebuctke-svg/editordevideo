# Edição de vídeos

O motor de edição de vídeos edita o seu vídeo bruto usando o texto que você leu como guia.

- Tira gaguejo, repetição, frase regravada, pigarro, comentário e silêncio, só com cortes secos.
- Deixa no máximo 0,20 s entre uma fala e outra, para o vídeo ficar corrido.
- Coloca legendas com o seu texto, palavra por palavra, de 2 a 4 palavras por vez, no tempo exato da fala.
- Coloca cenas de apoio do seu catálogo só quando a cena mostra o que você está dizendo.
- Confere tudo antes de entregar e diz o que precisa da sua decisão, como uma palavra dita a mais.

Você recebe o vídeo pronto e um relatório curto em `cliente/entregas/edicao-videos/`.

## Para quem instala

- **ffmpeg** (corta, junta e mede): `brew install ffmpeg` no Mac, `sudo apt install ffmpeg` no Linux. Precisa ter a biblioteca libass, que já vem no pacote comum.
- **Transcrição com tempo por palavra**, uma das duas:
  - whisper.cpp: `brew install whisper-cpp` e um modelo, como `ggml-large-v3-turbo.bin`. Informe o caminho em `transcricao.modelo` ou na variável `WHISPER_MODELO` de `cliente/.env`.
  - faster-whisper: `pip install faster-whisper` e `transcricao.motor` igual a `faster-whisper`.
- **Pillow** (opcional, só para a legenda com cantos arredondados): `pip install pillow` e o arquivo da fonte em `legendas.arquivo_fonte`.
- Os scripts usam só a biblioteca padrão do Python 3.9 ou mais novo. O `render.py --simular` e o `transcrever.py --simular-editado` rodam sem vídeo, para teste.
