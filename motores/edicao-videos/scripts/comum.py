#!/usr/bin/env python3
"""Funções comuns do motor de edição de vídeos. Só biblioteca padrão.

- configuração com padrões (templates/config_video.json) e ajustes do cliente
- normalização de palavras, números por extenso e siglas, para casar script e fala
- leitura do script em frases e palavras
- casamento entre palavras do script e palavras transcritas com tempo
"""
import copy
import difflib
import json
import os
import re
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
MOTOR = os.path.dirname(AQUI)
RAIZ = os.path.dirname(os.path.dirname(MOTOR))
TEMPLATES = os.path.join(MOTOR, "templates")


# ---------------------------------------------------------------- arquivos

def ler_json(caminho):
    return json.load(open(caminho, encoding="utf-8"))


def gravar_json(caminho, dados):
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, caminho)


def mesclar(base, extra):
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = mesclar(out[k], v)
        else:
            out[k] = v
    return out


def pasta_cliente_de(pasta_entrega):
    """A pasta do cliente é a mãe da pasta 'entregas' que contém a entrega."""
    atual = os.path.abspath(pasta_entrega)
    while True:
        mae = os.path.dirname(atual)
        if os.path.basename(atual) == "entregas":
            return mae
        if mae == atual:
            return os.environ.get("STARTIA_CLIENTE") or os.path.join(RAIZ, "cliente")
        atual = mae


def carregar_config(pasta_entrega=None, caminho=None):
    """Padrão do motor, depois cliente/edicao-videos/config.json, depois config_video.json da entrega."""
    cfg = ler_json(os.path.join(TEMPLATES, "config_video.json"))
    candidatos = []
    if pasta_entrega:
        candidatos.append(os.path.join(pasta_cliente_de(pasta_entrega), "edicao-videos", "config.json"))
        candidatos.append(os.path.join(pasta_entrega, "config_video.json"))
    if caminho:
        candidatos.append(caminho)
    for c in candidatos:
        if c and os.path.exists(c):
            cfg = mesclar(cfg, ler_json(c))
    return cfg


# ---------------------------------------------------------------- palavras

