function whichbutton()
  vim.g.events = vim.g.events .. " pressed:" .. vim.api.nvim_win_get_cursor(0)[1]
end