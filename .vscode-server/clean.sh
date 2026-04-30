#!/bin/bash
rm -rf ~/.cache 2> /dev/null

if [ ! -d ~/.vscode-server ]; then
  echo "\"~/.vscode-server\" does not exist."
  exit 0
fi

pkill -u "$USER" -f '\.vscode-server'

shopt -s extglob

rm -rf ~/.vscode-server/data/CachedExtensionVSIXs
rm -f ~/.vscode-server/.cli.*.log

if [[ ! -f "~/.vscode-server/cli/servers/lru.json" ]]; then
  SERVER_VERSION=$(grep -oE '[0-9a-f]{40}' ~/.vscode-server/cli/servers/lru.json | head -n1)
  echo "[\"Stable-$SERVER_VERSION\"]" > ~/.vscode-server/cli/servers/lru.json
  rm -rf ~/.vscode-server/cli/servers/Stable-!($SERVER_VERSION)
  rm -f ~/.vscode-server/code-!($SERVER_VERSION)
else
  rm -rf ~/.vscode-server/cli
  rm -f ~/.vscode-server/code-*
fi

rm -rf ~/.vscode-server/extensions/*.vsctmp

declare -A exts
for lsout in $(cd ~/.vscode-server/extensions && ls -rvd */); do
  ext_fullname=${lsout::-1}
  ext_version=$(grep -oP '\-\d+\.\d+\.\d+' <<< "$ext_fullname")
  ext_name=${ext_fullname/$ext_version}
  ext_version=${ext_version:1}
  if [[ -n "${exts[$ext_name]+isset}" ]]; then
    rm -rf ~/.vscode-server/extensions/$lsout
  else
    exts[$ext_name]=$ext_version
  fi
done

shopt -u extglob