UNIDADES = ["zero", "um", "dois", "tres", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez",
            "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
DEZENAS = {20: "vinte", 30: "trinta", 40: "quarenta", 50: "cinquenta", 60: "sessenta", 70: "setenta", 80: "oitenta", 90: "noventa"}
CENTENAS = {100: "cento", 200: "duzentos", 300: "trezentos", 400: "quatrocentos", 500: "quinhentos",
            600: "seiscentos", 700: "setecentos", 800: "oitocentos", 900: "novecentos"}
VARIANTES = {"quatorze": "catorze", "pra": "para"}
SIGLAS = {"kg": ["quilos"], "km": ["quilometros"], "%": ["por", "cento"], "r$": ["reais"]}


def por_extenso(n):
    """Número inteiro de 0 a 999.999 em palavras normalizadas (sem acento)."""
    if n < 20:
        return [UNIDADES[n]]
    if n < 100:
        d, u = n // 10 * 10, n % 10
        return [DEZENAS[d]] + (["e", UNIDADES[u]] if u else [])
    if n == 100:
        return ["cem"]
    if n < 1000:
        c, r = n // 100 * 100, n % 100
        return [CENTENAS[c]] + (["e"] + por_extenso(r) if r else [])
    m, r = n // 1000, n % 1000
    cab = ["mil"] if m == 1 else por_extenso(m) + ["mil"]
    if not r:
        return cab
    return cab + (["e"] if r < 100 or r % 100 == 0 else []) + por_extenso(r)


def sem_acento(txt):
    txt = unicodedata.normalize("NFD", txt.lower())
    return "".join(c for c in txt if unicodedata.category(c) != "Mn")


def norm(palavra):
    """Forma de comparação de uma palavra: minúscula, sem acento, sem pontuação."""
    w = re.sub(r"[^a-z0-9]", "", sem_acento(palavra))
    return VARIANTES.get(w, w)


def expandir(palavra):
    """Uma palavra escrita vira a lista de palavras faladas: '21' vira 'vinte e um', 'kg' vira 'quilos'."""
    base = sem_acento(palavra).strip()
    base_limpa = re.sub(r"[^a-z0-9$%]", "", base)
    if base_limpa in SIGLAS:
        return list(SIGLAS[base_limpa])
    so_num = base_limpa.replace(".", "")
    if so_num.isdigit() and len(so_num) <= 6:
        return por_extenso(int(so_num))
    n = norm(palavra)
    return [n] if n else []


def eh_ruido(palavra):
    return palavra.strip().startswith("[") and palavra.strip().endswith("]")


# ---------------------------------------------------------------- script

def ler_script(caminho):
    return open(caminho, encoding="utf-8").read().strip()


def frases_do_script(texto):
    """Frases terminadas em . ! ? (a pontuação fica na palavra)."""
    texto = re.sub(r"\s+", " ", texto.strip())
    return [f.strip() for f in re.split(r"(?<=[.!?])\s+", texto) if f.strip()]


def palavras_do_script(texto):
    """Lista de palavras do script com frase e posição: [{'w','frase','i'}]."""
    saida = []
    for fi, fr in enumerate(frases_do_script(texto)):
        for w in fr.split():
            if norm(w) or re.sub(r"[^\d]", "", w):
                saida.append({"w": w, "frase": fi, "i": len(saida)})
    return saida


# ---------------------------------------------------------------- transcrição

def tokens_falados(palavras):
    """Transcrição [{'w','ini','fim'}] vira tokens normalizados com tempo, sem ruídos.
    Um número escrito em algarismos vira várias palavras, com o tempo dividido entre elas."""
    toks = []
    for k, p in enumerate(palavras):
        if eh_ruido(p["w"]):
            continue
        partes = expandir(p["w"])
        if not partes:
            continue
        dur = (p["fim"] - p["ini"]) / len(partes)
        for j, parte in enumerate(partes):
            toks.append({"n": parte, "ini": p["ini"] + j * dur, "fim": p["ini"] + (j + 1) * dur, "orig": k})
    return toks


def tokens_do_script(palavras_script):
    toks = []
    for p in palavras_script:
        for parte in expandir(p["w"]):
            toks.append({"n": parte, "sw": p["i"]})
    return toks


def casar_script_com_fala(palavras_script, palavras_faladas):
    """Casa cada palavra do script com o tempo medido na fala.

    Devolve (tempos, extras): tempos[i] = (ini, fim) ou None; extras = palavras faladas sem par no script.
    """
    st = tokens_do_script(palavras_script)
    ft = tokens_falados(palavras_faladas)
    sm = difflib.SequenceMatcher(None, [t["n"] for t in st], [t["n"] for t in ft], autojunk=False)
    par = {}
    extras = []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op == "equal":
            for k in range(a2 - a1):
                par[a1 + k] = b1 + k
        if op in ("insert", "replace"):
            for j in range(b1, b2):
                extras.append({"w": palavras_faladas[ft[j]["orig"]]["w"], "ini": round(ft[j]["ini"], 3), "idx": ft[j]["orig"]})
    tempos = {}
    for a, b in par.items():
        sw = st[a]["sw"]
        ini, fim = ft[b]["ini"], ft[b]["fim"]
        if sw in tempos:
            tempos[sw] = (min(tempos[sw][0], ini), max(tempos[sw][1], fim))
        else:
            tempos[sw] = (ini, fim)
    # extras que são pedaços do mesmo token original não se repetem
    vistos, unicos = set(), []
    for e in extras:
        if e["idx"] not in vistos:
            vistos.add(e["idx"])
            unicos.append(e)
    return [tempos.get(p["i"]) for p in palavras_script], unicos


# ---------------------------------------------------------------- legendas

PONTUACAO_LEGENDA = r"[.,!:;…\"“”'‘’()«»\[\]]"


def texto_de_legenda(palavras, manter="?"):
    """Tira a pontuação, mantém só o '?' e o hífen interno, e passa para caixa alta."""
    txt = " ".join(palavras)
    txt = re.sub(PONTUACAO_LEGENDA, "", txt)
    txt = re.sub(r"(^|\s)[-–—]+(\s|$)", " ", txt)
    if "?" not in manter:
        txt = txt.replace("?", "")
    return re.sub(r"\s{2,}", " ", txt).strip().upper()


def tempo_srt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def tempo_ass(t):
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return "%d:%02d:%02d.%02d" % (h, m, s, cs)


def ler_srt_ou_ass(caminho):
    """Lê blocos de legenda de um .srt ou .ass: [{'texto','ini','fim','linhas'}]."""
    t = open(caminho, encoding="utf-8-sig").read()
    blocos = []
    if caminho.lower().endswith(".ass"):
        for ln in t.splitlines():
            if not ln.startswith("Dialogue:"):
                continue
            partes = ln.split(",", 9)
            ini, fim, txt = partes[1], partes[2], partes[9]
            txt = re.sub(r"\{[^}]*\}", "", txt)
            linhas = txt.replace("\\n", "\\N").split("\\N")

            def seg(x):
                h, m, s = x.strip().split(":")
                return int(h) * 3600 + int(m) * 60 + float(s)

            blocos.append({"texto": " ".join(linhas).strip(), "ini": seg(ini), "fim": seg(fim), "linhas": len(linhas)})
        return blocos
    for bloco in re.split(r"\n\s*\n", t.strip()):
        linhas = [x for x in bloco.splitlines() if x.strip()]
        if len(linhas) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", linhas[1])
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        ini = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        fim = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        blocos.append({"texto": " ".join(linhas[2:]).strip(), "ini": ini, "fim": fim, "linhas": len(linhas) - 2})
    return blocos


# palavras que não fecham bloco: ficam presas à palavra seguinte
TRAVA_FIM = set("""o a os as um uma uns umas de da do das dos em no na nos nas num numa por pelo pela pelos pelas
para pra com sem sobre que e mas ou se te me lhe seu sua seus suas meu minha meus minhas esse essa esses essas
este esta isto aquilo aquela aquele nao ja mais muito tao qual quais quem cada nessa nesse dessa desse ao aos""".split())
