-- debian-hypr: Berg light when the terminal uses the light "cream" profile
-- (hypr-termtheme), Berg dark otherwise. F4 still toggles.
local f = io.open(vim.fn.expand("~/.local/state/terminator-profile"))
local profile = f and f:read("*l") or "default"
if f then f:close() end
if profile == "cream" then
  vim.api.nvim_create_autocmd("VimEnter", {
    nested = true,
    callback = function() pcall(vim.cmd.colorscheme, "berg-light") end,
  })
end
