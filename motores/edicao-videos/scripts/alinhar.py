#!/usr/bin/env python3
"""Alinha a transcrição do vídeo bruto com o script oficial e monta o plano de cortes.

Uso: python3 scripts/alinhar.py <pasta-da-entrega> [--audio bruto.wav]

Lê script.txt e transcricao_bruta.json da pasta. Grava plano_cortes.json com:
- a tomada escolhida de cada frase (a última tomada completa fica);
- os trechos mantidos do bruto, em cortes secos, no grid de quadros;
- os descartes com motivo (tomada anterior, gaguejo, ruído, comentário, silêncio);
- os desvios mantidos (palavra solta dentro de fala fluida), para o relatório.

Com --audio (wav do bruto), cada corte de pausa só acontece se houver vale de energia
nas duas pontas. Sem --audio, os cortes saem só dos tempos das palavras e isso fica
registrado no plano.
"""
import argparse
import array
import difflib
import math
import os
import sys
import wave

from comum import (carregar_config, eh_ruido, frases_do_script, gravar_json, ler_json, ler_script, norm,
                   palavras_do_script, tokens_do_script, tokens_falados)

VICIOS = {"e", "eh", "ahn", "ah", "hum", "hm", "tipo", "ne", "entao"}


class Audio:
    """Leitura simples de wav mono ou estéreo de 16 bits para medir vales de energia."""

    def __init__(self, caminho):
        w = wave.open(caminho, "rb")
        self.sr = w.getframerate()
        canais = w.getnchannels()
        if w.getsampwidth() != 2:
            raise SystemExit("O wav precisa ter 16 bits. Converta com: ffmpeg -i bruto.mp4 -ac 1 -ar 16000 bruto.wav")
        dados = array.array("h", w.readframes(w.getnframes()))
        self.am = dados[::canais]

    def db_minimo(self, t, raio, lo=None, hi=None):
        n = int(0.03 * self.sr)
        a = int(max(t - raio, lo if lo is not None else 0) * self.sr)
        b = int(min(t + raio, hi if hi is not None else t + raio) * self.sr)
        melhor = None
        j = max(0, a)
        while j + n <= min(len(self.am), b):
            seg = self.am[j:j + n]
            rms = math.sqrt(sum(x * x for x in seg) / n) / 32768.0
            melhor = rms if melhor is None else min(melhor, rms)
            j += n // 2
        return -99.0 if melhor is None else 20 * math.log10(melhor + 1e-9)


