-- Managed by debian-hypr. Matches the terminal (Terminator/xfce4-terminal
-- "cobalt" profile, github.com/norandom/opencode-cream-blue): cream text on
-- cobalt, gold accents. The background stays transparent (plugin/after/
-- transparency.lua), so the navy profile works too.
return {
  {
    "bjarneo/aether.nvim",
    branch = "v3",
    name = "aether",
    priority = 1000,
    opts = {
      colors = {
        bg = "#0049b2",
        dark_bg = "#0041a0",
        darker_bg = "#00347d",
        lighter_bg = "#1453af",

        fg = "#fff8f0",
        dark_fg = "#c4bba3",
        light_fg = "#e8dfc9",
        bright_fg = "#ffffff",
        muted = "#8bb4e0",

        red = "#e87a74",
        yellow = "#f1dc9a",
        orange = "#ffe9a8",
        green = "#7ac48a",
        cyan = "#8bb4e0",
        blue = "#b8d3f0",
        magenta = "#d29acb",
        brown = "#c4bba3",

        bright_red = "#e87a74",
        bright_yellow = "#ffe9a8",
        bright_green = "#7ac48a",
        bright_cyan = "#b8d3f0",
        bright_blue = "#b8d3f0",
        bright_magenta = "#d29acb",

        accent = "#f1dc9a",
        cursor = "#f1dc9a",
        foreground = "#fff8f0",
        background = "#0049b2",
        selection = "#1453af",
        selection_foreground = "#fff8f0",
        selection_background = "#1453af",
      },
    },
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "aether",
    },
  },
}
