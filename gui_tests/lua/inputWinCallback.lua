function inputWinCallback()
    local input = vim.api.nvim_buf_get_lines(0, 0, 1, false)[1]
    input = string.gsub(input, " ", "")

    if input == "exit" then
        append_event("Global", "exit", {})
    elseif input == "menu" then
        append_event("Game", "pass_control", {action="kill_game_window"})
    elseif input == "resign" then
        append_event("Game", "internal", {action="resign"})
    elseif input == "abort" then
        append_event("Game", "internal", {action="abort"})
    elseif input == "flip" then
        append_event("Game", "internal", {action="flip"})
    elseif input ~= "" then 
        append_event("Game", "internal", { action="make_move", move=input})
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