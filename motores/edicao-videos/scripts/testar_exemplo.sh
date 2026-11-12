#!/usr/bin/env bash
# Roda a partir da pasta do motor: bash scripts/testar_exemplo.sh
set -u
cd "$(dirname "$0")/.."
LING=../../_nucleo/scripts/checar_linguagem.py
ENTREGA=exemplo/cliente/entregas/edicao-videos/video-01
falhou=0

echo "== validar.py na entrega de exemplo (pasta, e legenda sozinha)"
python3 scripts/validar.py "$ENTREGA" || falhou=1
python3 scripts/validar.py "$ENTREGA/legendas.srt" --script "$ENTREGA/script.txt" --palavras "$ENTREGA/palavras_editado.json" > /dev/null \
  || { echo "VOLTA validar.py com legendas.srt"; falhou=1; }

echo "== a cadeia de scripts reproduz o exemplo"
TMP=$(mktemp -d)
mkdir -p "$TMP/cliente/entregas/edicao-videos/video-01"
cp -R exemplo/cliente/edicao-videos "$TMP/cliente/"
for f in script.txt config_video.json transcricao_bruta.json cenas_escolhidas.json; do cp "$ENTREGA/$f" "$TMP/cliente/entregas/edicao-videos/video-01/"; done
V="$TMP/cliente/entregas/edicao-videos/video-01"
python3 scripts/alinhar.py "$V" > /dev/null && python3 scripts/transcrever.py --simular-editado "$V" > /dev/null \
  && python3 scripts/legendas.py "$V" > /dev/null && python3 scripts/cenas.py "$V" > /dev/null || { echo "VOLTA cadeia de scripts"; falhou=1; }
for f in plano_cortes.json palavras_editado.json blocos.json legendas.srt legendas.ass cenas_aprovadas.json; do
  cmp -s "$V/$f" "$ENTREGA/$f" || { echo "VOLTA $f diferente do reproduzido"; falhou=1; }
done
python3 scripts/render.py base "$V" --bruto bruto.mp4 --simular > /dev/null && python3 scripts/render.py final "$V" --simular > /dev/null \
  || { echo "VOLTA render --simular"; falhou=1; }
rm -rf "$TMP"

echo "== linguagem nos textos do exemplo e do motor"
if [ -f "$LING" ]; then
  for f in "$ENTREGA"/*.md "$ENTREGA"/cenas_escolhidas.json README.md AGENTE.md SPEC.md; do
    [ -f "$f" ] || continue
    python3 "$LING" "$f" > /dev/null || { echo "VOLTA linguagem: $f"; python3 "$LING" "$f" | grep VOLTA; falhou=1; }
  done
else
  echo "PULA linguagem: checar_linguagem.py não está neste repositório"
fi

if [ "$falhou" -eq 0 ]; then echo "PASSA exemplo do motor edicao-videos"; else echo "VOLTA exemplo do motor edicao-videos"; fi
exit "$falhou"
