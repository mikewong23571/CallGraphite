local ts_utils = require("nvim-treesitter.ts_utils")
local node = ts_utils.get_node_at_cursor()

-- 向上查找函数节点
while node and node:type() ~= "function_declaration" and node:type() ~= "method_declaration" do
    node = node:parent()

    if node ~= nil then
        vim.lsp.log.info("node type: " .. node:type())
    else
        vim.lsp.log.info("node type: " .. "nil")
    end
end

-- 如果没找到函数节点，返回 nil
if not node then
    return nil
end

-- 🔍 遍历该函数体内的所有子节点
local function print_node_tree(n, indent)
    indent = indent or 0
    local prefix = string.rep("  ", indent)

    -- 获取节点类型和文本
    local nodetype = n:type()
    local text = vim.treesitter.get_node_text(n, 0):gsub("\n", "\\n")

    -- 打印信息
    vim.lsp.log.info(prefix .. nodetype .. " -> " .. text)

    -- 递归打印子节点
    for child in n:iter_children() do
        print_node_tree(child, indent + 1)
    end
end

-- 🔧 打印整个函数节点结构
print_node_tree(node)

-- ✅ 返回函数范围（不变）
local start_row, start_col, end_row, end_col = node:range()
return { start_row, start_col, end_row, end_col }
