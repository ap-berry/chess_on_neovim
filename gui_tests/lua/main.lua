function ResizeWindows()
    local event = {
      page="Global",
      event="resize",
      opts = {}
    }
    vim.g.app_events = insertValueAndReturnTable(vim.g.app_events, event)
end
  
function insertValueAndReturnTable(tbl, value)
    table.insert(tbl, value)
    return tbl
end