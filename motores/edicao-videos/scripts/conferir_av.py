#!/usr/bin/env python3
"""Validação audiovisual do vídeo pronto (precisa de ffmpeg e ffprobe).

Uso: python3 scripts/conferir_av.py <pasta-da-entrega> [--arquivo final.mp4]

Mede no arquivo:
- sincronia: durações de vídeo e áudio com diferença de até 0,04 s;
- pausas: silêncios internos acima do intervalo máximo mais 0,10 s de folga de medição;
- quadros congelados: trechos parados por mais de 0,5 s;
- saltos de volume: variação de mais de 12 dB entre janelas vizinhas de 0,4 s.
Grava conferencia_av.json. O que não dá para medir (boca parada, fonema cortado de ouvido)
fica na lista de conferência humana do relatório.
"""
import json
import os
import re
import subprocess
import sys

from comum import carregar_config, gravar_json


def ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats"] + args, capture_output=True, text=True).stderr


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    pasta = os.path.abspath(sys.argv[1])
    cfg = carregar_config(pasta)
    arq = os.path.join(pasta, sys.argv[sys.argv.index("--arquivo") + 1] if "--arquivo" in sys.argv else cfg["saida"]["arquivo"])
    if not os.path.exists(arq):
        raise SystemExit("Vídeo não encontrado: %s" % arq)
    res, ok = {}, True

    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "json", arq],
                         capture_output=True, text=True).stdout
    d = {s["codec_type"]: float(s.get("duration", 0)) for s in json.loads(out).get("streams", [])}
    delta = abs(d.get("video", 0) - d.get("audio", 0))
    res["sincronia_ms"] = round(delta * 1000)
    ok_sinc = delta <= cfg["cortes"]["sincronia_av_max_s"]

    lim = cfg["cortes"]["intervalo_max_s"] + 0.10
    txt = ff(["-i", arq, "-af", "silencedetect=noise=-30dB:d=%.2f" % lim, "-f", "null", "-"])
    pausas = [float(x) for x in re.findall(r"silence_duration: ([0-9.]+)", txt)]
    res["pausas_acima_do_limite"] = pausas
    txt = ff(["-i", arq, "-vf", "freezedetect=n=0.001:d=0.5", "-map", "0:v", "-f", "null", "-"])
    congelados = re.findall(r"freeze_start: ([0-9.]+)", txt)
    res["quadros_congelados_em_s"] = [float(x) for x in congelados]
    txt = ff(["-i", arq, "-af", "asetnsamples=n=19200,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
              "-f", "null", "-"])
    niveis = [float(x) for x in re.findall(r"RMS_level=(-?[0-9.]+)", txt)]
    saltos = [round(i * 0.4, 1) for i in range(1, len(niveis)) if abs(niveis[i] - niveis[i - 1]) > 12 and min(niveis[i], niveis[i - 1]) > -50]
    res["saltos_de_volume_em_s"] = saltos

    for nome, passou in (("sincronia de vídeo e áudio", ok_sinc), ("pausas internas", not pausas),
                         ("quadros congelados", not congelados), ("saltos de volume", not saltos)):
        print(("PASSA " if passou else "VOLTA ") + nome)
        ok = ok and passou
    res["conferencia_humana"] = ["boca parada com áudio seguindo", "fonema cortado ouvido no fone", "pigarro ou respiração que sobrou"]
    gravar_json(os.path.join(pasta, "conferencia_av.json"), res)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