def achar_exatos(seq, alvo, desde):
    L = len(alvo)
    return [j for j in range(desde, len(seq) - L + 1) if seq[j:j + L] == alvo]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrega")
    ap.add_argument("--audio")
    a = ap.parse_args()
    pasta = os.path.abspath(a.entrega)
    cfg = carregar_config(pasta)
    cc = cfg["cortes"]
    fps = float(cfg["saida"]["fps"])

    script = ler_script(os.path.join(pasta, "script.txt"))
    frases = frases_do_script(script)
    pal_script = palavras_do_script(script)
    bruta = ler_json(os.path.join(pasta, "transcricao_bruta.json"))
    palavras = bruta["palavras"]
    ft = tokens_falados(palavras)
    seq = [t["n"] for t in ft]

    # tokens de cada frase do script
    ftoks = [[] for _ in frases]
    for t in tokens_do_script(pal_script):
        ftoks[pal_script[t["sw"]]["frase"]].append(t["n"])

    escolhas, ausentes = [], []
    cursor = 0
    for fi, F in enumerate(ftoks):
        L = len(F)
        cands = achar_exatos(seq, F, cursor)
        if cands:
            limite = len(seq) + 1
            if fi + 1 < len(ftoks):
                prox = achar_exatos(seq, ftoks[fi + 1], cands[0] + L)
                if prox:
                    limite = prox[0]
            validos = [c for c in cands if c + L <= limite] or [cands[0]]
            j = validos[-1]
            escolhas.append({"frase": fi, "a": j, "b": j + L, "casamento": "exato", "tomadas": len(validos), "razao": 1.0})
            cursor = j + L
            continue
        melhor = None
        for j in range(cursor, min(len(seq), cursor + 3 * L + 40)):
            for L2 in range(max(1, L - 3), L + 4):
                if j + L2 > len(seq):
                    break
                r = difflib.SequenceMatcher(None, F, seq[j:j + L2], autojunk=False).ratio()
                if melhor is None or r > melhor[0] + 1e-9 or (abs(r - melhor[0]) < 1e-9 and j > melhor[1]):
                    melhor = (r, j, j + L2)
        if melhor and melhor[0] >= cc["casamento_minimo"]:
            escolhas.append({"frase": fi, "a": melhor[1], "b": melhor[2], "casamento": "aproximado", "tomadas": 1,
                             "razao": round(melhor[0], 3)})
            cursor = melhor[2]
        else:
            ausentes.append({"frase": fi, "texto": frases[fi]})

    # palavras originais mantidas, cortes internos e desvios
    manter = []           # índices de palavras originais mantidas, em ordem
    quebra_forcada = set()  # índice k: há corte antes da palavra k
    desvios = []
    cortes_internos = []
    for e in escolhas:
        span = ft[e["a"]:e["b"]]
        F = ftoks[e["frase"]]
        extras_orig = set()
        if e["casamento"] != "exato":
            sm = difflib.SequenceMatcher(None, F, [t["n"] for t in span], autojunk=False)
            for op, a1, a2, b1, b2 in sm.get_opcodes():
                if op in ("insert", "replace"):
                    for j in range(b1, b2):
                        extras_orig.add(span[j]["orig"])
        o_ini, o_fim = span[0]["orig"], span[-1]["orig"]
        for k in range(o_ini, o_fim + 1):
            p = palavras[k]
            if eh_ruido(p["w"]):
                cortes_internos.append({"ini": p["ini"], "fim": p["fim"], "texto": p["w"], "motivo": "ruído dentro da frase"})
                quebra_forcada.add(k + 1)
                continue
            if k in extras_orig:
                ant = palavras[k - 1] if k > o_ini else None
                pro = palavras[k + 1] if k < o_fim else None
                folga_a = p["ini"] - ant["fim"] if ant else 9
                folga_d = pro["ini"] - p["fim"] if pro else 9
                vizinho = {norm(x["w"]) for x in (ant, pro) if x}
                if norm(p["w"]) in vizinho and folga_a >= cc["gaguejo_folga_min_s"] and folga_d >= cc["gaguejo_folga_min_s"]:
                    cortes_internos.append({"ini": p["ini"], "fim": p["fim"], "texto": p["w"], "motivo": "gaguejo (palavra repetida)"})
                    quebra_forcada.add(k + 1)
                    continue
                desvios.append({"w": p["w"], "ini_bruto": p["ini"], "frase": e["frase"],
                                "motivo": "palavra solta dentro de fala fluida: fica no áudio, a legenda segue o script"})
            manter.append(k)

    # segmentos: quebra quando há corte entre palavras ou pausa acima do máximo
    segs = []
    for k in manter:
        if segs:
            ult = segs[-1][-1]
            pausa = palavras[k]["ini"] - palavras[ult]["fim"]
            if k == ult + 1 and k not in quebra_forcada and pausa <= cc["intervalo_max_s"]:
                segs[-1].append(k)
                continue
        segs.append([k])

    audio = Audio(a.audio) if a.audio else None
    avisos = []

    def em_grade(lo, hi, alvo):
        """Quadro mais perto do alvo dentro de [lo, hi]. Sem quadro possível, devolve o alvo."""
        q0, q1 = math.ceil(lo * fps - 1e-6), math.floor(hi * fps + 1e-6)
        if q0 > q1:
            return round(alvo, 4), False
        q = min(max(round(alvo * fps), q0), q1)
        return round(q / fps, 5), True

    trechos = []
    for s in segs:
        pri, ult = palavras[s[0]], palavras[s[-1]]
        ant_fim = palavras[s[0] - 1]["fim"] if s[0] > 0 else 0.0
        pro_ini = palavras[s[-1] + 1]["ini"] if s[-1] + 1 < len(palavras) else bruta.get("duracao_s", ult["fim"] + 1)
        m_ini = min(cc["margem_palavra_s"], (pri["ini"] - ant_fim) / 2.0)
        m_fim = min(cc["margem_palavra_s"], (pro_ini - ult["fim"]) / 2.0)
        ini, ok1 = em_grade(max(ant_fim, pri["ini"] - 2 * m_ini), pri["ini"], pri["ini"] - m_ini)
        fim, ok2 = em_grade(ult["fim"], min(pro_ini, ult["fim"] + 2 * m_fim), ult["fim"] + m_fim)
        if not (ok1 and ok2):
            avisos.append("corte fora do grid de quadros perto de %.2f s (vão menor que 1 quadro)" % pri["ini"])
        if audio:
            for t, lo, hi in ((ini, ant_fim, pri["ini"]), (fim, ult["fim"], pro_ini)):
                db = audio.db_minimo(t, cc["raio_vale_s"], lo, hi)
                if db > cc["vale_db"]:
                    avisos.append("corte em %.2f s sem vale de energia (%.1f dB): conferir de ouvido" % (t, db))
        trechos.append([ini, fim, s])

    # funde trechos que se tocam
    fundidos = []
    for ini, fim, s in trechos:
        if fundidos and ini <= fundidos[-1][1] + 1e-6:
            fundidos[-1][1] = max(fundidos[-1][1], fim)
            fundidos[-1][2] += s
        else:
            fundidos.append([ini, fim, list(s)])

    # descartes: o que ficou entre os trechos mantidos
    todas_script = {n for F in ftoks for n in F}
    frase_da_palavra = {}
    for e in escolhas:
        for t in ft[e["a"]:e["b"]]:
            frase_da_palavra[t["orig"]] = e["frase"]
    ja_cortadas = {(c["ini"], c["fim"]) for c in cortes_internos}
    descartes = []
    limites = [(0.0, fundidos[0][0])] + [(fundidos[i][1], fundidos[i + 1][0]) for i in range(len(fundidos) - 1)] \
        + [(fundidos[-1][1], bruta.get("duracao_s", fundidos[-1][1]))]
    for i, (x, y) in enumerate(limites):
        if y - x < 1e-3:
            continue
        dentro = [p for p in palavras if p["ini"] >= x - 1e-6 and p["fim"] <= y + 1e-6]
        if dentro and all((p["ini"], p["fim"]) in ja_cortadas for p in dentro):
            continue
        falas = [p for p in dentro if not eh_ruido(p["w"])]
        ns = [n for p in falas for n in ([norm(p["w"])] if norm(p["w"]) else [])]
        if i < len(fundidos):
            prox_F = ftoks[frase_da_palavra.get(fundidos[i][2][0], 0)]
        else:
            prox_F = []
        if not dentro:
            motivo = "silêncio ou pausa longa"
        elif not falas:
            motivo = "ruído: " + ", ".join(p["w"] for p in dentro)
        elif len(ns) == 1 and ns[0] in VICIOS:
            motivo = "vício de linguagem"
        elif ns and sum(1 for n in ns if n in prox_F) / len(ns) >= 0.6:
            motivo = "tomada anterior ou falso começo (fica a última tomada)"
        elif ns and sum(1 for n in ns if n in todas_script) / len(ns) < 0.5:
            motivo = "comentário fora do script"
        else:
            motivo = "trecho fora do script"
        descartes.append({"ini": round(x, 3), "fim": round(y, 3), "texto": " ".join(p["w"] for p in dentro), "motivo": motivo})
    for c in cortes_internos:
        descartes.append({"ini": c["ini"], "fim": c["fim"], "texto": c["texto"], "motivo": c["motivo"]})
    descartes.sort(key=lambda d: d["ini"])

    keeps = [[round(i, 5), round(f, 5)] for i, f, _ in fundidos]

    def bruto_para_editado(t):
        acc = 0.0
        for i, f in keeps:
            if t < i:
                return acc
            if t <= f:
                return acc + t - i
            acc += f - i
        return acc

    dur_ed = round(sum(f - i for i, f in keeps), 3)
    for d in desvios:
        d["ini_editado"] = round(bruto_para_editado(d["ini_bruto"]), 3)

    # maior intervalo entre palavras mantidas, já no tempo editado
    maior = 0.0
    mantidas = [k for _, _, s in fundidos for k in s]
    for k0, k1 in zip(mantidas, mantidas[1:]):
        g = bruto_para_editado(palavras[k1]["ini"]) - bruto_para_editado(palavras[k0]["fim"])
        maior = max(maior, g)

    plano = {
        "fps": fps,
        "fonte_transcricao": bruta.get("fonte", ""),
        "vale_de_energia": "medido no wav" if audio else "não medido (sem --audio): conferir cortes de ouvido",
        "duracao_bruto_s": bruta.get("duracao_s"),
        "duracao_editado_s": dur_ed,
        "maior_intervalo_editado_s": round(maior, 3),
        "trechos": keeps,
        "frases": [{"frase": e["frase"], "texto": frases[e["frase"]],
                    "tomada_bruto": [palavras[ft[e["a"]]["orig"]]["ini"], palavras[ft[e["b"] - 1]["orig"]]["fim"]],
                    "tomadas_encontradas": e["tomadas"], "casamento": e["casamento"], "razao": e["razao"]} for e in escolhas],
        "frases_ausentes": ausentes,
        "descartes": descartes,
        "desvios_mantidos": desvios,
        "avisos": avisos,
    }
    gravar_json(os.path.join(pasta, "plano_cortes.json"), plano)
    print("frases: %d de %d | trechos: %d | bruto %.2f s -> editado %.2f s | descartes: %d | desvios: %d | maior intervalo %.3f s"
          % (len(escolhas), len(frases), len(keeps), bruta.get("duracao_s", 0), dur_ed, len(descartes), len(desvios), maior))
    for d in descartes:
        print("  corta %7.2f-%7.2f %-48s %s" % (d["ini"], d["fim"], d["motivo"][:48], d["texto"][:50]))
    for d in desvios:
        print("  mantém '%s' em %.2f s (editado): %s" % (d["w"], d["ini_editado"], d["motivo"]))
    for x in ausentes:
        print("  FRASE AUSENTE: " + x["texto"])
    for x in avisos:
        print("  aviso: " + x)
    sys.exit(1 if ausentes else 0)


if __name__ == "__main__":
    main()
