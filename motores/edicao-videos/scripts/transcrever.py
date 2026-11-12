#!/usr/bin/env python3
"""Transcreve um áudio com tempo por palavra, em janelas curtas, e grava o JSON de palavras.

Uso:
  python3 scripts/transcrever.py <audio.wav> <saida.json> [--config cfg.json] [--motor whisper-cpp|faster-whisper]
  python3 scripts/transcrever.py --simular-editado <pasta-da-entrega>
  python3 scripts/transcrever.py --verificar      confere ffmpeg, whisper-cli e o modelo, e ensina a instalar

Configuração: sem --config, lê o padrão do motor, cliente/edicao-videos/config.json e o
config_video.json da pasta da saída. Carrega também cliente/.env (WHISPER_MODELO).

Modelo do whisper.cpp (transcricao.modelo ou WHISPER_MODELO): pode ser o caminho do arquivo .bin
ou só o nome, como large-v3-turbo. Pelo nome, o script procura ggml-<nome>.bin em
~/.cache/whisper, ~/.cache/whisper.cpp, ~/whisper.cpp/models, ~/models, cliente/edicao-videos/modelos,
/opt/homebrew/share/whisper-cpp, /usr/local/share/whisper-cpp e /usr/share/whisper.cpp/models.

Modo real:
  - quebra o áudio nas pausas (ffmpeg silencedetect) em janelas de no máximo 38 s;
  - transcreve cada janela com whisper-cli (whisper.cpp, com --dtw) ou faster-whisper;
  - devolve {"fonte", "duracao_s", "palavras": [{"w","ini","fim"}]}.
  Janelas curtas evitam a deriva de tempo que aparece em arquivos longos.
  Use no bruto (transcricao_bruta.json) e depois de novo no editado (palavras_editado.json).

Modo --simular-editado (exemplo e teste, sem vídeo):
  gera palavras_editado.json a partir de transcricao_bruta.json e plano_cortes.json,
  como se o editado tivesse sido retranscrito, com pequeno erro de medição.
  Nunca use este modo num vídeo real: a regra exige retranscrever o editado.
"""
import glob
import json
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import tempfile

from comum import RAIZ, carregar_config, gravar_json, ler_json, pasta_cliente_de

URL_MODELOS = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-%s.bin"
PASTAS_MODELO = ["~/.cache/whisper", "~/.cache/whisper.cpp", "~/whisper.cpp/models", "~/models",
                 "/opt/homebrew/share/whisper-cpp", "/usr/local/share/whisper-cpp", "/usr/share/whisper.cpp/models"]


def carregar_env(cliente):
    """Lê cliente/.env sem sobrescrever o que já está no ambiente. Nunca imprime valores."""
    arq = os.path.join(cliente, ".env")
    if not os.path.exists(arq):
        return
    for linha in open(arq, encoding="utf-8", errors="replace"):
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def como_instalar():
    if platform.system() == "Darwin":
        return "No Terminal, com Homebrew: brew install ffmpeg whisper-cpp"
    if platform.system() == "Windows":
        return "Instale o ffmpeg (winget install Gyan.FFmpeg) e o whisper.cpp (versão pronta em github.com/ggerganov/whisper.cpp/releases), ou use --motor faster-whisper com: pip install faster-whisper"
    return "Ubuntu e Debian: sudo apt install ffmpeg. whisper.cpp: compile pelo guia em github.com/ggerganov/whisper.cpp, ou use --motor faster-whisper com: pip install faster-whisper"


def achar_modelo(t, cliente=None):
    """Caminho do modelo .bin do whisper.cpp, ou None. Aceita caminho ou nome (large-v3-turbo)."""
    pedidos = [x for x in (t.get("modelo"), os.environ.get("WHISPER_MODELO")) if x]
    pastas = [os.path.expanduser(p) for p in PASTAS_MODELO]
    if cliente:
        pastas.insert(0, os.path.join(cliente, "edicao-videos", "modelos"))
    for p in pedidos:
        c = os.path.expanduser(p)
        if os.path.isfile(c):
            return c
        nome = os.path.basename(c)
        nomes = [nome] if nome.endswith(".bin") else ["ggml-%s.bin" % nome, "%s.bin" % nome]
        for pasta in pastas:
            for n in nomes:
                if os.path.isfile(os.path.join(pasta, n)):
                    return os.path.join(pasta, n)
    if not pedidos:  # sem nome pedido: qualquer ggml-*.bin de verdade (nunca o de teste)
        for pasta in pastas:
            for c in sorted(glob.glob(os.path.join(pasta, "ggml-*.bin"))):
                if "for-tests" not in os.path.basename(c):
                    return c
    return None


