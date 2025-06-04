local id = ...

local client = vim.lsp.get_active_clients({ bufnr = 0 })[1]
local encoding = client and client.offset_encoding or "utf-8"
local params = vim.lsp.util.make_position_params(0, encoding)

vim.lsp.buf_request(0, "textDocument/references", params, function(err, result)

    if err or not result then
        return
    end
    vim.fn._graphite_response({
        id = id,
        type = "references",
        data = result
    })
end)
