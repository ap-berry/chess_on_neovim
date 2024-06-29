function whichbutton()
  vim.g.menu_events = vim.g.menu_events .. vim.api.nvim_win_get_cursor(0)[1] .. " "
end