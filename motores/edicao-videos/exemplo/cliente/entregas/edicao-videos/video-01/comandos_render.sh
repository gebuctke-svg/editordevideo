#!/usr/bin/env bash
# Comandos gerados por render.py --simular. Caminhos relativos à pasta da entrega.
set -e

# etapa base
ffmpeg -y -v error -i bruto.mp4 -filter_complex '[0:v]select='"'"'gte(t,5.21666)*lt(t,8.05000)+gte(t,8.41666)*lt(t,10.08333)+gte(t,10.58333)*lt(t,15.01666)+gte(t,15.45000)*lt(t,15.95000)+gte(t,17.41666)*lt(t,19.38333)+gte(t,19.91666)*lt(t,22.28333)+gte(t,26.38333)*lt(t,28.38333)+gte(t,28.78333)*lt(t,32.18333)+gte(t,36.91666)*lt(t,40.95000)+gte(t,41.98333)*lt(t,45.05000)+gte(t,45.51666)*lt(t,49.51666)+gte(t,50.01666)*lt(t,54.28333)+gte(t,54.78333)*lt(t,60.58333)'"'"',setpts=N/30/TB,crop=1215:2160:1312:0,scale=1080:1920,setsar=1[vo];[0:a]asetnsamples=n=32,aselect='"'"'gte(t,5.23333)*lt(t,8.06667)+gte(t,8.43333)*lt(t,10.10000)+gte(t,10.60000)*lt(t,15.03333)+gte(t,15.46667)*lt(t,15.96667)+gte(t,17.43333)*lt(t,19.40000)+gte(t,19.93333)*lt(t,22.30000)+gte(t,26.40000)*lt(t,28.40000)+gte(t,28.80000)*lt(t,32.20000)+gte(t,36.93333)*lt(t,40.96667)+gte(t,42.00000)*lt(t,45.06667)+gte(t,45.53333)*lt(t,49.53333)+gte(t,50.03333)*lt(t,54.30000)+gte(t,54.80000)*lt(t,60.60000)'"'"',asetpts=N/SR/TB[ao]' -map '[vo]' -map '[ao]' -r 30 -c:v libx264 -b:v 8M -c:a pcm_s16le base.mov
ffmpeg -y -v error -i base.mov -vn -ac 1 -ar 16000 base.wav

# etapa final
ffmpeg -y -v error -i base.mov -an -i cliente/edicao-videos/cenas/mulher-prato-quase-vazio.mp4 -an -i cliente/edicao-videos/cenas/metabolismo-cofre-animacao.mp4 -an -i cliente/edicao-videos/cenas/clara-foto-antiga-gravidez.mp4 -an -i cliente/edicao-videos/cenas/prato-cheio-de-cima.mp4 -an -i cliente/edicao-videos/cenas/mulher-fecha-calca-sorrindo.mp4 -i cliente/edicao-videos/efeitos/whoosh.wav -filter_complex '[1:v]trim=duration=2.900,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,setpts=PTS-STARTPTS+4.555/TB[c0];
[0:v][c0]overlay=eof_action=pass:enable='"'"'between(t,4.555,7.455)'"'"'[v0];
[2:v]trim=duration=4.248,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,setpts=PTS-STARTPTS+9.472/TB[c1];
[v0][c1]overlay=eof_action=pass:enable='"'"'between(t,9.472,13.720)'"'"'[v1];
[3:v]trim=duration=3.264,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,setpts=PTS-STARTPTS+15.847/TB[c2];
[v1][c2]overlay=eof_action=pass:enable='"'"'between(t,15.847,19.111)'"'"'[v2];
[4:v]trim=duration=3.927,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,setpts=PTS-STARTPTS+26.289/TB[c3];
[v2][c3]overlay=eof_action=pass:enable='"'"'between(t,26.289,30.216)'"'"'[v3];
[5:v]trim=duration=3.765,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,setpts=PTS-STARTPTS+34.581/TB[c4];
[v3][c4]overlay=eof_action=pass:enable='"'"'between(t,34.581,38.345)'"'"'[v4];
[v4]subtitles='"'"'legendas.ass'"'"'[vo];
[6:a]volume=0dB,asplit=5[w0][w1][w2][w3][w4];
[w0]adelay=4205|4205[wd0];
[w1]adelay=9122|9122[wd1];
[w2]adelay=15497|15497[wd2];
[w3]adelay=25939|25939[wd3];
[w4]adelay=34231|34231[wd4];
[0:a][wd0][wd1][wd2][wd3][wd4]amix=inputs=6:normalize=0:duration=first[ao]' -map '[vo]' -map '[ao]' -c:v libx264 -b:v 8M -c:a aac -b:a 192k -movflags +faststart final.mp4
