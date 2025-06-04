from pynvim import plugin, command, function

@plugin
class CallGraphitePlugin:
    """Neovim plugin for capturing function text using tree-sitter."""

    def __init__(self, nvim):
        self.nvim = nvim

    @command('CaptureFunction', nargs='0', range='')
    def capture_function(self, args, range):
        """Print the text of the function under the cursor."""
        text = self.nvim.exec_lua('''
            local ts_utils = require('nvim-treesitter.ts_utils')
            local node = ts_utils.get_node_at_cursor()
            while node do
                local t = node:type()
                if t == 'function' or t == 'function_definition' or
                   t == 'function_declaration' or t == 'method_definition' then
                    break
                end
                node = node:parent()
            end
            if not node then return nil end
            local sr, sc, er, ec = node:range()
            local lines = vim.api.nvim_buf_get_lines(0, sr, er + 1, false)
            if #lines == 0 then return nil end
            lines[#lines] = string.sub(lines[#lines], 1, ec)
            lines[1] = string.sub(lines[1], sc + 1)
            return table.concat(lines, '\n')
        ''')
        if text:
            self.nvim.out_write(text + '\n')
        else:
            self.nvim.out_write('No function found\n')


