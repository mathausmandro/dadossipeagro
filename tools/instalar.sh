#!/bin/zsh
# Configuração única: chave de acesso ao repositório + agendamento diário no Mac.
BASE="${0:A:h:h}"
K=~/.ssh/sipeagro_deploy
mkdir -p ~/.ssh && chmod 700 ~/.ssh
[ -f $K ] || ssh-keygen -t ed25519 -N "" -C "sipeagro-mac" -f $K -q
grep -q "Host github-sipeagro" ~/.ssh/config 2>/dev/null || printf "\nHost github-sipeagro\n  HostName github.com\n  User git\n  IdentityFile ~/.ssh/sipeagro_deploy\n  IdentitiesOnly yes\n" >> ~/.ssh/config
chmod 600 ~/.ssh/config
cp "$BASE/tools/com.sipeagro.atualizar.plist" ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.sipeagro.atualizar.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.sipeagro.atualizar.plist
echo "\nAgendamento instalado (todo dia às 7h)."
echo "\nCole esta chave em https://github.com/mathausmandro/dadossipeagro/settings/keys/new"
echo "(marque 'Allow write access'):\n"
cat $K.pub
