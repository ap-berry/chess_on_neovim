function MenuWinCallback()
  local line = vim.api.nvim_win_get_cursor(0)[1]
  local event = {
    page="Menu",
    event="enter",
    opts={
      line=line -1 --converting to 0 based index for python lists
    }
  }
  vim.g.app_events = insertValueAndReturnTable(vim.g.app_events, event)
end

function RefreshMenu()
  local event = {
    page="Menu",
    event="refresh",
    opts = {}
  }
  vim.g.app_events = insertValueAndReturnTable(vim.g.app_events, event)
end

function insertValueAndReturnTable(tbl, value)
  table.insert(tbl, value)
  return tbl
end