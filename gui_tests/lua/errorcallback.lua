function ErrorWinCallBack()
    local pressedat = vim.api.nvim_win_get_cursor(0)[1]

    local endnumber = vim.b.end_line_number

    if endnumber == pressedat then
        vim.api.nvim_win_close(0, true)
    end
end

