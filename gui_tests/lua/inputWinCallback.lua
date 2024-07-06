function inputWinCallback()
    local input = vim.api.nvim_buf_get_lines(0, 0, 1, false)[1]
    input = string.gsub(input, " ", "")

    if input == "menu" then
        append_event("Game", "kill_game_window", {})
    elseif input == "kill_main" then
        append_event("Global", "kill_main_process", {})
    elseif input == "resign" then
        append_event("Game", "resign", {})
    elseif input == "abort" then
        append_event("Game", "abort", {})
    elseif input ~= "" then 
        append_event("Game", "make_move", {move=input})
    end

    vim.api.nvim_buf_set_lines(0, 0, -1, false, {})
end

function append_event(page, event, opts)
    vim.g.app_events = insertValueAndReturnTable(vim.g.app_events, {
        page=page,
        event=event,
        opts= opts
    })    
end
function insertValueAndReturnTable(tbl, value)
    table.insert(tbl, value)
    return tbl
end