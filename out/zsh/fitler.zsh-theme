# Fitler prompt — generated from palette.json; do not edit
# ZSH_THEME="fitler" in ~/.zshrc, with this file at
# ~/.oh-my-zsh/custom/themes/fitler.zsh-theme

# ponytail: native %F{#hex} truecolor (zsh >= 5.7). zsh emits the SGR and does
# the zero-width accounting itself, so no raw \e or %{..%} wrapping.
_fit_dir="%F{#668db1}"
_fit_git="%F{#9e7aab}"
_fit_ok="%F{#8da261}"
_fit_err="%F{#c96256}"
_fit_dim="%F{#615e58}"
_fit_acc="%F{#d3a54c}"
_fit_rst="%f"

ZSH_THEME_GIT_PROMPT_PREFIX="${_fit_git}"
ZSH_THEME_GIT_PROMPT_SUFFIX="${_fit_rst}"
ZSH_THEME_GIT_PROMPT_DIRTY="${_fit_acc}*${_fit_rst}"
ZSH_THEME_GIT_PROMPT_CLEAN=""

PROMPT='${_fit_dir}%~${_fit_rst} $(git_prompt_info)
%(?.${_fit_ok}.${_fit_err})❯${_fit_rst} '
RPROMPT='${_fit_dim}%*${_fit_rst}'
