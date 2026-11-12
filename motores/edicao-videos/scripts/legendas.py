#!/usr/bin/env python3
"""Gera as legendas a partir do script oficial, sincronizadas com a retranscrição do editado.

Uso: python3 scripts/legendas.py <pasta-da-entrega> [--png]

Lê script.txt e palavras_editado.json (tempos medidos no vídeo já cortado).
Grava blocos.json, legendas.srt e legendas.ass. Com --png (precisa do Pillow),
grava também legendas_png/NNN.png com a caixa de cantos arredondados, idêntica ao padrão.

Regras aplicadas:
- texto literal do script, sem pontuação (fica só o '?'), em caixa alta, uma linha por bloco;
- de 2 a 4 palavras por bloco, alvo de 3, sem deixar artigo, preposição ou pronome no fim do bloco;
- nenhum bloco atravessa o fim de uma frase, salvo frase de uma palavra só;
- a legenda entra no início da primeira palavra e sai no fim da última;
- em fala contínua (vão menor que 0,30 s) a legenda seguinte encosta na anterior, sem vão visual.
"""
import os
import re
import sys

from comum import (TRAVA_FIM, carregar_config, casar_script_com_fala, gravar_json, ler_json, ler_script, norm,
                   palavras_do_script, tempo_ass, tempo_srt, texto_de_legenda)


def unidades(pal_script):
    """Agrupa as palavras do script por frase. Frase de uma palavra se junta à seguinte."""
    grupos = []
    for p in pal_script:
        if grupos and grupos[-1][-1]["frase"] == p["frase"]:
            grupos[-1].append(p)
        else:
            grupos.append([p])
    saida = []
    for g in grupos:
        if saida and len(saida[-1]) < 2:
            saida[-1] = saida[-1] + g
        else:
            saida.append(g)
    if len(saida) > 1 and len(saida[-1]) < 2:
        saida[-2] = saida[-2] + saida.pop()
    return saida


INICIO_BOM = {"e", "que", "porque", "quando", "mas", "com", "para", "sempre", "se", "depois", "em", "na", "no", "ou"}


def cortes_proibidos(palavras, expressoes):
    """Posições j (corte antes da palavra j) que partiriam uma expressão inseparável."""
    ns = [norm(p["w"]) for p in palavras]
    proib = set()
    for exp in expressoes:
        alvo = [norm(w) for w in exp.split() if norm(w)]
        L = len(alvo)
        for s in range(len(ns) - L + 1):
            if L > 1 and ns[s:s + L] == alvo:
                proib.update(range(s + 1, s + L))
    return proib


def dividir(palavras, cfg_l):
    """Divide uma unidade em blocos de 2 a 4 palavras pelo menor custo."""
    n = len(palavras)
    proib = cortes_proibidos(palavras, cfg_l.get("expressoes_inseparaveis", []))
    mn, mx, alvo = cfg_l["palavras_min"], cfg_l["palavras_max"], cfg_l["palavras_alvo"]
    lim = cfg_l["caracteres_max_linha"]
    INF = float("inf")
    custo = [INF] * (n + 1)
    escolha = [0] * (n + 1)
    custo[0] = 0
    for i in range(1, n + 1):
        for k in range(mn, mx + 1):
            j = i - k
            if j < 0 or custo[j] == INF:
                continue
            bloco = palavras[j:i]
            txt = texto_de_legenda([p["w"] for p in bloco], cfg_l["pontuacao_mantida"])
            c = custo[j] + abs(k - alvo)
            if len(txt) > lim:
                c += 50
            if i < n and norm(bloco[-1]["w"]) in TRAVA_FIM:
                c += 10
            if i < n and i in proib:
                c += 20
            if i < n and re.search(r"[,;:]$", bloco[-1]["w"]):
                c -= 0.5
            if i < n and norm(palavras[i]["w"]) in INICIO_BOM:
                c -= 0.5
            if c < custo[i]:
                custo[i], escolha[i] = c, k
    if custo[n] == INF:
        return [palavras]
    blocos, i = [], n
    while i > 0:
        k = escolha[i]
        blocos.append(palavras[i - k:i])
        i -= k
    return list(reversed(blocos))


def cor_ass(hex_cor, opacidade=1.0):
    h = hex_cor.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    alfa = int(round(255 * (1 - opacidade)))
    return "&H%02X%s%s%s" % (alfa, b.upper(), g.upper(), r.upper())


