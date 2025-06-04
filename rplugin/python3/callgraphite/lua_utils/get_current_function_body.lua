local ts_utils = require("nvim-treesitter.ts_utils")
local node = ts_utils.get_node_at_cursor()

vim.lsp.set_log_level("debug")

while node and node:type() ~= "function_declaration" and node:type() ~= "method_declaration" do
    node = node:parent()

    if node ~= nil then
        vim.lsp.log.info("node type: " .. node:type())
    else
        vim.lsp.log.info("node type: " .. "nil")
    end


end

if node ~= nil then
    vim.lsp.log.info("node type: " .. node:type())
else
    vim.lsp.log.info("node type: " .. "nil")
end

if not node then
    return nil
end
local start_row, start_col, end_row, end_col = node:range()
return { start_row, start_col, end_row, end_col }