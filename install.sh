#!/bin/sh
# Symlink out/ into place. Rebuilds are live — no reinstall needed.
set -e

SRC="$(cd "$(dirname "$0")" && pwd)/out"
SLUG=fitler

link() {
  mkdir -p "$(dirname "$2")"
  ln -sfn "$1" "$2"
  echo "  $2"
}

python3 "$(dirname "$0")/build.py" >/dev/null
echo "linking:"

link "$SRC/ghostty/$SLUG"                        "$HOME/.config/ghostty/themes/$SLUG"
link "$SRC/nvim/colors/$SLUG.lua"                "$HOME/.config/nvim/colors/$SLUG.lua"
link "$SRC/nvim/lua/lualine/themes/$SLUG.lua"    "$HOME/.config/nvim/lua/lualine/themes/$SLUG.lua"
link "$SRC/tmux/$SLUG.conf"                      "$HOME/.config/tmux/$SLUG.conf"
link "$SRC/vscode"                               "$HOME/.vscode/extensions/$SLUG-theme"
link "$SRC/zsh/$SLUG.zsh-theme"                  "$HOME/.oh-my-zsh/custom/themes/$SLUG.zsh-theme"

cat <<EOF

then, once:
  ghostty   ~/.config/ghostty/config    theme = $SLUG
  nvim      colorscheme $SLUG           (lualine theme = "$SLUG")
  tmux      ~/.tmux.conf                source-file ~/.config/tmux/$SLUG.conf
  vscode    cmd+shift+p > Color Theme > Fitler   (restart first)
  zsh       ~/.zshrc                    ZSH_THEME="$SLUG"
  herdr     ~/.config/herdr/config.toml merge in $SRC/herdr/$SLUG.toml (see README)
  windows terminal   settings.json      merge in $SRC/windows-terminal/$SLUG.json (see README)
EOF
