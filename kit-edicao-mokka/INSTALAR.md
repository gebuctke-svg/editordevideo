# Instalação do Kit de Edição Mokka

Instruções para o Claude Code. A aluna anexa o arquivo `KIT-EDICAO-MOKKA.zip` e escreve "instale o arquivo em anexo". Siga os passos abaixo na ordem, avisando em uma linha o que fez em cada um.

## 1. Descompactar
- Descompacte o zip na raiz do projeto aberto, numa pasta chamada `kit-edicao-mokka/`.
- Se a pasta já existir, não apague nada: pergunte se é para atualizar e só substitua os arquivos do kit, nunca os vídeos da aluna.

## 2. Criar as pastas de trabalho
Na raiz do projeto, ao lado do kit:
```
brutos/       vídeos originais, nunca alterados
prontos/      resultado final de cada edição
```
Se a descrição do projeto já pedir essas pastas, só confira que existem.

## 3. Instalar as fontes
As fontes estão em `kit-edicao-mokka/assets/fontes/` (licença OFL, livres).
- **Mac:** copie os `.ttf` para `~/Library/Fonts/`.
- **Windows:** copie para `%LOCALAPPDATA%\Microsoft\Windows\Fonts\` e registre cada uma em `HKCU\Software\Microsoft\Windows NT\CurrentVersion\Fonts`, ou peça para a aluna dar dois cliques em cada arquivo e clicar em Instalar.
- **Linux:** copie para `~/.local/share/fonts/` e rode `fc-cache -f`.

## 4. Conferir as ferramentas de vídeo
Para editar, o Claude Code usa `ffmpeg` (corte, legenda, som, exportação) e `python3`.
- Rode `ffmpeg -version` e `python3 --version`.
- Se faltar alguma, **pergunte antes de instalar** e explique em uma frase para que serve.
  - Mac: `brew install ffmpeg` (se não tiver Homebrew, mostre o comando de instalação do site brew.sh e peça autorização).
  - Windows: `winget install Gyan.FFmpeg` e `winget install Python.Python.3.12`.

## 5. Gravar as instruções do projeto
A descrição do projeto escrita pela aluna manda. O `CLAUDE.md` do kit só complementa com as regras de edição.
Copie `kit-edicao-mokka/CLAUDE.md` para a raiz do projeto como `CLAUDE.md`. Se já existir um `CLAUDE.md`, acrescente o conteúdo no fim, sem apagar o que estava lá.

## 6. Teste
- Liste as pastas do kit e diga quantos efeitos há em `referencias/` e quantos sons em `sfx/`.
- Se o ffmpeg estiver instalado, gere `prontos/teste-som.mp3` juntando `pop.mp3`, `whoosh.mp3` e `success.mp3` em sequência, para provar que tudo funciona.

## 7. Fechamento
Responda em português, curto:
- o que foi instalado;
- o que ficou faltando e por quê;
- o próximo passo: "Coloque um vídeo em `brutos/` e me diga qual receita do Guia 08 quer usar."