def modelo_faltando(t):
    nome = os.path.basename(t.get("modelo") or os.environ.get("WHISPER_MODELO") or "large-v3-turbo")
    nome = re.sub(r"^ggml-|\.bin$", "", nome) or "large-v3-turbo"
    destino = os.path.expanduser("~/.cache/whisper/ggml-%s.bin" % nome)
    return ("Modelo do whisper não encontrado (pedido: %s). Baixe uma vez, cerca de 1,6 GB:\n"
            "  mkdir -p ~/.cache/whisper && curl -L -o %s %s\n"
            "Depois grave em cliente/.env a linha WHISPER_MODELO=%s (ou só o nome: WHISPER_MODELO=%s).\n"
            "Para conferir: python3 motores/edicao-videos/scripts/transcrever.py --verificar"
            % (t.get("modelo") or os.environ.get("WHISPER_MODELO") or "nenhum", destino, URL_MODELOS % nome, destino, nome))


def verificar(cfg, cliente):
    t = cfg["transcricao"]
    ok = True
    for prog in ("ffmpeg", "ffprobe"):
        achou = shutil.which(prog)
        print(("PASSA " if achou else "VOLTA ") + prog + (": " + achou if achou else ": não instalado. " + como_instalar()))
        ok = ok and bool(achou)
    exe = shutil.which(t.get("executavel", "whisper-cli"))
    try:
        import faster_whisper  # noqa: F401
        fw = True
    except ImportError:
        fw = False
    print(("PASSA " if exe else "AVISO ") + "whisper-cli" + (": " + exe if exe else ": não instalado. " + como_instalar()))
    print(("PASSA " if fw else "AVISO ") + "faster-whisper" + (": instalado" if fw else ": não instalado (opcional: pip install faster-whisper)"))
    modelo = achar_modelo(t, cliente)
    if exe:
        print(("PASSA modelo: " + modelo) if modelo else "VOLTA " + modelo_faltando(t))
        ok = ok and bool(modelo)
    if not exe and not fw:
        print("VOLTA nenhum transcritor instalado: instale o whisper-cli ou o faster-whisper")
        ok = False
    return 0 if ok else 1


