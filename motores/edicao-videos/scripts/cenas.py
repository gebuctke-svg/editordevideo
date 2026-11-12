#!/usr/bin/env python3
"""Confere e posiciona as cenas de apoio escolhidas pelo agente.

Uso: python3 scripts/cenas.py <pasta-da-entrega>

Lê cenas_escolhidas.json (o trecho literal do script e o arquivo do catálogo, escolhidos
pelo agente com o prompt prompts/etapa3_cenas.md), o catálogo do cliente e os tempos
medidos no editado. Aplica as regras de frequência e duração e grava cenas_aprovadas.json
com o tempo de cada cena, o início do efeito sonoro e as recusadas com motivo.

A escolha semântica é do agente. Este script só aprova o que cumpre as regras mecânicas:
unidade de sentido, duração, retorno ao apresentador, repetição, duplicado, orientação,
fim do vídeo no apresentador e no máximo metade do tempo em cenas.
"""
import array
import csv
import os
import re
import sys
import wave

from comum import (carregar_config, casar_script_com_fala, gravar_json, ler_json, ler_script, norm,
                   palavras_do_script, pasta_cliente_de)

CONJ = {"e", "mas", "porque", "quando", "que", "se", "com", "ou", "entao", "depois", "hoje", "so", "sempre"}


def ler_catalogo(caminho):
    if not os.path.exists(caminho):
        raise SystemExit("Catálogo de cenas não encontrado: %s" % caminho)
    linhas = list(csv.DictReader(open(caminho, encoding="utf-8")))
    obrig = {"arquivo", "classe", "descricao", "quando_usar", "duracao_s", "formato", "orientacao", "observacao"}
    faltam = obrig - set(linhas[0].keys() if linhas else [])
    if faltam:
        raise SystemExit("O catálogo precisa das colunas: %s" % ", ".join(sorted(faltam)))
    return {l["arquivo"]: l for l in linhas}


def pico_do_efeito(caminho, padrao):
    """Instante do pico do efeito sonoro, medido no wav. Sem arquivo, vale a configuração."""
    if not caminho or not os.path.exists(caminho) or not caminho.lower().endswith(".wav"):
        return float(padrao), "configuração"
    w = wave.open(caminho, "rb")
    if w.getsampwidth() != 2:
        return float(padrao), "configuração (wav não é 16 bits)"
    canais, sr = w.getnchannels(), w.getframerate()
    dados = array.array("h", w.readframes(w.getnframes()))
    maior, onde = 0, 0
    for i in range(0, len(dados), canais):
        v = abs(dados[i])
        if v > maior:
            maior, onde = v, i // canais
    return round(onde / float(sr), 3), "medido no arquivo"


