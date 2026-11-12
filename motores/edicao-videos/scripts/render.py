#!/usr/bin/env python3
"""Monta e roda os comandos do ffmpeg: base com cortes secos e, depois, o vídeo final.

Uso:
  python3 scripts/render.py base  <pasta-da-entrega> --bruto <video> [--simular]
  python3 scripts/render.py final <pasta-da-entrega> [--legendas ass|png] [--simular]

base:  corta o bruto em passada única, com janelas meio abertas [ini, fim), aplica o
       enquadramento do projeto e grava base.mov e base.wav (para a retranscrição).
       Portão: vídeo e áudio com durações que não divergem mais de 0,04 s.
final: sobre base.mov, coloca as cenas de apoio em corte seco, as legendas e o efeito
       sonoro com o pico no corte de entrada de cada cena. O áudio das cenas fica mudo.
       Portão: o mesmo de sincronia, no arquivo final.
--simular: não roda nada. Grava os comandos em comandos_render.sh para conferência.
"""
import argparse
import os
import shlex
import subprocess
import sys

from comum import carregar_config, ler_json, pasta_cliente_de


def duracoes(arq):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", arq],
                         capture_output=True, text=True).stdout
    d = {}
    for ln in out.strip().splitlines():
        p = ln.split(",")
        if len(p) >= 2 and p[1] not in ("", "N/A"):
            d[p[0]] = float(p[1])
    return d


def portao(arq, limite):
    d = duracoes(arq)
    delta = abs(d.get("video", 0) - d.get("audio", 0))
    print("sincronia %s: vídeo %.3f s, áudio %.3f s, diferença %.0f ms (máximo %.0f ms)"
          % (os.path.basename(arq), d.get("video", 0), d.get("audio", 0), delta * 1000, limite * 1000))
    return delta <= limite


def cmd_base(pasta, bruto, cfg):
    plano = ler_json(os.path.join(pasta, "plano_cortes.json"))
    s, crop = cfg["saida"], (cfg["enquadramento"].get("crop") or "").strip()
    fps = s["fps"]
    meio = 0.5 / float(fps)
    # vídeo: limites deslocados meio quadro, para cada quadro cair de um lado só da janela [ini, fim)
    vsel = "+".join("gte(t,%.5f)*lt(t,%.5f)" % (a - meio, b - meio) for a, b in plano["trechos"])
    # áudio: blocos de 32 amostras, para a janela não arredondar para blocos de 1.024
    sel = "+".join("gte(t,%.5f)*lt(t,%.5f)" % (a, b) for a, b in plano["trechos"])
    vf = "select='%s',setpts=N/%s/TB" % (vsel, fps)
    if crop:
        vf += ",crop=%s" % crop
    vf += ",scale=%d:%d,setsar=1" % (s["largura"], s["altura"])
    af = "asetnsamples=n=32,aselect='%s',asetpts=N/SR/TB" % sel
    fc = "[0:v]%s[vo];[0:a]%s[ao]" % (vf, af)
    base_mov = os.path.join(pasta, "base.mov")
    return [
        ["ffmpeg", "-y", "-v", "error", "-i", bruto, "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
         "-r", str(fps), "-c:v", s["codec_video"], "-b:v", s["bitrate_video"], "-c:a", "pcm_s16le", base_mov],
        ["ffmpeg", "-y", "-v", "error", "-i", base_mov, "-vn", "-ac", "1", "-ar", "16000", os.path.join(pasta, "base.wav")],
    ], base_mov


