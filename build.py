#!/usr/bin/env python3
"""Generate every theme config from palette.json.

    python3 build.py          # write out/
    ./install.sh              # symlink out/ into place

Everything downstream is generated. Edit palette.json, never out/.
"""

import colorsys
import json
import pathlib

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out"


# ---------------------------------------------------------------- color math

def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def rgb2hex(r, g, b):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in (r, g, b))


def shift(h, dl=0.0, ds=1.0):
    """Nudge lightness by dl percentage points, scale saturation by ds."""
    r, g, b = (v / 255 for v in hex2rgb(h))
    hue, lig, sat = colorsys.rgb_to_hls(r, g, b)
    lig = max(0.0, min(1.0, lig + dl / 100))
    sat = max(0.0, min(1.0, sat * ds))
    return rgb2hex(*(v * 255 for v in colorsys.hls_to_rgb(hue, lig, sat)))


def mix(a, b, t):
    A, B = hex2rgb(a), hex2rgb(b)
    return rgb2hex(*(A[i] + (B[i] - A[i]) * t for i in range(3)))


def luminance(h):
    def chan(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(v) for v in hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


# ---------------------------------------------------------------- derivation

HUES = ("red", "green", "yellow", "blue", "magenta", "cyan")


def resolve(core):
    """core (the 16 hand-picked colors) -> the full palette everything else uses."""
    p = dict(core)

    p["fgBright"] = shift(core["fg"], 6)

    # brights: lift, and pull a little saturation back out so they don't go neon
    for k in HUES:
        p["br_" + k] = shift(core[k], 8, 0.94)

    p["black"] = core["bg"]
    p["brBlack"] = mix(core["bg"], core["fg"], 0.34)
    p["white"] = core["fg"]
    p["brWhite"] = p["fgBright"]

    # diff grounds: the background, tinted toward the hue
    p["diffAdd"] = mix(core["bg"], core["green"], 0.13)
    p["diffDel"] = mix(core["bg"], core["red"], 0.13)
    p["diffChange"] = mix(core["bg"], core["blue"], 0.13)
    p["diffText"] = mix(core["bg"], core["blue"], 0.24)

    p["error"] = core["red"]
    p["warning"] = core["yellow"]
    p["info"] = core["blue"]
    p["hint"] = core["cyan"]
    p["ok"] = core["green"]

    # a dimmer error/warn for undercurls and virtual text
    for k in ("error", "warning", "info", "hint"):
        p[k + "Bg"] = mix(core["bg"], p[k], 0.15)

    p["keyword"] = core["magenta"]
    p["func"] = core["blue"]
    p["string"] = core["green"]
    p["number"] = core["yellow"]
    p["constant"] = core["yellow"]
    p["type"] = core["cyan"]
    p["builtin"] = core["red"]
    p["operator"] = core["dim"]
    p["variable"] = core["fg"]
    p["property"] = mix(core["fg"], core["blue"], 0.45)

    p["border"] = shift(core["sel"], 2)
    p["match"] = core["accent"]
    p["search"] = mix(core["bg"], core["yellow"], 0.28)
    p["incSearch"] = core["accent"]
    p["indent"] = shift(core["line"], 3)
    p["indentActive"] = shift(core["sel"], 3)

    return p


# ---------------------------------------------------------------- generators
# Each returns (relative path, file contents). Add a target = add a function.

def ghostty(p):
    ansi = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
    lines = [
        f"# {p['name']} — {p['about']}",
        "# generated from palette.json; do not edit",
        "",
        f"background = {p['bg']}",
        f"foreground = {p['fg']}",
        f"cursor-color = {p['accent']}",
        f"cursor-text = {p['bg']}",
        f"selection-background = {p['sel']}",
        f"selection-foreground = {p['fgBright']}",
        "",
        "# normal",
    ]
    for i, k in enumerate(ansi):
        lines.append(f"palette = {i}={p[k]}")
    lines += ["", "# bright", f"palette = 8={p['brBlack']}"]
    for i, k in enumerate(HUES, start=9):
        lines.append(f"palette = {i}={p['br_' + k]}")
    lines.append(f"palette = 15={p['brWhite']}")
    return f"ghostty/{p['slug']}", "\n".join(lines) + "\n"


def nvim(p):
    """A single-file colorscheme. Drop in ~/.config/nvim/colors/ — no plugin needed."""
    groups = [
        # -- editor chrome
        ("Normal", p["fg"], p["bg"], None),
        ("NormalNC", p["fg"], p["bg"], None),
        ("NormalFloat", p["fg"], p["bgEl"], None),
        ("FloatBorder", p["border"], p["bgEl"], None),
        ("FloatTitle", p["accent"], p["bgEl"], "bold"),
        ("ColorColumn", None, p["bgEl"], None),
        ("Conceal", p["dim"], None, None),
        ("Cursor", p["bg"], p["accent"], None),
        ("lCursor", p["bg"], p["accent"], None),
        ("CursorIM", p["bg"], p["accent"], None),
        ("CursorLine", None, p["line"], None),
        ("CursorColumn", None, p["line"], None),
        ("CursorLineNr", p["accent"], None, "bold"),
        ("LineNr", p["gutter"], None, None),
        ("LineNrAbove", p["gutter"], None, None),
        ("LineNrBelow", p["gutter"], None, None),
        ("SignColumn", p["gutter"], None, None),
        ("FoldColumn", p["gutter"], None, None),
        ("Folded", p["dim"], p["bgEl"], None),
        ("Directory", p["blue"], None, None),
        ("EndOfBuffer", p["bg"], None, None),
        ("ErrorMsg", p["error"], None, None),
        ("WarningMsg", p["warning"], None, None),
        ("ModeMsg", p["fg"], None, "bold"),
        ("MoreMsg", p["blue"], None, None),
        ("MsgArea", p["fg"], None, None),
        ("NonText", p["gutter"], None, None),
        ("Whitespace", p["gutter"], None, None),
        ("SpecialKey", p["gutter"], None, None),
        ("Pmenu", p["fg"], p["bgEl"], None),
        ("PmenuSel", p["fgBright"], p["sel"], "bold"),
        ("PmenuSbar", None, p["bgEl"], None),
        ("PmenuThumb", None, p["sel"], None),
        ("Question", p["blue"], None, None),
        ("QuickFixLine", None, p["sel"], None),
        ("Search", p["fgBright"], p["search"], None),
        ("IncSearch", p["bg"], p["incSearch"], "bold"),
        ("CurSearch", p["bg"], p["incSearch"], "bold"),
        ("Substitute", p["bg"], p["red"], None),
        ("MatchParen", p["match"], None, "bold"),
        ("Visual", None, p["sel"], None),
        ("VisualNOS", None, p["sel"], None),
        ("StatusLine", p["fg"], p["bgAlt"], None),
        ("StatusLineNC", p["comment"], p["bgAlt"], None),
        ("TabLine", p["dim"], p["bgAlt"], None),
        ("TabLineFill", None, p["bgAlt"], None),
        ("TabLineSel", p["fgBright"], p["bg"], "bold"),
        ("WinBar", p["dim"], None, None),
        ("WinBarNC", p["comment"], None, None),
        ("WinSeparator", p["border"], None, None),
        ("VertSplit", p["border"], None, None),
        ("Title", p["accent"], None, "bold"),
        ("SpellBad", None, None, "undercurl", p["error"]),
        ("SpellCap", None, None, "undercurl", p["warning"]),
        ("SpellLocal", None, None, "undercurl", p["info"]),
        ("SpellRare", None, None, "undercurl", p["hint"]),

        # -- syntax
        ("Comment", p["comment"], None, "italic"),
        ("Constant", p["constant"], None, None),
        ("String", p["string"], None, None),
        ("Character", p["string"], None, None),
        ("Number", p["number"], None, None),
        ("Float", p["number"], None, None),
        ("Boolean", p["builtin"], None, None),
        ("Identifier", p["variable"], None, None),
        ("Function", p["func"], None, None),
        ("Statement", p["keyword"], None, None),
        ("Conditional", p["keyword"], None, None),
        ("Repeat", p["keyword"], None, None),
        ("Label", p["keyword"], None, None),
        ("Operator", p["operator"], None, None),
        ("Keyword", p["keyword"], None, None),
        ("Exception", p["builtin"], None, None),
        ("PreProc", p["keyword"], None, None),
        ("Include", p["keyword"], None, None),
        ("Define", p["keyword"], None, None),
        ("Macro", p["keyword"], None, None),
        ("PreCondit", p["keyword"], None, None),
        ("Type", p["type"], None, None),
        ("StorageClass", p["keyword"], None, None),
        ("Structure", p["type"], None, None),
        ("Typedef", p["type"], None, None),
        ("Special", p["cyan"], None, None),
        ("SpecialChar", p["cyan"], None, None),
        ("Tag", p["cyan"], None, None),
        ("Delimiter", p["operator"], None, None),
        ("SpecialComment", p["dim"], None, "italic"),
        ("Debug", p["red"], None, None),
        ("Underlined", p["blue"], None, "underline"),
        ("Ignore", p["comment"], None, None),
        ("Error", p["error"], None, None),
        ("Todo", p["bg"], p["accent"], "bold"),

        # -- treesitter
        ("@variable", p["variable"], None, None),
        ("@variable.builtin", p["builtin"], None, None),
        ("@variable.parameter", p["fg"], None, None),
        ("@variable.member", p["property"], None, None),
        ("@constant", p["constant"], None, None),
        ("@constant.builtin", p["builtin"], None, None),
        ("@constant.macro", p["keyword"], None, None),
        ("@module", p["type"], None, None),
        ("@label", p["keyword"], None, None),
        ("@string", p["string"], None, None),
        ("@string.escape", p["cyan"], None, None),
        ("@string.special", p["cyan"], None, None),
        ("@string.regexp", p["cyan"], None, None),
        ("@character", p["string"], None, None),
        ("@character.special", p["cyan"], None, None),
        ("@boolean", p["builtin"], None, None),
        ("@number", p["number"], None, None),
        ("@number.float", p["number"], None, None),
        ("@type", p["type"], None, None),
        ("@type.builtin", p["type"], None, None),
        ("@type.definition", p["type"], None, None),
        ("@attribute", p["keyword"], None, None),
        ("@property", p["property"], None, None),
        ("@function", p["func"], None, None),
        ("@function.builtin", p["builtin"], None, None),
        ("@function.call", p["func"], None, None),
        ("@function.macro", p["keyword"], None, None),
        ("@function.method", p["func"], None, None),
        ("@function.method.call", p["func"], None, None),
        ("@constructor", p["type"], None, None),
        ("@operator", p["operator"], None, None),
        ("@keyword", p["keyword"], None, None),
        ("@keyword.function", p["keyword"], None, None),
        ("@keyword.operator", p["keyword"], None, None),
        ("@keyword.import", p["keyword"], None, None),
        ("@keyword.return", p["keyword"], None, None),
        ("@keyword.exception", p["builtin"], None, None),
        ("@punctuation.delimiter", p["operator"], None, None),
        ("@punctuation.bracket", p["operator"], None, None),
        ("@punctuation.special", p["cyan"], None, None),
        ("@comment", p["comment"], None, "italic"),
        ("@comment.error", p["error"], None, None),
        ("@comment.warning", p["warning"], None, None),
        ("@comment.todo", p["bg"], p["accent"], "bold"),
        ("@comment.note", p["bg"], p["hint"], "bold"),
        ("@markup.strong", p["fgBright"], None, "bold"),
        ("@markup.italic", p["fg"], None, "italic"),
        ("@markup.strikethrough", p["dim"], None, "strikethrough"),
        ("@markup.underline", p["fg"], None, "underline"),
        ("@markup.heading", p["accent"], None, "bold"),
        ("@markup.quote", p["dim"], None, "italic"),
        ("@markup.link", p["blue"], None, None),
        ("@markup.link.url", p["cyan"], None, "underline"),
        ("@markup.link.label", p["blue"], None, None),
        ("@markup.raw", p["green"], None, None),
        ("@markup.list", p["accent"], None, None),
        ("@markup.list.checked", p["green"], None, None),
        ("@markup.list.unchecked", p["dim"], None, None),
        ("@diff.plus", p["ok"], None, None),
        ("@diff.minus", p["error"], None, None),
        ("@diff.delta", p["info"], None, None),
        ("@tag", p["cyan"], None, None),
        ("@tag.attribute", p["property"], None, None),
        ("@tag.delimiter", p["operator"], None, None),

        # -- lsp semantic tokens
        ("@lsp.type.class", p["type"], None, None),
        ("@lsp.type.decorator", p["keyword"], None, None),
        ("@lsp.type.enum", p["type"], None, None),
        ("@lsp.type.enumMember", p["constant"], None, None),
        ("@lsp.type.interface", p["type"], None, None),
        ("@lsp.type.namespace", p["type"], None, None),
        ("@lsp.type.parameter", p["fg"], None, None),
        ("@lsp.type.property", p["property"], None, None),
        ("@lsp.type.struct", p["type"], None, None),
        ("@lsp.type.type", p["type"], None, None),
        ("@lsp.type.typeParameter", p["type"], None, None),
        ("@lsp.type.variable", p["variable"], None, None),
        ("@lsp.mod.readonly", p["constant"], None, None),
        ("LspReferenceText", None, p["sel"], None),
        ("LspReferenceRead", None, p["sel"], None),
        ("LspReferenceWrite", None, p["sel"], None),
        ("LspInlayHint", p["gutter"], p["bgEl"], "italic"),
        ("LspSignatureActiveParameter", p["accent"], None, "bold"),
        ("LspInfoBorder", p["border"], None, None),

        # -- diagnostics
        ("DiagnosticError", p["error"], None, None),
        ("DiagnosticWarn", p["warning"], None, None),
        ("DiagnosticInfo", p["info"], None, None),
        ("DiagnosticHint", p["hint"], None, None),
        ("DiagnosticOk", p["ok"], None, None),
        ("DiagnosticVirtualTextError", p["error"], p["errorBg"], None),
        ("DiagnosticVirtualTextWarn", p["warning"], p["warningBg"], None),
        ("DiagnosticVirtualTextInfo", p["info"], p["infoBg"], None),
        ("DiagnosticVirtualTextHint", p["hint"], p["hintBg"], None),
        ("DiagnosticUnderlineError", None, None, "undercurl", p["error"]),
        ("DiagnosticUnderlineWarn", None, None, "undercurl", p["warning"]),
        ("DiagnosticUnderlineInfo", None, None, "undercurl", p["info"]),
        ("DiagnosticUnderlineHint", None, None, "undercurl", p["hint"]),
        ("DiagnosticUnnecessary", p["comment"], None, None),

        # -- diff / git
        ("DiffAdd", None, p["diffAdd"], None),
        ("DiffChange", None, p["diffChange"], None),
        ("DiffDelete", None, p["diffDel"], None),
        ("DiffText", None, p["diffText"], None),
        ("Added", p["ok"], None, None),
        ("Changed", p["info"], None, None),
        ("Removed", p["error"], None, None),
        ("diffAdded", p["ok"], None, None),
        ("diffRemoved", p["error"], None, None),
        ("diffChanged", p["info"], None, None),
        ("diffFile", p["cyan"], None, None),
        ("diffLine", p["dim"], None, None),
        ("diffIndexLine", p["dim"], None, None),
        ("GitSignsAdd", p["ok"], None, None),
        ("GitSignsChange", p["info"], None, None),
        ("GitSignsDelete", p["error"], None, None),
        ("GitSignsCurrentLineBlame", p["gutter"], None, "italic"),

        # -- plugins LazyVim ships with
        ("TelescopeNormal", p["fg"], p["bgEl"], None),
        ("TelescopeBorder", p["border"], p["bgEl"], None),
        ("TelescopeTitle", p["accent"], None, "bold"),
        ("TelescopeSelection", p["fgBright"], p["sel"], None),
        ("TelescopeMatching", p["accent"], None, "bold"),
        ("SnacksPickerDir", p["dim"], None, None),
        ("SnacksPickerMatch", p["accent"], None, "bold"),
        ("SnacksNormal", p["fg"], p["bgEl"], None),
        ("SnacksBorder", p["border"], p["bgEl"], None),
        ("SnacksDashboardHeader", p["accent"], None, None),
        ("SnacksDashboardIcon", p["cyan"], None, None),
        ("SnacksDashboardDesc", p["fg"], None, None),
        ("SnacksDashboardKey", p["blue"], None, None),
        ("SnacksDashboardFooter", p["comment"], None, "italic"),
        ("SnacksIndent", p["indent"], None, None),
        ("SnacksIndentScope", p["indentActive"], None, None),
        ("IblIndent", p["indent"], None, None),
        ("IblScope", p["indentActive"], None, None),
        ("BlinkCmpMenu", p["fg"], p["bgEl"], None),
        ("BlinkCmpMenuBorder", p["border"], p["bgEl"], None),
        ("BlinkCmpMenuSelection", p["fgBright"], p["sel"], None),
        ("BlinkCmpLabelMatch", p["accent"], None, "bold"),
        ("BlinkCmpDoc", p["fg"], p["bgEl"], None),
        ("BlinkCmpDocBorder", p["border"], p["bgEl"], None),
        ("BlinkCmpKind", p["cyan"], None, None),
        ("CmpItemAbbrMatch", p["accent"], None, "bold"),
        ("CmpItemKind", p["cyan"], None, None),
        ("WhichKey", p["cyan"], None, None),
        ("WhichKeyGroup", p["blue"], None, None),
        ("WhichKeyDesc", p["fg"], None, None),
        ("WhichKeySeparator", p["comment"], None, None),
        ("WhichKeyFloat", None, p["bgEl"], None),
        ("WhichKeyBorder", p["border"], p["bgEl"], None),
        ("NeoTreeNormal", p["fg"], p["bgAlt"], None),
        ("NeoTreeNormalNC", p["fg"], p["bgAlt"], None),
        ("NeoTreeDirectoryName", p["blue"], None, None),
        ("NeoTreeDirectoryIcon", p["blue"], None, None),
        ("NeoTreeGitModified", p["info"], None, None),
        ("NeoTreeGitUntracked", p["ok"], None, None),
        ("NeoTreeIndentMarker", p["indent"], None, None),
        ("NotifyERRORBorder", p["error"], None, None),
        ("NotifyWARNBorder", p["warning"], None, None),
        ("NotifyINFOBorder", p["info"], None, None),
        ("NotifyERRORTitle", p["error"], None, None),
        ("NotifyWARNTitle", p["warning"], None, None),
        ("NotifyINFOTitle", p["info"], None, None),
        ("NoiceCmdlinePopupBorder", p["border"], None, None),
        ("NoiceCmdlineIcon", p["accent"], None, None),
        ("FlashLabel", p["bg"], p["accent"], "bold"),
        ("MiniIconsAzure", p["blue"], None, None),
        ("MiniIconsBlue", p["blue"], None, None),
        ("MiniIconsCyan", p["cyan"], None, None),
        ("MiniIconsGreen", p["green"], None, None),
        ("MiniIconsGrey", p["dim"], None, None),
        ("MiniIconsOrange", p["accent"], None, None),
        ("MiniIconsPurple", p["magenta"], None, None),
        ("MiniIconsRed", p["red"], None, None),
        ("MiniIconsYellow", p["yellow"], None, None),
    ]

    body = []
    for entry in groups:
        name, fg, bg, style = entry[0], entry[1], entry[2], entry[3]
        sp = entry[4] if len(entry) > 4 else None
        parts = []
        if fg:
            parts.append('fg = "%s"' % fg)
        if bg:
            parts.append('bg = "%s"' % bg)
        if sp:
            parts.append('sp = "%s"' % sp)
        for s in (style or "").split(","):
            if s.strip():
                parts.append("%s = true" % s.strip())
        body.append('  ["%s"] = { %s },' % (name, ", ".join(parts)))

    ansi = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
    term = [f'vim.g.terminal_color_{i} = "{p[k]}"' for i, k in enumerate(ansi)]
    term.append(f'vim.g.terminal_color_8 = "{p["brBlack"]}"')
    term += [f'vim.g.terminal_color_{i} = "{p["br_" + k]}"' for i, k in enumerate(HUES, 9)]
    term.append(f'vim.g.terminal_color_15 = "{p["brWhite"]}"')

    src = f"""-- {p['name']} — {p['about']}
-- generated from palette.json; do not edit

vim.cmd("highlight clear")
if vim.fn.exists("syntax_on") == 1 then
  vim.cmd("syntax reset")
end

vim.o.background = "dark"
vim.o.termguicolors = true
vim.g.colors_name = "{p['slug']}"

local groups = {{
{chr(10).join(body)}
}}

for name, opts in pairs(groups) do
  vim.api.nvim_set_hl(0, name, opts)
end

-- transparent background: :lua vim.g.{p['slug']}_transparent = true (before :colorscheme)
if vim.g.{p['slug']}_transparent then
  for _, g in ipairs({{ "Normal", "NormalNC", "SignColumn", "EndOfBuffer", "FoldColumn" }}) do
    vim.api.nvim_set_hl(0, g, vim.tbl_extend("force", groups[g] or {{}}, {{ bg = "NONE" }}))
  end
end

{chr(10).join(term)}
"""
    return f"nvim/colors/{p['slug']}.lua", src


def lualine(p):
    src = f"""-- {p['name']} statusline — generated from palette.json; do not edit
local M = {{}}

M.normal = {{
  a = {{ fg = "{p['bg']}", bg = "{p['blue']}", gui = "bold" }},
  b = {{ fg = "{p['fg']}", bg = "{p['sel']}" }},
  c = {{ fg = "{p['dim']}", bg = "{p['bgAlt']}" }},
}}
M.insert = {{
  a = {{ fg = "{p['bg']}", bg = "{p['green']}", gui = "bold" }},
  b = {{ fg = "{p['fg']}", bg = "{p['sel']}" }},
  c = {{ fg = "{p['dim']}", bg = "{p['bgAlt']}" }},
}}
M.visual = {{
  a = {{ fg = "{p['bg']}", bg = "{p['magenta']}", gui = "bold" }},
  b = {{ fg = "{p['fg']}", bg = "{p['sel']}" }},
  c = {{ fg = "{p['dim']}", bg = "{p['bgAlt']}" }},
}}
M.replace = {{
  a = {{ fg = "{p['bg']}", bg = "{p['red']}", gui = "bold" }},
  b = {{ fg = "{p['fg']}", bg = "{p['sel']}" }},
  c = {{ fg = "{p['dim']}", bg = "{p['bgAlt']}" }},
}}
M.command = {{
  a = {{ fg = "{p['bg']}", bg = "{p['accent']}", gui = "bold" }},
  b = {{ fg = "{p['fg']}", bg = "{p['sel']}" }},
  c = {{ fg = "{p['dim']}", bg = "{p['bgAlt']}" }},
}}
M.terminal = M.normal
M.inactive = {{
  a = {{ fg = "{p['comment']}", bg = "{p['bgAlt']}" }},
  b = {{ fg = "{p['comment']}", bg = "{p['bgAlt']}" }},
  c = {{ fg = "{p['comment']}", bg = "{p['bgAlt']}" }},
}}

return M
"""
    return f"nvim/lua/lualine/themes/{p['slug']}.lua", src


def vscode(p):
    theme = {
        "name": p["name"],
        "type": "dark",
        "semanticHighlighting": True,
        "colors": {
            "editor.background": p["bg"],
            "editor.foreground": p["fg"],
            "editor.lineHighlightBackground": p["line"],
            "editor.selectionBackground": p["sel"],
            "editor.selectionHighlightBackground": p["sel"],
            "editor.wordHighlightBackground": p["sel"],
            "editor.wordHighlightStrongBackground": p["sel"],
            "editor.findMatchBackground": p["search"],
            "editor.findMatchHighlightBackground": p["sel"],
            "editorCursor.foreground": p["accent"],
            "editorLineNumber.foreground": p["gutter"],
            "editorLineNumber.activeForeground": p["accent"],
            "editorIndentGuide.background1": p["indent"],
            "editorIndentGuide.activeBackground1": p["indentActive"],
            "editorWhitespace.foreground": p["gutter"],
            "editorRuler.foreground": p["line"],
            "editorBracketMatch.background": p["sel"],
            "editorBracketMatch.border": p["accent"],
            "editorError.foreground": p["error"],
            "editorWarning.foreground": p["warning"],
            "editorInfo.foreground": p["info"],
            "editorHint.foreground": p["hint"],
            "editorGutter.addedBackground": p["ok"],
            "editorGutter.modifiedBackground": p["info"],
            "editorGutter.deletedBackground": p["error"],
            "diffEditor.insertedTextBackground": p["diffAdd"] + "80",
            "diffEditor.removedTextBackground": p["diffDel"] + "80",
            "editorWidget.background": p["bgEl"],
            "editorWidget.border": p["border"],
            "editorSuggestWidget.background": p["bgEl"],
            "editorSuggestWidget.border": p["border"],
            "editorSuggestWidget.selectedBackground": p["sel"],
            "editorSuggestWidget.highlightForeground": p["accent"],
            "editorHoverWidget.background": p["bgEl"],
            "editorHoverWidget.border": p["border"],
            "peekViewEditor.background": p["bgEl"],
            "peekViewResult.background": p["bgAlt"],
            "sideBar.background": p["bgAlt"],
            "sideBar.foreground": p["dim"],
            "sideBar.border": p["line"],
            "sideBarTitle.foreground": p["fg"],
            "sideBarSectionHeader.background": p["bgAlt"],
            "sideBarSectionHeader.foreground": p["dim"],
            "activityBar.background": p["bgAlt"],
            "activityBar.foreground": p["fg"],
            "activityBar.inactiveForeground": p["comment"],
            "activityBar.border": p["line"],
            "activityBarBadge.background": p["accent"],
            "activityBarBadge.foreground": p["bg"],
            "statusBar.background": p["bgAlt"],
            "statusBar.foreground": p["dim"],
            "statusBar.border": p["line"],
            "statusBar.noFolderBackground": p["bgAlt"],
            "statusBar.debuggingBackground": p["accent"],
            "statusBar.debuggingForeground": p["bg"],
            "statusBarItem.remoteBackground": p["sel"],
            "statusBarItem.remoteForeground": p["fg"],
            "titleBar.activeBackground": p["bgAlt"],
            "titleBar.activeForeground": p["fg"],
            "titleBar.inactiveBackground": p["bgAlt"],
            "titleBar.inactiveForeground": p["comment"],
            "titleBar.border": p["line"],
            "tab.activeBackground": p["bg"],
            "tab.activeForeground": p["fgBright"],
            "tab.activeBorderTop": p["accent"],
            "tab.inactiveBackground": p["bgAlt"],
            "tab.inactiveForeground": p["comment"],
            "tab.border": p["line"],
            "editorGroupHeader.tabsBackground": p["bgAlt"],
            "editorGroup.border": p["line"],
            "panel.background": p["bgAlt"],
            "panel.border": p["line"],
            "panelTitle.activeForeground": p["fg"],
            "panelTitle.inactiveForeground": p["comment"],
            "terminal.background": p["bg"],
            "terminal.foreground": p["fg"],
            "terminal.ansiBlack": p["black"],
            "terminal.ansiRed": p["red"],
            "terminal.ansiGreen": p["green"],
            "terminal.ansiYellow": p["yellow"],
            "terminal.ansiBlue": p["blue"],
            "terminal.ansiMagenta": p["magenta"],
            "terminal.ansiCyan": p["cyan"],
            "terminal.ansiWhite": p["white"],
            "terminal.ansiBrightBlack": p["brBlack"],
            "terminal.ansiBrightRed": p["br_red"],
            "terminal.ansiBrightGreen": p["br_green"],
            "terminal.ansiBrightYellow": p["br_yellow"],
            "terminal.ansiBrightBlue": p["br_blue"],
            "terminal.ansiBrightMagenta": p["br_magenta"],
            "terminal.ansiBrightCyan": p["br_cyan"],
            "terminal.ansiBrightWhite": p["brWhite"],
            "list.activeSelectionBackground": p["sel"],
            "list.activeSelectionForeground": p["fgBright"],
            "list.inactiveSelectionBackground": p["bgEl"],
            "list.hoverBackground": p["bgEl"],
            "list.highlightForeground": p["accent"],
            "list.errorForeground": p["error"],
            "list.warningForeground": p["warning"],
            "input.background": p["bgEl"],
            "input.foreground": p["fg"],
            "input.border": p["border"],
            "input.placeholderForeground": p["comment"],
            "inputOption.activeBorder": p["accent"],
            "dropdown.background": p["bgEl"],
            "dropdown.border": p["border"],
            "dropdown.foreground": p["fg"],
            "button.background": p["accent"],
            "button.foreground": p["bg"],
            "button.hoverBackground": p["br_yellow"],
            "badge.background": p["sel"],
            "badge.foreground": p["fg"],
            "scrollbarSlider.background": p["sel"] + "99",
            "scrollbarSlider.hoverBackground": p["sel"],
            "scrollbarSlider.activeBackground": p["gutter"],
            "progressBar.background": p["accent"],
            "focusBorder": p["border"],
            "foreground": p["fg"],
            "descriptionForeground": p["dim"],
            "errorForeground": p["error"],
            "widget.shadow": p["bgAlt"] + "80",
            "notifications.background": p["bgEl"],
            "notifications.border": p["border"],
            "breadcrumb.foreground": p["comment"],
            "breadcrumb.focusForeground": p["fg"],
            "menu.background": p["bgEl"],
            "menu.foreground": p["fg"],
            "menu.selectionBackground": p["sel"],
            "menu.border": p["border"],
            "gitDecoration.addedResourceForeground": p["ok"],
            "gitDecoration.modifiedResourceForeground": p["info"],
            "gitDecoration.deletedResourceForeground": p["error"],
            "gitDecoration.untrackedResourceForeground": p["ok"],
            "gitDecoration.ignoredResourceForeground": p["comment"],
            "gitDecoration.conflictingResourceForeground": p["warning"],
            "minimap.findMatchHighlight": p["accent"],
            "minimapSlider.background": p["sel"] + "80",
        },
        "tokenColors": [
            {"scope": ["comment", "punctuation.definition.comment"],
             "settings": {"foreground": p["comment"], "fontStyle": "italic"}},
            {"scope": ["string", "string.quoted", "punctuation.definition.string"],
             "settings": {"foreground": p["string"]}},
            {"scope": ["constant.character.escape", "string.regexp"],
             "settings": {"foreground": p["cyan"]}},
            {"scope": ["constant.numeric", "constant.language.numeric"],
             "settings": {"foreground": p["number"]}},
            {"scope": ["constant.language", "constant.language.boolean", "constant.language.null",
                       "constant.language.undefined", "variable.language.this", "variable.language.super"],
             "settings": {"foreground": p["builtin"]}},
            {"scope": ["constant.other", "variable.other.constant"],
             "settings": {"foreground": p["constant"]}},
            {"scope": ["keyword", "keyword.control", "storage", "storage.type", "storage.modifier"],
             "settings": {"foreground": p["keyword"]}},
            {"scope": ["keyword.operator", "punctuation", "meta.brace"],
             "settings": {"foreground": p["operator"]}},
            {"scope": ["entity.name.function", "support.function", "meta.function-call.generic"],
             "settings": {"foreground": p["func"]}},
            {"scope": ["entity.name.type", "entity.name.class", "entity.name.namespace",
                       "entity.other.inherited-class", "support.type", "support.class"],
             "settings": {"foreground": p["type"]}},
            {"scope": ["variable", "variable.other.readwrite", "meta.definition.variable"],
             "settings": {"foreground": p["variable"]}},
            {"scope": ["variable.parameter"],
             "settings": {"foreground": p["fg"]}},
            {"scope": ["variable.other.property", "variable.other.object.property",
                       "meta.object-literal.key", "support.variable.property"],
             "settings": {"foreground": p["property"]}},
            {"scope": ["entity.name.tag", "support.class.component"],
             "settings": {"foreground": p["cyan"]}},
            {"scope": ["entity.other.attribute-name"],
             "settings": {"foreground": p["property"]}},
            {"scope": ["support.type.property-name.css", "support.constant.property-value.css"],
             "settings": {"foreground": p["property"]}},
            {"scope": ["invalid", "invalid.illegal"],
             "settings": {"foreground": p["error"]}},
            {"scope": ["markup.heading", "entity.name.section"],
             "settings": {"foreground": p["accent"], "fontStyle": "bold"}},
            {"scope": ["markup.bold"], "settings": {"foreground": p["fgBright"], "fontStyle": "bold"}},
            {"scope": ["markup.italic"], "settings": {"fontStyle": "italic"}},
            {"scope": ["markup.inline.raw", "markup.raw"], "settings": {"foreground": p["green"]}},
            {"scope": ["markup.underline.link"], "settings": {"foreground": p["blue"]}},
            {"scope": ["markup.inserted"], "settings": {"foreground": p["ok"]}},
            {"scope": ["markup.deleted"], "settings": {"foreground": p["error"]}},
            {"scope": ["markup.changed"], "settings": {"foreground": p["info"]}},
            {"scope": ["comment.line.todo", "keyword.codetag"],
             "settings": {"foreground": p["accent"], "fontStyle": "bold"}},
        ],
        "semanticTokenColors": {
            "parameter": p["fg"],
            "property": p["property"],
            "variable.readonly": p["constant"],
            "class": p["type"],
            "interface": p["type"],
            "enumMember": p["constant"],
            "function": p["func"],
            "method": p["func"],
            "namespace": p["type"],
        },
    }

    pkg = {
        "name": f"{p['slug']}-theme",
        "displayName": p["name"],
        "description": p["about"],
        "version": "1.0.0",
        "publisher": p["author"],
        "engines": {"vscode": "^1.70.0"},
        "categories": ["Themes"],
        "contributes": {
            "themes": [{
                "label": p["name"],
                "uiTheme": "vs-dark",
                "path": f"./themes/{p['slug']}-color-theme.json",
            }]
        },
    }

    return [
        (f"vscode/themes/{p['slug']}-color-theme.json", json.dumps(theme, indent=2) + "\n"),
        ("vscode/package.json", json.dumps(pkg, indent=2) + "\n"),
    ]


def tmux(p):
    src = f"""# {p['name']} — generated from palette.json; do not edit
# source-file ~/.config/tmux/{p['slug']}.conf

set -g status-style "fg={p['dim']},bg={p['bgAlt']}"
set -g status-left "#[fg={p['bg']},bg={p['blue']},bold] #S #[default] "
set -g status-left-length 30
set -g status-right "#[fg={p['comment']}]#{{?client_prefix,#[fg={p['accent']}]^A ,}}#[fg={p['dim']}]%H:%M #[fg={p['bg']},bg={p['sel']}] #h "
set -g status-right-length 60

setw -g window-status-format "#[fg={p['comment']}] #I:#W "
setw -g window-status-current-format "#[fg={p['fgBright']},bg={p['sel']},bold] #I:#W "
setw -g window-status-activity-style "fg={p['warning']},bg={p['bgAlt']}"
setw -g window-status-bell-style "fg={p['red']},bg={p['bgAlt']}"

set -g pane-border-style "fg={p['line']}"
set -g pane-active-border-style "fg={p['accent']}"

set -g message-style "fg={p['bg']},bg={p['accent']},bold"
set -g message-command-style "fg={p['fg']},bg={p['bgEl']}"

set -g mode-style "fg={p['fgBright']},bg={p['sel']}"
set -g copy-mode-match-style "fg={p['bg']},bg={p['yellow']}"
set -g copy-mode-current-match-style "fg={p['bg']},bg={p['accent']}"

set -g display-panes-active-colour "{p['accent']}"
set -g display-panes-colour "{p['gutter']}"
set -g clock-mode-colour "{p['accent']}"
"""
    return f"tmux/{p['slug']}.conf", src


def zsh(p):
    """Prompt for oh-my-zsh. Blocks, not powerline glyphs — plain JetBrains Mono
    has no U+E0B0, so a chevron prompt would render as tofu."""
    src = f"""# {p['name']} prompt — generated from palette.json; do not edit
# ZSH_THEME="{p['slug']}" in ~/.zshrc, with this file at
# ~/.oh-my-zsh/custom/themes/{p['slug']}.zsh-theme

# ponytail: native %F{{#hex}} truecolor (zsh >= 5.7). zsh emits the SGR and does
# the zero-width accounting itself, so no raw \\e or %{{..%}} wrapping.
_fit_dir="%F{{{p['blue']}}}"
_fit_git="%F{{{p['magenta']}}}"
_fit_ok="%F{{{p['green']}}}"
_fit_err="%F{{{p['red']}}}"
_fit_dim="%F{{{p['comment']}}}"
_fit_acc="%F{{{p['accent']}}}"
_fit_rst="%f"

ZSH_THEME_GIT_PROMPT_PREFIX="${{_fit_git}}"
ZSH_THEME_GIT_PROMPT_SUFFIX="${{_fit_rst}}"
ZSH_THEME_GIT_PROMPT_DIRTY="${{_fit_acc}}*${{_fit_rst}}"
ZSH_THEME_GIT_PROMPT_CLEAN=""

PROMPT='${{_fit_dir}}%~${{_fit_rst}} $(git_prompt_info)
%(?.${{_fit_ok}}.${{_fit_err}})❯${{_fit_rst}} '
RPROMPT='${{_fit_dim}}%*${{_fit_rst}}'
"""
    return f"zsh/{p['slug']}.zsh-theme", src


def preview(p):
    """Source for the repo hero image. `./shot.sh` renders it to assets/preview.png."""
    code = [
        [("c", "// verify a session token against the rotating key set")],
        [],
        [("k", "export async function "), ("f", "verify"), ("o", "("), ("v", "token"),
         ("o", ": "), ("t", "string"), ("o", "): "), ("t", "Promise"), ("o", "&lt;"),
         ("t", "Claims"), ("o", "&gt; {")],
        [("o", "  "), ("k", "const "), ("v", "keys"), ("o", " = "), ("k", "await "),
         ("f", "loadKeys"), ("o", "("), ("n", "3600"), ("o", ")")],
        [("o", "  "), ("k", "if "), ("o", "(!"), ("v", "keys"), ("o", "."), ("pr", "length"),
         ("o", ") "), ("k", "throw new "), ("t", "AuthError"), ("o", "("),
         ("s", "&quot;no signing keys&quot;"), ("o", ")")],
        [],
        [("o", "  "), ("k", "for "), ("o", "("), ("k", "const "), ("v", "key"),
         ("k", " of "), ("v", "keys"), ("o", ") {")],
        [("o", "    "), ("k", "const "), ("v", "claims"), ("o", " = "), ("f", "decode"),
         ("o", "("), ("v", "token"), ("o", ", "), ("v", "key"), ("o", ")")],
        [("o", "    "), ("k", "if "), ("o", "("), ("v", "claims"), ("o", " &amp;&amp; "),
         ("v", "claims"), ("o", "."), ("pr", "exp"), ("o", " &gt; "), ("b", "Date"),
         ("o", "."), ("f", "now"), ("o", "()) "), ("k", "return "), ("v", "claims")],
        [("o", "  }")],
        [],
        [("c", "  // TODO: emit a metric before we give up")],
        [("o", "  "), ("k", "throw new "), ("t", "AuthError"), ("o", "("),
         ("s", "`rejected by "), ("o", "${"), ("v", "keys"), ("o", "."), ("pr", "length"),
         ("o", "}"), ("s", " keys`"), ("o", ")")],
        [("o", "}")],
    ]

    rows = []
    for i, spans in enumerate(code, 1):
        body = "".join(f'<span class="{c}">{t}</span>' for c, t in spans)
        cur = ' class="ln cur"' if i == 9 else ' class="ln"'
        rows.append(f'<span{cur}><i>{i}</i>{body or " "}</span>')

    swatches = "".join(
        f'<span class="sw"><i style="background:{p[k]}"></i>{p[k]}</span>'
        for k in ("red", "green", "yellow", "blue", "magenta", "cyan", "fg", "comment")
    )

    src = f"""<meta charset="utf-8">
<title>{p['name']}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ width:1200px; height:640px; background:{p['bgAlt']};
    font-family:"JetBrains Mono", ui-monospace, monospace;
    display:flex; flex-direction:column; gap:20px; padding:34px 38px;
    -webkit-font-smoothing:antialiased; font-feature-settings:"liga" 0, "calt" 0; }}
  .hdr {{ display:flex; align-items:baseline; gap:13px; }}
  .hdr h1 {{ color:{p['fgBright']}; font-size:23px; font-weight:600; letter-spacing:-.02em; }}
  .hdr .dot {{ color:{p['accent']}; font-size:15px; }}
  .hdr .sub {{ color:{p['comment']}; font-size:12.5px; }}
  .win {{ flex:1; background:{p['bg']}; border:1px solid {p['sel']}; border-radius:7px;
    overflow:hidden; display:flex; flex-direction:column; }}
  .bar {{ display:flex; align-items:center; gap:8px; padding:10px 14px;
    background:{p['bgEl']}; border-bottom:1px solid {p['sel']}; }}
  .bar b {{ width:10px; height:10px; border-radius:50%; display:block; }}
  .bar em {{ margin-left:10px; color:{p['dim']}; font-size:11.5px; font-style:normal; }}
  .code {{ flex:1; padding:16px 0; font-size:14.5px; line-height:1.74; }}
  .ln {{ display:block; padding:0 20px; white-space:pre; color:{p['fg']}; }}
  .ln.cur {{ background:{p['line']}; }}
  .ln i {{ display:inline-block; width:24px; text-align:right; margin-right:18px;
    color:{p['gutter']}; font-style:normal; }}
  .st {{ display:flex; font-size:11.5px; background:{p['bgAlt']}; }}
  .st span {{ padding:5px 13px; }}
  .st .m {{ background:{p['blue']}; color:{p['bg']}; font-weight:600; }}
  .st .g {{ background:{p['sel']}; color:{p['fg']}; }}
  .st .fill {{ flex:1; color:{p['dim']}; }}
  .st .p {{ background:{p['accent']}; color:{p['bg']}; font-weight:600; }}
  .strip {{ display:flex; gap:10px; }}
  .sw {{ flex:1; display:flex; align-items:center; gap:8px; font-size:11px;
    color:{p['comment']}; }}
  .sw i {{ width:20px; height:20px; border-radius:4px; display:block; }}
  .c {{ color:{p['comment']}; font-style:italic; }}
  .k {{ color:{p['keyword']}; }} .f {{ color:{p['func']}; }} .s {{ color:{p['string']}; }}
  .n {{ color:{p['number']}; }} .t {{ color:{p['type']}; }} .b {{ color:{p['builtin']}; }}
  .o {{ color:{p['operator']}; }} .v {{ color:{p['variable']}; }} .pr {{ color:{p['property']}; }}
</style>
<div class="hdr">
  <h1>{p['name']}</h1><span class="dot">&#9679;</span>
  <span class="sub">{p['fg']} on {p['bg']} &nbsp;&middot;&nbsp; {contrast(p['fg'], p['bg']):.1f}:1</span>
</div>
<div class="win">
  <div class="bar">
    <b style="background:{p['red']}"></b><b style="background:{p['yellow']}"></b>
    <b style="background:{p['green']}"></b><em>src/lib/auth.ts</em>
  </div>
  <div class="code">{''.join(rows)}</div>
  <div class="st">
    <span class="m">NORMAL</span><span class="g">main +2</span>
    <span class="fill">&nbsp;src/lib/auth.ts</span><span class="g">17:24</span><span class="p">42%</span>
  </div>
</div>
<div class="strip">{swatches}</div>
"""
    return "preview.html", src


def readme(p):
    checks = [
        ("text on background", contrast(p["fg"], p["bg"])),
        ("dim on background", contrast(p["dim"], p["bg"])),
        ("comment on background", contrast(p["comment"], p["bg"])),
        ("accent on background", contrast(p["accent"], p["bg"])),
    ]
    rows = "\n".join(f"| {n} | {r:.1f}:1 |" for n, r in checks)

    roles = [
        ("bg", "editor background"),
        ("bgAlt", "statusline, sidebar, tab bar"),
        ("bgEl", "floats, popups, completion menu"),
        ("sel", "selection, borders"),
        ("line", "cursorline"),
        ("fg", "body text"),
        ("fgBright", "emphasis, selected item"),
        ("dim", "operators, punctuation"),
        ("comment", "comments"),
        ("gutter", "line numbers, whitespace"),
        ("red", "errors, booleans, builtins"),
        ("green", "strings, diff add"),
        ("yellow", "numbers, constants"),
        ("blue", "functions, diff change"),
        ("magenta", "keywords"),
        ("cyan", "types, tags, escapes"),
        ("accent", "cursor, matched paren, prompt"),
    ]
    # The header + separator rows are what make GitHub parse this as a table.
    # Without them the whole thing renders as literal pipes.
    swatch = "\n".join(
        ["| key | hex | role |", "| --- | --- | --- |"]
        + [f"| `{k}` | `{p[k]}` | {role} |" for k, role in roles]
    )
    slug = p["slug"]
    repo = p["repo"]
    return "../README.md", f"""<h1 align="center">{p['name']}</h1>

<p align="center">
  {p['about']}<br>
  <sub>One palette. Every tool. Generated, not copy-pasted.</sub>
</p>

<p align="center">
  <img src="assets/preview.png" alt="{p['name']} — Neovim" width="900">
</p>

## Install

Everything is generated from a single file, so pick a tool and take the config —
or clone and symlink the lot.

<details>
<summary><b>Ghostty</b></summary>

```sh
mkdir -p ~/.config/ghostty/themes
curl -o ~/.config/ghostty/themes/{slug} \\
  https://raw.githubusercontent.com/{repo}/main/out/ghostty/{slug}
```

Then in `~/.config/ghostty/config`:

```
theme = {slug}
```
</details>

<details>
<summary><b>Neovim</b></summary>

Not a plugin — a single colorscheme file, so there is nothing to manage.

```sh
mkdir -p ~/.config/nvim/colors
curl -o ~/.config/nvim/colors/{slug}.lua \\
  https://raw.githubusercontent.com/{repo}/main/out/nvim/colors/{slug}.lua
```

```lua
vim.cmd.colorscheme("{slug}")
```

LazyVim:

```lua
return {{
  {{ "LazyVim/LazyVim", opts = {{ colorscheme = "{slug}" }} }},
}}
```

Transparent background — set before the colorscheme loads:

```lua
vim.g.{slug}_transparent = true
```
</details>

<details>
<summary><b>lualine</b></summary>

Drop `out/nvim/lua/lualine/themes/{slug}.lua` anywhere on your runtime path, then:

```lua
require("lualine").setup({{ options = {{ theme = "{slug}" }} }})
```
</details>

<details>
<summary><b>VS Code</b></summary>

Not on the Marketplace. Symlink or copy `out/vscode/` into your extensions folder:

```sh
ln -s "$PWD/out/vscode" ~/.vscode/extensions/{slug}-theme
```

Restart, then <kbd>Cmd</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> &rarr; Color Theme &rarr; {p['name']}.
</details>

<details>
<summary><b>tmux</b></summary>

```sh
curl -o ~/.config/tmux/{slug}.conf \\
  https://raw.githubusercontent.com/{repo}/main/out/tmux/{slug}.conf
```

In `~/.tmux.conf`:

```
source-file ~/.config/tmux/{slug}.conf
```
</details>

<details>
<summary><b>zsh (oh-my-zsh)</b></summary>

```sh
curl -o ~/.oh-my-zsh/custom/themes/{slug}.zsh-theme \\
  https://raw.githubusercontent.com/{repo}/main/out/zsh/{slug}.zsh-theme
```

In `~/.zshrc`: `ZSH_THEME="{slug}"`

Uses colored text rather than powerline separators, so it renders correctly in
any monospace font. No Nerd Font required.
</details>

<details>
<summary><b>All of it, kept in sync</b></summary>

```sh
git clone https://github.com/{repo}
cd {slug} && ./install.sh
```

Symlinks every target into place. Edit `palette.json`, run `python3 build.py`,
and every tool updates at once — no reinstall.

Absolute symlinks, so re-run `./install.sh` if you ever move the folder.
</details>

## Palette

{swatch}

Those are the only colors anyone chose. The other ~50 — bright ANSI, diff
grounds, diagnostic tints, syntax roles — are derived in `build.py`, so a hue
can never drift out of sync with its variants.

## Contrast

| pair | ratio |
| --- | --- |
{rows}

Text is at the bright end on purpose: crisp strokes, chosen over the softer
13:1 of an earlier tune. If it blooms on OLED in a dark room, raise `bg` toward
`#141416` rather than dimming `fg` — lifting the ground kills halation without
costing sharpness.

## How it works

```
palette.json     17 colors. the only file you edit.
   |
build.py         derives the rest, writes every config
   |
out/             generated. never edit by hand.
```

Each target is a function taking the resolved palette and returning
`(path, contents)`. Adding a tool means writing one function and appending it to
`TARGETS`. That is the entire extension mechanism.

```sh
python3 build.py     # regenerate out/
./shot.sh            # re-render assets/preview.png
```

No dependencies — Python standard library only.

## License

MIT
"""


TARGETS = [ghostty, nvim, lualine, vscode, tmux, zsh, preview, readme]


# ---------------------------------------------------------------------- main

def main():
    core = json.loads((ROOT / "palette.json").read_text())
    p = resolve(core)

    written = []
    for target in TARGETS:
        result = target(p)
        for path, content in ([result] if isinstance(result, tuple) else result):
            # "../x" escapes out/ — that's how README lands at the repo root
            dest = (OUT / path).resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
            written.append(dest.relative_to(ROOT))

    for f in sorted(written):
        print(f"  {f}")
    print(f"\n{p['name']}  {p['fg']} on {p['bg']}  "
          f"({contrast(p['fg'], p['bg']):.1f}:1)  ->  {len(written)} files")


if __name__ == "__main__":
    main()