def achar_trecho(pal_script, trecho):
    alvo = [norm(w) for w in trecho.split() if norm(w)]
    ns = [norm(p["w"]) for p in pal_script]
    for s in range(len(ns) - len(alvo) + 1):
        if ns[s:s + len(alvo)] == alvo:
            return s, s + len(alvo) - 1
    return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    pasta = os.path.abspath(sys.argv[1])
    cfg = carregar_config(pasta)
    cc = cfg["cenas"]
    modo = cc["modos"][cc["modo"]]
    cliente = pasta_cliente_de(pasta)
    catalogo = ler_catalogo(os.path.join(cliente, cc["catalogo"]))
    pal_script = palavras_do_script(ler_script(os.path.join(pasta, "script.txt")))
    editado = ler_json(os.path.join(pasta, "palavras_editado.json"))
    tempos, _ = casar_script_com_fala(pal_script, editado["palavras"])
    dur_total = float(editado.get("duracao_s") or max(t[1] for t in tempos if t))
    esc = ler_json(os.path.join(pasta, "cenas_escolhidas.json"))["escolhas"]
    pico, origem_pico = pico_do_efeito(os.path.join(cliente, cfg["efeito_sonoro"]["arquivo"]), cfg["efeito_sonoro"]["pico_s"])
    orient = cfg["saida"]["orientacao"]

    candidatas = []
    recusadas = []
    for e in esc:
        pos = achar_trecho(pal_script, e["trecho"])
        if not pos:
            recusadas.append(dict(e, motivo="o trecho não aparece literalmente no script"))
            continue
        candidatas.append((pos, e))
    candidatas.sort(key=lambda x: x[0][0])

    aprovadas, usados = [], set()
    for (a, b), e in candidatas:
        def recusa(motivo):
            recusadas.append(dict(e, motivo=motivo))

        pa, pb = pal_script[a], pal_script[b]
        inicio_ok = a == 0 or pal_script[a - 1]["frase"] != pa["frase"] or re.search(r"[,;:]$", pal_script[a - 1]["w"]) \
            or norm(pa["w"]) in CONJ
        fim_ok = b == len(pal_script) - 1 or pal_script[b + 1]["frase"] != pb["frase"] or re.search(r"[,;:.!?]$", pb["w"]) \
            or norm(pal_script[b + 1]["w"]) in CONJ
        if not (inicio_ok and fim_ok):
            recusa("o trecho não é uma oração ou trecho de sentido completo")
            continue
        if pa["frase"] != pb["frase"]:
            recusa("uma cena não pode cobrir duas frases")
            continue
        cat = catalogo.get(e["arquivo"])
        if not cat:
            recusa("arquivo fora do catálogo")
            continue
        if cat["classe"] == cc["classe_apresentador"]:
            recusa("a gravação do apresentador é a base, nunca cena de apoio")
            continue
        if cat["orientacao"].strip().lower() != orient:
            recusa("orientação %s diferente da saída %s" % (cat["orientacao"], orient))
            continue
        m = re.search(r"duplicado de\s+(\S+)", cat.get("observacao") or "")
        if m and m.group(1) in catalogo:
            recusa("arquivo duplicado; o original %s está disponível" % m.group(1))
            continue
        if e["arquivo"] in usados:
            recusa("cena repetida no mesmo vídeo")
            continue
        ta, tb = tempos[a], tempos[b]
        if not ta or not tb:
            recusa("o trecho não tem tempo medido no editado")
            continue
        ini, fim = round(ta[0], 3), round(tb[1], 3)
        dur = fim - ini
        if fim > dur_total - cc["retorno_min_s"]:
            recusa("o vídeo termina com o apresentador falando")
            continue
        if dur < cc["duracao_min_s"]:
            recusa("trecho de %.2f s, abaixo do mínimo de %.1f s" % (dur, cc["duracao_min_s"]))
            continue
        dur_arquivo = float(cat["duracao_s"] or 0)
        if dur_arquivo < dur:
            recusa("arquivo de %.1f s é mais curto que o trecho de %.2f s (não se acelera, congela nem repete)" % (dur_arquivo, dur))
            continue
        longo = dur > cc["duracao_max_s"]
        anterior = aprovadas[-1]["fim"] if aprovadas else 0.0
        if ini - anterior < cc["retorno_min_s"]:
            recusa("retorno ao apresentador de %.2f s, abaixo do mínimo de %.1f s" % (ini - anterior, cc["retorno_min_s"]))
            continue
        usados.add(e["arquivo"])
        aprovadas.append({
            "n": len(aprovadas) + 1, "trecho": e["trecho"], "arquivo": e["arquivo"], "classe": cat["classe"],
            "funcao": e.get("funcao", ""), "motivo": e.get("motivo", ""),
            "ini": ini, "fim": fim, "duracao_s": round(dur, 3),
            "apresentador_antes_s": round(ini - anterior, 3),
            "trecho_longo_com_arquivo_suficiente": longo,
            "efeito_ini": round(max(0.0, ini - pico), 3),
        })

    total = sum(c["duracao_s"] for c in aprovadas)
    while aprovadas and total > cc["fracao_max_video"] * dur_total:
        c = aprovadas.pop()
        total -= c["duracao_s"]
        recusadas.append({"trecho": c["trecho"], "arquivo": c["arquivo"], "motivo": "cenas passariam de metade do vídeo"})

    retornos = [c["apresentador_antes_s"] for c in aprovadas]
    if aprovadas:
        retornos.append(round(dur_total - aprovadas[-1]["fim"], 3))
    no_alvo = sum(1 for r in retornos if modo["apresentador_min_s"] <= r <= modo["apresentador_max_s"])
    saida = {
        "modo": cc["modo"],
        "duracao_editado_s": round(dur_total, 3),
        "pico_efeito_s": pico, "pico_origem": origem_pico,
        "arquivo_efeito": cfg["efeito_sonoro"]["arquivo"],
        "cenas": aprovadas,
        "recusadas": recusadas,
        "estatisticas": {
            "cenas": len(aprovadas),
            "tempo_em_cenas_s": round(total, 3),
            "fracao_do_video": round(total / dur_total, 3) if dur_total else 0,
            "trechos_do_apresentador_s": retornos,
            "trechos_no_alvo": "%d de %d entre %.1f e %.1f s" % (no_alvo, len(retornos), modo["apresentador_min_s"], modo["apresentador_max_s"]),
        },
    }
    gravar_json(os.path.join(pasta, "cenas_aprovadas.json"), saida)
    print("aprovadas: %d | recusadas: %d | %.1f%% do vídeo em cenas | pico do efeito %.3f s (%s)"
          % (len(aprovadas), len(recusadas), 100 * saida["estatisticas"]["fracao_do_video"], pico, origem_pico))
    for c in aprovadas:
        print("  [%6.2f %6.2f] %-32s %s" % (c["ini"], c["fim"], c["arquivo"], c["trecho"][:50]))
    for r in recusadas:
        print("  recusada: %s | %s" % (r.get("trecho", "")[:40], r["motivo"]))


if __name__ == "__main__":
    main()