def cmd_final(pasta, cfg, modo_legenda):
    s = cfg["saida"]
    cliente = pasta_cliente_de(pasta)
    cenas = ler_json(os.path.join(pasta, "cenas_aprovadas.json"))
    pasta_cenas = os.path.join(cliente, cfg["cenas"]["pasta_arquivos"])
    arq_efeito = (cfg.get("efeito_sonoro") or {}).get("arquivo") or ""
    efeito = os.path.join(cliente, arq_efeito) if arq_efeito else ""
    com_efeito = bool(cenas.get("cenas")) and bool(efeito) and os.path.isfile(efeito)
    if cenas.get("cenas") and not com_efeito:
        print("AVISO efeito sonoro não encontrado (%s): o vídeo sai sem o som de transição."
              % (arq_efeito or "nenhum arquivo em efeito_sonoro.arquivo"))
    base_mov = os.path.join(pasta, "base.mov")
    entradas = ["-i", base_mov]
    fc, ov = [], "[0:v]"
    lista = cenas["cenas"]
    for i, c in enumerate(lista):
        entradas += ["-an", "-i", os.path.join(pasta_cenas, c["arquivo"])]
        d = c["fim"] - c["ini"]
        fc.append("[%d:v]trim=duration=%.3f,scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%s,setsar=1,"
                  "setpts=PTS-STARTPTS+%.3f/TB[c%d]" % (i + 1, d, s["largura"], s["altura"], s["largura"], s["altura"], s["fps"], c["ini"], i))
        fc.append("%s[c%d]overlay=eof_action=pass:enable='between(t,%.3f,%.3f)'[v%d]" % (ov, i, c["ini"], c["fim"] - 0.0005, i))
        ov = "[v%d]" % i
    n = len(lista) + 1
    if modo_legenda == "png":
        entradas += ["-f", "concat", "-safe", "0", "-i", os.path.join(pasta, "legendas_png", "concat.txt")]
        fc.append("%s[%d:v]overlay=eof_action=pass[vo]" % (ov, n))
        n += 1
    else:
        ass = os.path.join(pasta, "legendas.ass").replace("\\", "/").replace(":", "\\:")
        fc.append("%ssubtitles='%s'[vo]" % (ov, ass))
    mix = "[0:a]"
    if lista and com_efeito:
        entradas += ["-i", efeito]
        fc.append("[%d:a]volume=%sdB,asplit=%d%s" % (n, cfg["efeito_sonoro"].get("volume_db", 0), len(lista),
                                                    "".join("[w%d]" % i for i in range(len(lista)))))
        for i, c in enumerate(lista):
            ms = int(round(c["efeito_ini"] * 1000))
            fc.append("[w%d]adelay=%d|%d[wd%d]" % (i, ms, ms, i))
            mix += "[wd%d]" % i
    n_efeitos = len(lista) if com_efeito else 0
    if n_efeitos:
        fc.append("%samix=inputs=%d:normalize=0:duration=first[ao]" % (mix, n_efeitos + 1))
    else:
        fc.append("[0:a]anull[ao]")
    final = os.path.join(pasta, s["arquivo"])
    return [["ffmpeg", "-y", "-v", "error"] + entradas + ["-filter_complex", ";\n".join(fc), "-map", "[vo]", "-map", "[ao]",
             "-c:v", s["codec_video"], "-b:v", s["bitrate_video"], "-c:a", s["codec_audio"], "-b:a", s["bitrate_audio"],
             "-movflags", "+faststart", final]], final


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("etapa", choices=["base", "final"])
    ap.add_argument("entrega")
    ap.add_argument("--bruto")
    ap.add_argument("--legendas", choices=["ass", "png"], default="ass")
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()
    pasta = os.path.abspath(a.entrega)
    cfg = carregar_config(pasta)
    if a.etapa == "base":
        if not a.bruto:
            raise SystemExit("Informe o vídeo bruto com --bruto.")
        cmds, alvo = cmd_base(pasta, a.bruto, cfg)
    else:
        cmds, alvo = cmd_final(pasta, cfg, a.legendas)

    if a.simular:
        caminho = os.path.join(pasta, "comandos_render.sh")
        modo = "a" if a.etapa == "final" and os.path.exists(caminho) else "w"
        rel = lambda x: x.replace(pasta + os.sep, "").replace(pasta_cliente_de(pasta) + os.sep, "cliente/")
        with open(caminho, modo, encoding="utf-8") as f:
            if modo == "w":
                f.write("#!/usr/bin/env bash\n# Comandos gerados por render.py --simular. Caminhos relativos à pasta da entrega.\nset -e\n")
            f.write("\n# etapa %s\n" % a.etapa)
            for c in cmds:
                f.write(" ".join(shlex.quote(rel(x)) for x in c) + "\n")
        print("comandos da etapa %s gravados em comandos_render.sh (nada foi rodado)" % a.etapa)
        return
    for c in cmds:
        subprocess.run(c, check=True)
    if not portao(alvo, cfg["cortes"]["sincronia_av_max_s"]):
        print("PORTÃO DE SINCRONIA REPROVADO: não exporte este arquivo.")
        sys.exit(1)
    print("pronto: %s" % alvo)


if __name__ == "__main__":
    main()
