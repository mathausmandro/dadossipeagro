#!/bin/zsh
# Baixa o CSV do SIPEAGRO pelo navegador padrão (o servidor do MAPA recusa download por curl) e regenera o app.
BASE="${0:A:h:h}"
URL="https://dados.agricultura.gov.br/dataset/52a01565-72d6-410e-b21b-64035831a7be/resource/e0bbc9d5-f161-448b-a6d4-c7beb312ec33/download/sipeagrofertilizante.csv"
MARK=$(mktemp); sleep 1
open "$URL"
for i in {1..60}; do
  F=$(find ~/Downloads -maxdepth 1 -name 'sipeagrofertilizante*.csv' -newer "$MARK" 2>/dev/null | head -1)
  [[ -n "$F" && ! -e "$F.crdownload" && ! -e "$F.download" ]] && break; F=""; sleep 2
done
rm -f "$MARK"
[[ -z "$F" ]] && { echo "ERRO: download não chegou em ~/Downloads"; exit 1; }
sleep 2; mv "$F" "$BASE/dados/sipeagrofertilizante.csv"
python3 -I "$BASE/tools/build.py" "$BASE"

# Publica no GitHub Pages se houver mudança
cp "$BASE/sipeagro-fertilizantes.html" "$BASE/index.html"
cd "$BASE"
git add -A
if ! git diff --cached --quiet; then
  git commit -q -m "Atualiza base SIPEAGRO $(date +%d/%m/%Y)" && git push -q origin main && echo "Publicado no GitHub Pages"
else
  echo "Sem mudanças para publicar"
fi
