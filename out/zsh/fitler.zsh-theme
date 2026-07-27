# Fitler prompt — generated from palette.json; do not edit
# ZSH_THEME="fitler" in ~/.zshrc, with this file at
# ~/.oh-my-zsh/custom/themes/fitler.zsh-theme

# ponytail: truecolor SGR inline. Works in ghostty; falls back to nothing weird
# elsewhere. Switch to %F{n} 256-color codes if you ever use a dumb terminal.
_f() { print -n "%{\e[38;2;$1;$2;$3m%}"; }
_b() { print -n "%{\e[48;2;$1;$2;$3m%}"; }
_r="%{\e[0m%}"

_fit_dir="%{\e[38;2;102;141;177m%}"
_fit_git="%{\e[38;2;158;122;171m%}"
_fit_ok="%{\e[38;2;141;162;97m%}"
_fit_err="%{\e[38;2;201;98;86m%}"
_fit_dim="%{\e[38;2;97;94;88m%}"
_fit_acc="%{\e[38;2;211;165;76m%}"
_fit_rst="%{\e[0m%}"

ZSH_THEME_GIT_PROMPT_PREFIX="${_fit_git}"
ZSH_THEME_GIT_PROMPT_SUFFIX="${_fit_rst}"
ZSH_THEME_GIT_PROMPT_DIRTY="${_fit_acc}*${_fit_rst}"
ZSH_THEME_GIT_PROMPT_CLEAN=""

PROMPT='${_fit_dir}%~${_fit_rst} $(git_prompt_info)
%(?.${_fit_ok}.${_fit_err})❯${_fit_rst} '
RPROMPT='${_fit_dim}%*${_fit_rst}'
