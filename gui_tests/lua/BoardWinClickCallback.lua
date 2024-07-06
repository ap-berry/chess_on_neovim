function BoardWinLeftClickCallback()
    cursor = vim.api.nvim_win_get_cursor(0)
    append_event("Board", "leftmouse", {pos=cursor})
end


function append_event(page, event, opts)
    vim.g.app_events = insertValueAndReturnTable(vim.g.app_events, {
        page=page,
        event=event,
        opts= opts
    })    
end
