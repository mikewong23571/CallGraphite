local args = ...
local id, position

id = args.id
position = args.position  -- 可为 nil

local bufnr = 0
local client = vim.lsp.get_active_clients({ bufnr = bufnr })[1]
local encoding = client and client.offset_encoding or "utf-8"

-- 构造完整 LSP 请求参数
local params = {
    textDocument = vim.lsp.util.make_text_document_params(bufnr),
    position = position or vim.api.nvim_win_get_cursor(0),
}

if not position then
    local row, col = unpack(params.position)
    params.position = { line = row - 1, character = col }  -- LSP 是 0-based
end

-- ⚙️ 可选：处理编码转换（有需要时）
params.position = vim.lsp.util.convert_position(params.position, encoding)

-- 发起引用请求
vim.lsp.buf_request(bufnr, "textDocument/references", params, function(err, result)
    if err or not result then
        return
    end

    vim.fn._graphite_response({
        id = id,
        type = "references",
        data = result
    })
end)