def duracao(caminho):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", caminho],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def janelas(caminho, cfg):
    t = cfg["transcricao"]
    dur = duracao(caminho)
    out = subprocess.run(["ffmpeg", "-i", caminho, "-af", "silencedetect=noise=%sdB:d=%s" % (t["silencio_db"], t["silencio_min_s"]),
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    pontos, cur = [], None
    for m in re.finditer(r"silence_(start|end): ([0-9.]+)", out):
        if m.group(1) == "start":
            cur = float(m.group(2))
        elif cur is not None:
            pontos.append((cur + float(m.group(2))) / 2)
    js, ini = [], 0.0
    while ini < dur - 0.2:
        limite = ini + t["janela_max_s"]
        cand = [p for p in pontos if ini + 8 < p <= limite]
        fim = cand[-1] if cand else min(limite, dur)
        if dur - fim < 6:
            fim = dur
        js.append((round(ini, 3), round(fim, 3)))
        ini = fim
    return js, dur


def whisper_cpp(wav, ini, cfg):
    t = cfg["transcricao"]
    modelo = achar_modelo(t, cfg.get("_cliente"))
    if not modelo:
        raise SystemExit(modelo_faltando(t))
    if not shutil.which(t.get("executavel", "whisper-cli")):
        raise SystemExit("whisper-cli não instalado. " + como_instalar())
    base = wav[:-4]
    subprocess.run([t.get("executavel", "whisper-cli"), "-m", modelo, "-f", wav, "-l", t["idioma"],
                    "-nfa", "--dtw", t.get("dtw", "large.v3.turbo"), "-ojf", "-of", base], capture_output=True)
    dd = json.load(open(base + ".json", encoding="utf-8"))
    palavras = []
    for seg in dd.get("transcription", []):
        for tok in seg.get("tokens", []):
            txt = tok.get("text", "")
            if txt.startswith("[_") or not txt.strip():
                continue
            ts = ini + tok.get("t_dtw", 0) / 100.0
            if palavras and not txt.startswith(" "):
                palavras[-1]["w"] += txt
                palavras[-1]["fim"] = max(palavras[-1]["fim"], ts)
            else:
                palavras.append({"w": txt.strip(), "ini": ts, "fim": ts})
    for i in range(len(palavras) - 1):
        dur_max = max(0.15, 0.05 + 0.055 * len(palavras[i]["w"]))
        palavras[i]["fim"] = min(palavras[i + 1]["ini"], palavras[i]["ini"] + dur_max)
    if palavras:
        palavras[-1]["fim"] = palavras[-1]["ini"] + 0.35
    return palavras


def faster_whisper(wav, ini, cfg, cache={}):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("faster-whisper não instalado: pip install faster-whisper")
    t = cfg["transcricao"]
    if "m" not in cache:
        nome = t.get("modelo") or os.environ.get("WHISPER_MODELO") or "large-v3-turbo"
        if nome.endswith(".bin"):  # arquivo do whisper.cpp não serve no faster-whisper: usa o nome
            nome = re.sub(r"^ggml-|\.bin$", "", os.path.basename(nome))
        cache["m"] = WhisperModel(nome)
    segs, _ = cache["m"].transcribe(wav, language=t["idioma"], word_timestamps=True)
    return [{"w": w.word.strip(), "ini": ini + w.start, "fim": ini + w.end} for s in segs for w in (s.words or [])]


def real(audio, saida, cfg, motor):
    for prog in ("ffmpeg", "ffprobe"):
        if not shutil.which(prog):
            raise SystemExit("%s não instalado. %s" % (prog, como_instalar()))
    js, dur = janelas(audio, cfg)
    todas = []
    with tempfile.TemporaryDirectory() as tmp:
        for a, b in js:
            w = os.path.join(tmp, "jan_%.2f_%.2f.wav" % (a, b))
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-to", str(b), "-i", audio, "-ac", "1", "-ar", "16000", w],
                           check=True)
            fn = whisper_cpp if motor == "whisper-cpp" else faster_whisper
            todas += fn(w, a, cfg)
    todas = [{"w": p["w"], "ini": round(p["ini"], 3), "fim": round(p["fim"], 3)} for p in todas if p["w"]]
    gravar_json(saida, {"fonte": "%s, %d janelas" % (motor, len(js)), "arquivo": os.path.basename(audio),
                        "duracao_s": round(dur, 3), "palavras": todas})
    print("%d janelas, %d palavras -> %s" % (len(js), len(todas), saida))


def simular_editado(pasta):
    bruta = ler_json(os.path.join(pasta, "transcricao_bruta.json"))
    plano = ler_json(os.path.join(pasta, "plano_cortes.json"))
    keeps = plano["trechos"]
    rnd = random.Random(11)

    def mapa(t):
        acc = 0.0
        for i, f in keeps:
            if t < i:
                return None
            if t <= f:
                return acc + t - i
            acc += f - i
        return None

    saida = []
    for p in bruta["palavras"]:
        a, b = mapa(p["ini"]), mapa(p["fim"])
        if a is None or b is None or b <= a:
            continue
        if p["w"].startswith("["):
            continue
        erro = rnd.uniform(-0.02, 0.02)
        saida.append({"w": p["w"], "ini": round(max(0.0, a + erro), 3), "fim": round(b + erro, 3)})
    for x, y in zip(saida, saida[1:]):
        if y["ini"] < x["fim"]:
            y["ini"] = x["fim"]
    gravar_json(os.path.join(pasta, "palavras_editado.json"), {
        "fonte": "simulada para o exemplo: retranscrição do editado com erro de medição de até 0,02 s",
        "arquivo": "base.wav", "duracao_s": plano["duracao_editado_s"], "palavras": saida})
    print("%d palavras no editado simulado -> palavras_editado.json" % len(saida))


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="?")
    ap.add_argument("saida", nargs="?")
    ap.add_argument("--config")
    ap.add_argument("--motor")
    ap.add_argument("--simular-editado", metavar="PASTA")
    ap.add_argument("--verificar", action="store_true")
    a = ap.parse_args()
    if a.simular_editado:
        simular_editado(os.path.abspath(a.simular_editado))
        return
    if a.verificar:
        cliente = os.environ.get("STARTIA_CLIENTE") or os.path.join(RAIZ, "cliente")
        carregar_env(cliente)
        sys.exit(verificar(carregar_config(caminho=a.config), cliente))
    if not a.audio or not a.saida:
        ap.print_help()
        sys.exit(2)
    entrega = os.path.dirname(os.path.abspath(a.saida))
    cliente = pasta_cliente_de(entrega)
    carregar_env(cliente)
    cfg = carregar_config(pasta_entrega=entrega, caminho=a.config)
    cfg["_cliente"] = cliente
    real(a.audio, a.saida, cfg, a.motor or cfg["transcricao"]["motor"])


if __name__ == "__main__":
    main()
