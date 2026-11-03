#!/bin/zsh
# Baixa empresas (CSV) e produtos (painel Qlik) do MAPA num Chrome invisível, gera o app e publica no GitHub Pages.
BASE="${0:A:h:h}"
cd "$BASE" || exit 1
echo "=== $(date '+%d/%m/%Y %H:%M') ==="
python3 -I "$BASE/tools/baixar_qlik.py" "$BASE" || echo "AVISO: falha ao baixar do MAPA (usando a última versão)"
python3 -I "$BASE/tools/build.py" "$BASE" || exit 1
cp "$BASE/sipeagro-fertilizantes.html" "$BASE/index.html"
git add -A
if ! git diff --cached --quiet; then
  git commit -q -m "Atualiza base SIPEAGRO $(date +%d/%m/%Y)" && GIT_SSH_COMMAND="ssh -o BatchMode=yes" git push -q origin main && echo "Publicado no GitHub Pages"
else
  echo "Sem mudanças para publicar"
fi
