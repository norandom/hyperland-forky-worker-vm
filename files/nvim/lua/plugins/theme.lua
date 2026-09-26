-- cream-blue-light via aether (same as the Omarchy theme), managed by debian-hypr
return {
  {
    "bjarneo/aether.nvim",
    branch = "v3",
    name = "aether",
    priority = 1000,
    opts = {
      colors = {
        bg = "#fff8f0",
        dark_bg = "#f5ede0",
        darker_bg = "#ebe3d6",
        lighter_bg = "#d9d0c0",

        fg = "#2b4570",
        dark_fg = "#8babc7",
        light_fg = "#2b4570",
        bright_fg = "#1a2a3f",
        muted = "#7b96b4",

        red = "#c0605a",
        yellow = "#8a6a20",
        orange = "#8a6a20",
        green = "#5a9e6f",
        cyan = "#5b7fa5",
        blue = "#2b4570",
        magenta = "#7a5aaf",
        brown = "#453510",

        bright_red = "#a0403a",
        bright_yellow = "#a87a2f",
        bright_green = "#3a8e4f",
        bright_cyan = "#3a5a8a",
        bright_blue = "#4a90d9",
        bright_magenta = "#7a5aaf",

        accent = "#4a90d9",
        cursor = "#1a2a3f",
        foreground = "#2b4570",
        background = "#fff8f0",
        selection = "#d5dfeb",
        selection_foreground = "#1a2a3f",
        selection_background = "#d5dfeb",
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