def ass(blocos, cfg):
    l, s = cfg["legendas"], cfg["saida"]
    negrito = -1 if str(l["peso"]).lower() in ("bold", "negrito", "700") else 0
    estilo = ",".join(str(x) for x in [
        "Legenda", l["fonte"], l["tamanho_px"], cor_ass(l["cor"]), cor_ass(l["cor"]),
        cor_ass(l["fundo_cor"], l["fundo_opacidade"]), cor_ass(l["fundo_cor"], 0.0),
        negrito, 0, 0, 0, 100, 100, l["espacamento_letras"], 0, 3, l["fundo_margem"], l["sombra"], 2,
        l["margem_lateral"], l["margem_lateral"], abs(int(l["pos_y"])), 1])
    linhas = [
        "[Script Info]",
        "; Gerado pelo motor de edição de vídeos do Start.IA",
        "; BorderStyle 3 desenha a caixa de fundo em OutlineColour. O ASS não arredonda cantos:",
        "; para o raio de %s px exato, use legendas_png (legendas.py --png)." % l["fundo_raio"],
        "ScriptType: v4.00+",
        "PlayResX: %d" % s["largura"],
        "PlayResY: %d" % s["altura"],
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, "
        "MarginV, Encoding",
        "Style: " + estilo,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for b in blocos:
        linhas.append("Dialogue: 0,%s,%s,Legenda,,0,0,0,,%s" % (tempo_ass(b["ini"]), tempo_ass(b["fim"]), b["texto"]))
    return "\n".join(linhas) + "\n"


def srt(blocos):
    partes = []
    for i, b in enumerate(blocos, 1):
        partes.append("%d\n%s --> %s\n%s\n" % (i, tempo_srt(b["ini"]), tempo_srt(b["fim"]), b["texto"]))
    return "\n".join(partes)


def pngs(blocos, cfg, pasta):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise SystemExit("O modo --png precisa do Pillow: pip install pillow")
    l, s = cfg["legendas"], cfg["saida"]
    fonte = l.get("arquivo_fonte") or os.environ.get("FONTE_LEGENDA", "")
    if not fonte or not os.path.exists(fonte):
        raise SystemExit("Informe o arquivo .ttf da fonte em legendas.arquivo_fonte ou FONTE_LEGENDA.")
    font = ImageFont.truetype(fonte, l["tamanho_px"])
    alfa = int(round(255 * l["fundo_opacidade"]))
    pad, raio = l["fundo_margem"], l["fundo_raio"]
    destino = os.path.join(pasta, "legendas_png")
    os.makedirs(destino, exist_ok=True)
    for i, b in enumerate(blocos):
        larg = int(font.getlength(b["texto"])) + 2 * pad
        asc, desc = font.getmetrics()
        alt = asc + desc + 2 * pad
        img = Image.new("RGBA", (s["largura"], s["altura"]), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x0 = (s["largura"] - larg) // 2 + int(l["pos_x"])
        y0 = s["altura"] - abs(int(l["pos_y"])) - alt
        d.rounded_rectangle([x0, y0, x0 + larg, y0 + alt], raio, fill=(0, 0, 0, alfa))
        d.text((x0 + pad, y0 + pad), b["texto"], font=font, fill=(255, 255, 255, 255))
        img.save(os.path.join(destino, "%03d.png" % i))
    Image.new("RGBA", (s["largura"], s["altura"]), (0, 0, 0, 0)).save(os.path.join(destino, "vazio.png"))
    dur = max(b["fim"] for b in blocos)
    with open(os.path.join(destino, "concat.txt"), "w", encoding="utf-8") as f:
        t = 0.0
        for i, b in enumerate(blocos):
            if b["ini"] > t + 0.001:
                f.write("file 'vazio.png'\nduration %.6f\n" % (b["ini"] - t))
            f.write("file '%03d.png'\nduration %.6f\n" % (i, b["fim"] - b["ini"]))
            t = b["fim"]
        f.write("file 'vazio.png'\nduration %.6f\nfile 'vazio.png'\n" % max(0.04, dur - t + 0.5))
    print("%d PNGs e concat.txt em %s" % (len(blocos), destino))


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    pasta = os.path.abspath(args[0])
    cfg = carregar_config(pasta)
    l = cfg["legendas"]
    pal_script = palavras_do_script(ler_script(os.path.join(pasta, "script.txt")))
    editado = ler_json(os.path.join(pasta, "palavras_editado.json"))
    tempos, extras = casar_script_com_fala(pal_script, editado["palavras"])
    dur = float(editado.get("duracao_s") or 0)

    blocos = []
    for u, uni in enumerate(unidades(pal_script)):
        for grupo in dividir(uni, l):
            t_ini = tempos[grupo[0]["i"]]
            t_fim = tempos[grupo[-1]["i"]]
            blocos.append({
                "texto": texto_de_legenda([p["w"] for p in grupo], l["pontuacao_mantida"]),
                "palavras": [p["i"] for p in grupo],
                "unidade": u,
                "ini": t_ini[0] if t_ini else None,
                "fim": t_fim[1] if t_fim else None,
                "fala_fim": t_fim[1] if t_fim else None,
                "tempo_medido": bool(t_ini and t_fim),
            })
    # tempos que faltaram: interpola entre vizinhos e marca
    for i, b in enumerate(blocos):
        if b["ini"] is None:
            b["ini"] = blocos[i - 1]["fim"] if i else 0.0
        if b["fim"] is None:
            prox = next((c["ini"] for c in blocos[i + 1:] if c["ini"] is not None), dur or b["ini"] + 0.6)
            b["fim"] = prox
            b["fala_fim"] = prox
    # fala contínua: encosta no próximo bloco; nunca sobrepõe
    for a, b in zip(blocos, blocos[1:]):
        if b["ini"] - a["fim"] < l["vao_continuo_s"]:
            a["fim"] = b["ini"]
        if a["fim"] > b["ini"]:
            a["fim"] = b["ini"]
    for n, b in enumerate(blocos, 1):
        b["n"] = n
        b["ini"] = round(b["ini"], 3)
        b["fim"] = round(max(b["fim"], b["ini"] + 0.1), 3)
        b["fala_fim"] = round(b["fala_fim"], 3)

    gravar_json(os.path.join(pasta, "blocos.json"), {"blocos": blocos, "palavras_fora_do_script": extras})
    open(os.path.join(pasta, "legendas.srt"), "w", encoding="utf-8").write(srt(blocos))
    open(os.path.join(pasta, "legendas.ass"), "w", encoding="utf-8").write(ass(blocos, cfg))
    media = sum(len(b["texto"].split()) for b in blocos) / len(blocos)
    sem_tempo = [b["texto"] for b in blocos if not b["tempo_medido"]]
    print("%d blocos | média %.2f palavras | sem tempo medido: %s" % (len(blocos), media, sem_tempo or "nenhum"))
    if "--png" in sys.argv:
        pngs(blocos, cfg, pasta)


if __name__ == "__main__":
    main()
