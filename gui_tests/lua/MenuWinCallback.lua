function MenuWinCallback()
  local line = vim.api.nvim_win_get_cursor(0)[1]
  local event = {
    page="Home",
    event="menu",
    opts={
      line=line
    }
  }
  vim.g.app_events = insertValueAndReturnTable(vim.g.app_events, event)
end


function insertValueAndReturnTable(tbl, value)
  table.insert(tbl, value)
  return tbl
end