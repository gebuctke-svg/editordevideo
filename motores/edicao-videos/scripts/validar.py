#!/usr/bin/env python3
"""Valida uma entrega do motor de edição de vídeos.

Uso:
  python3 scripts/validar.py <pasta-da-entrega>
  python3 scripts/validar.py <legendas.srt|legendas.ass> [--script script.txt] [--palavras palavras_editado.json]

Confere as legendas contra o script oficial e as regras de bloco, a sincronia contra o JSON
de tempos por palavra do editado, o texto do editado contra o script (cobertura, ordem,
conteúdo a mais, repetições e intervalos), o plano de cortes e as cenas de apoio.
Imprime PASSA ou VOLTA por checagem e sai com 0 se tudo passou.
"""
import argparse
import os
import re
import sys

from comum import (PONTUACAO_LEGENDA, TRAVA_FIM, carregar_config, casar_script_com_fala, frases_do_script, ler_json,
                   ler_script, ler_srt_ou_ass, norm, palavras_do_script, texto_de_legenda, tokens_falados)

RES = []


def checa(nome, ok, motivo=""):
    RES.append(bool(ok))
    print(("PASSA " if ok else "VOLTA ") + nome + ("" if ok or not motivo else ": " + motivo))


def divisao_possivel(palavras, cfg_l, proib):
    """Existe divisão da unidade em blocos de 2 a 4 palavras sem prender artigo ou preposição no fim
    e sem partir expressão inseparável?"""
    n = len(palavras)
    ok = [False] * (n + 1)
    ok[0] = True
    for i in range(1, n + 1):
        for k in range(cfg_l["palavras_min"], cfg_l["palavras_max"] + 1):
            j = i - k
            if j < 0 or not ok[j]:
                continue
            if i < n and (norm(palavras[i - 1]["w"]) in TRAVA_FIM or i in proib):
                continue
            if len(texto_de_legenda([p["w"] for p in palavras[j:i]])) > cfg_l["caracteres_max_linha"]:
                continue
            ok[i] = True
            break
    return ok[n]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("alvo")
    ap.add_argument("--script")
    ap.add_argument("--palavras")
    a = ap.parse_args()
    alvo = os.path.abspath(a.alvo)
    pasta = alvo if os.path.isdir(alvo) else os.path.dirname(alvo)
    cfg = carregar_config(pasta)
    cl, cc = cfg["legendas"], cfg["cortes"]
    arq_leg = [alvo] if os.path.isfile(alvo) else [os.path.join(pasta, x) for x in ("legendas.srt", "legendas.ass")
                                                    if os.path.exists(os.path.join(pasta, x))]
    script_p = a.script or os.path.join(pasta, "script.txt")
    pal_p = a.palavras or os.path.join(pasta, "palavras_editado.json")
    for nome, p in (("script oficial", script_p), ("tempos por palavra do editado", pal_p)):
        checa("arquivo: " + nome, os.path.exists(p), p)
    checa("arquivo de legenda (.srt ou .ass)", bool(arq_leg))
    if not all(RES):
        sys.exit(1)

    script = ler_script(script_p)
    frases = frases_do_script(script)
    pal_script = palavras_do_script(script)
    editado = ler_json(pal_p)
    pal_ed = editado["palavras"]
    tempos, extras = casar_script_com_fala(pal_script, pal_ed)
    esperado = texto_de_legenda([p["w"] for p in pal_script], cl["pontuacao_mantida"]).split()
    plano = ler_json(os.path.join(pasta, "plano_cortes.json")) if os.path.exists(os.path.join(pasta, "plano_cortes.json")) else None

    # ------------------------------------------------ legendas
    for arq in arq_leg:
        tag = os.path.basename(arq)
        blocos = ler_srt_ou_ass(arq)
        checa("%s: blocos lidos" % tag, len(blocos) > 0, "nenhum bloco")
        if not blocos:
            continue
        uma_linha = [b["texto"] for b in blocos if b["linhas"] != 1]
        checa("%s: uma linha por bloco" % tag, not uma_linha, "; ".join(uma_linha[:3]))
        fora = [b["texto"] for b in blocos if not cl["palavras_min"] <= len(b["texto"].split()) <= cl["palavras_max"]]
        checa("%s: de %d a %d palavras por bloco" % (tag, cl["palavras_min"], cl["palavras_max"]), not fora, "; ".join(fora[:3]))
        media = sum(len(b["texto"].split()) for b in blocos) / float(len(blocos))
        checa("%s: média de palavras por bloco perto de %d (%.2f, faixa 2,5 a 3,5)" % (tag, cl["palavras_alvo"], media), 2.5 <= media <= 3.5)
        longos = [b["texto"] for b in blocos if len(b["texto"]) > cl["caracteres_max_linha"]]
        checa("%s: até %d caracteres por linha" % (tag, cl["caracteres_max_linha"]), not longos, "; ".join(longos[:3]))
        minusc = [b["texto"] for b in blocos if b["texto"] != b["texto"].upper()]
        checa("%s: tudo em caixa alta" % tag, not minusc or not cl["caixa_alta"], "; ".join(minusc[:3]))
        pont = [b["texto"] for b in blocos if re.search(PONTUACAO_LEGENDA, b["texto"]) or re.search(r"(^|\s)[-–—]+(\s|$)", b["texto"])]
        checa("%s: sem pontuação além do '?'" % tag, not pont, "; ".join(pont[:3]))
        obtido = " ".join(b["texto"] for b in blocos).split()
        div = next((i for i, (x, y) in enumerate(zip(obtido, esperado)) if x != y), None)
        if div is None and len(obtido) != len(esperado):
            div = min(len(obtido), len(esperado))
        checa("%s: texto literal do script, na ordem" % tag, div is None,
              "diverge na palavra %s: '%s' no lugar de '%s'" % (div, " ".join(obtido[div:div + 3]) if div is not None else "",
                                                              " ".join(esperado[div:div + 3]) if div is not None else ""))
        if div is not None:
            continue

        # blocos por palavra do script
        idx, faixas = 0, []
        for b in blocos:
            n = len(b["texto"].split())
            faixas.append(list(range(idx, idx + n)))
            idx += n
        cruza = [b["texto"] for b, f in zip(blocos, faixas)
                 if len({pal_script[i]["frase"] for i in f}) > 1
                 and not any(sum(1 for p in pal_script if p["frase"] == pal_script[i]["frase"]) == 1 for i in f)]
        checa("%s: nenhum bloco atravessa o fim de uma frase" % tag, not cruza, "; ".join(cruza[:3]))

        # preposição ou artigo no fim do bloco, só quando havia divisão melhor
        expr = cl.get("expressoes_inseparaveis", [])
        por_frase = {}
        for p in pal_script:
            por_frase.setdefault(p["frase"], []).append(p)
        travados = []
        for b, f in zip(blocos, faixas):
            ultima = pal_script[f[-1]]
            if ultima["i"] == len(pal_script) - 1 or pal_script[ultima["i"] + 1]["frase"] != ultima["frase"]:
                continue
            if norm(ultima["w"]) in TRAVA_FIM:
                uni = por_frase[ultima["frase"]]
                if divisao_possivel(uni, cl, set()):
                    travados.append(b["texto"])
        checa("%s: artigo, preposição e pronome presos à palavra seguinte" % tag, not travados, "; ".join(travados[:3]))
        partidos = []
        for e in expr:
            alvo_e = [norm(w) for w in e.split() if norm(w)]
            for s in range(len(pal_script) - len(alvo_e) + 1):
                if len(alvo_e) > 1 and [norm(p["w"]) for p in pal_script[s:s + len(alvo_e)]] == alvo_e:
                    blocos_da_exp = {k for k, f in enumerate(faixas) for i in range(s, s + len(alvo_e)) if i in f}
                    if len(blocos_da_exp) > 1:
                        partidos.append(e)
        checa("%s: expressões inseparáveis inteiras" % tag, not partidos, "; ".join(partidos[:3]))

        # sincronia com a fala medida no editado
        tol = cl["tolerancia_sincronia_s"]
        desvio, sai_cedo, fica_demais, sobrepoe, vao = [], [], [], [], []
        for k, (b, f) in enumerate(zip(blocos, faixas)):
            t0, t1 = tempos[f[0]], tempos[f[-1]]
            if not t0 or not t1:
                continue
            if abs(b["ini"] - t0[0]) > tol:
                desvio.append("%s (%.2f s)" % (b["texto"], b["ini"] - t0[0]))
            if b["fim"] < t1[1] - tol:
                sai_cedo.append(b["texto"])
            prox = blocos[k + 1] if k + 1 < len(blocos) else None
            if prox:
                if b["fim"] > prox["ini"] + 0.001:
                    sobrepoe.append(b["texto"])
                p0 = tempos[faixas[k + 1][0]]
                continua = p0 and p0[0] - t1[1] < cl["vao_continuo_s"]
                if continua and prox["ini"] - b["fim"] > 0.001:
                    vao.append(b["texto"])
                if not continua and b["fim"] > t1[1] + tol:
                    fica_demais.append(b["texto"])
            elif b["fim"] > t1[1] + tol:
                fica_demais.append(b["texto"])
        checa("%s: início de cada bloco a até %.2f s do ataque da primeira palavra" % (tag, tol), not desvio, "; ".join(desvio[:4]))
        checa("%s: legenda não some antes do fim da fala" % tag, not sai_cedo, "; ".join(sai_cedo[:3]))
        checa("%s: legenda não fica depois da fala num silêncio real" % tag, not fica_demais, "; ".join(fica_demais[:3]))
        checa("%s: blocos sem sobreposição" % tag, not sobrepoe, "; ".join(sobrepoe[:3]))
        checa("%s: sem vão visual em fala contínua" % tag, not vao, "; ".join(vao[:3]))
        ordem = all(x["ini"] <= y["ini"] for x, y in zip(blocos, blocos[1:]))
        checa("%s: blocos em ordem de tempo" % tag, ordem)

        if arq.endswith(".ass"):
            t = open(arq, encoding="utf-8").read()
            campos = valores = None
            sec = ""
            for ln in t.splitlines():
                if ln.startswith("["):
                    sec = ln
                elif sec == "[V4+ Styles]" and ln.startswith("Format:"):
                    campos = [x.strip() for x in ln[7:].split(",")]
                elif sec == "[V4+ Styles]" and ln.startswith("Style: Legenda,"):
                    valores = [x.strip() for x in ln[6:].split(",")]
            st = dict(zip(campos or [], valores or []))
            esperado_st = {"Fontname": cl["fonte"], "Fontsize": str(cl["tamanho_px"]), "Bold": "-1", "BorderStyle": "3",
                           "Shadow": str(cl["sombra"]), "Alignment": "2", "MarginV": str(abs(int(cl["pos_y"]))),
                           "Spacing": str(cl["espacamento_letras"]), "Outline": str(cl["fundo_margem"]),
                           "OutlineColour": "&H%02X000000" % int(round(255 * (1 - cl["fundo_opacidade"]))),
                           "PrimaryColour": "&H00FFFFFF"}
            difere = [k for k, v in esperado_st.items() if st.get(k) != v]
            checa("%s: estilo igual ao padrão (fonte, tamanho, negrito, caixa de fundo, sombra, posição)" % tag, not difere,
                  ", ".join("%s=%s" % (k, st.get(k)) for k in difere))
            anim = re.findall(r"\\(fad|move|t\(|k|fscx|fscy|c&)", t)
            checa("%s: sem animação, fade, movimento ou troca de cor" % tag, not anim)

    # ------------------------------------------------ texto do editado
    faltam = [pal_script[i]["w"] for i, t in enumerate(tempos) if not t]
    checa("editado: todas as palavras do script presentes", not faltam, " ".join(faltam[:8]))
    inicios = [t[0] for t in tempos if t]
    checa("editado: frases na sequência do script", all(x <= y for x, y in zip(inicios, inicios[1:])))
    aceitos = {norm(d["w"]) for d in (plano or {}).get("desvios_mantidos", [])}
    nao_aceitos = [e["w"] for e in extras if norm(e["w"]) not in aceitos]
    checa("editado: nenhum conteúdo além do script (fora os desvios registrados no plano)", not nao_aceitos, " ".join(nao_aceitos[:8]))
    ft = tokens_falados(pal_ed)
    ns = [t["n"] for t in ft]
    sanc = [norm(p["w"]) for p in pal_script]
    reps = []
    for j in range(len(ns) - 2):
        for k in range(j + 3, len(ns) - 2):
            if ft[k]["ini"] - ft[j]["ini"] > 8.0:
                break
            tri = ns[j:j + 3]
            if ns[k:k + 3] == tri:
                pos = [i for i in range(len(sanc) - 2) if sanc[i:i + 3] == tri]
                if len(pos) < 2:
                    reps.append(" ".join(tri))
    checa("editado: nenhuma sequência de 3 palavras repetida em 8 s (tomada sobrando)", not reps, "; ".join(reps[:3]))
    falas = [p for p in pal_ed if not p["w"].startswith("[")]
    gaps = [(round(y["ini"] - x["fim"], 3), x["w"]) for x, y in zip(falas, falas[1:])]
    grandes = [g for g in gaps if g[0] > cc["intervalo_max_s"] + 1e-6]
    checa("editado: intervalo entre falas até %.2f s" % cc["intervalo_max_s"], not grandes,
          "; ".join("%.2f s depois de '%s'" % g for g in grandes[:3]))
    dur = float(editado.get("duracao_s") or 0)
    if falas and dur:
        checa("editado: sem silêncio antes da primeira fala e depois da última",
              falas[0]["ini"] <= cc["intervalo_max_s"] and dur - falas[-1]["fim"] <= cc["intervalo_max_s"],
              "começo %.2f s, fim %.2f s" % (falas[0]["ini"], dur - falas[-1]["fim"]))

    # ------------------------------------------------ plano de cortes
    if plano:
        tr = plano["trechos"]
        checa("plano: trechos em ordem e sem sobreposição", all(a[1] <= b[0] for a, b in zip(tr, tr[1:])) and all(a[0] < a[1] for a in tr))
        fps = float(plano.get("fps", cfg["saida"]["fps"]))
        fora_grade = [x for a in tr for x in a if abs(x * fps - round(x * fps)) > 0.02]
        checa("plano: cortes no grid de quadros", len(fora_grade) <= len(plano.get("avisos", [])), "%d cortes fora" % len(fora_grade))
        checa("plano: todas as frases do script têm tomada", not plano.get("frases_ausentes") and len(plano["frases"]) == len(frases))
        checa("plano: maior intervalo editado até %.2f s" % cc["intervalo_max_s"], plano.get("maior_intervalo_editado_s", 0) <= cc["intervalo_max_s"])

    # ------------------------------------------------ cenas de apoio
    cp = os.path.join(pasta, "cenas_aprovadas.json")
    if os.path.exists(cp):
        cenas = ler_json(cp)
        lista = cenas["cenas"]
        ccen = cfg["cenas"]
        durt = cenas.get("duracao_editado_s") or dur
        curtas = [c["arquivo"] for c in lista if c["duracao_s"] < ccen["duracao_min_s"]]
        checa("cenas: duração mínima de %.1f s" % ccen["duracao_min_s"], not curtas, "; ".join(curtas))
        longas = [c["arquivo"] for c in lista if c["duracao_s"] > ccen["duracao_max_s"] and not c.get("trecho_longo_com_arquivo_suficiente")]
        checa("cenas: duração máxima de %.1f s ou arquivo suficiente" % ccen["duracao_max_s"], not longas, "; ".join(longas))
        ret = [c["arquivo"] for i, c in enumerate(lista) if c["ini"] - (lista[i - 1]["fim"] if i else 0.0) < ccen["retorno_min_s"] - 1e-6]
        checa("cenas: volta ao apresentador por pelo menos %.1f s" % ccen["retorno_min_s"], not ret, "; ".join(ret))
        checa("cenas: nenhuma cena repetida", len({c["arquivo"] for c in lista}) == len(lista))
        checa("cenas: o vídeo termina com o apresentador", not lista or lista[-1]["fim"] <= durt - ccen["retorno_min_s"] + 1e-6)
        frac = sum(c["duracao_s"] for c in lista) / float(durt or 1)
        checa("cenas: no máximo metade do vídeo (%.0f%%)" % (100 * frac), frac <= ccen["fracao_max_video"] + 1e-6)
        wh = [c["arquivo"] for c in lista if abs(c["efeito_ini"] - max(0.0, c["ini"] - cenas["pico_efeito_s"])) > 0.002]
        checa("cenas: pico do efeito sonoro no corte de entrada", not wh, "; ".join(wh))
        dentro = []
        for c in lista:
            ws = [norm(w) for w in c["trecho"].split() if norm(w)]
            idx = [i for i in range(len(pal_script) - len(ws) + 1) if [norm(p["w"]) for p in pal_script[i:i + len(ws)]] == ws]
            if not idx or len({p["frase"] for p in pal_script[idx[0]:idx[0] + len(ws)]}) > 1:
                dentro.append(c["arquivo"])
            elif tempos[idx[0]] and abs(c["ini"] - tempos[idx[0]][0]) > 0.002:
                dentro.append(c["arquivo"])
        checa("cenas: começam no início do trecho e ficam dentro de uma frase", not dentro, "; ".join(dentro))

    sys.exit(0 if all(RES) else 1)


if __name__ == "__main__":
    main()
