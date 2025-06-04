"""Entry point for the CallGraphite Neovim plugin."""

from __future__ import annotations

import pynvim
from pynvim import command, plugin, function

from .capture import get_current_function_text
from .log import logger
from .lua_utils import helpers
from .traversal import TraversalManager, traverse_project


@plugin
class CallGraphitePlugin:
    """Neovim plugin for capturing function text using tree-sitter."""

    def __init__(self, nvim):
        self.nvim: pynvim.Nvim = nvim
        self.manager: TraversalManager | None = None

    @command('CaptureFunction', nargs='0', range='')
    def capture_function(self, args, range):
        """Print the text of the function under the cursor."""
        text = get_current_function_text(self.nvim)
        if text:
            self.nvim.out_write(text + '\n')
        else:
            self.nvim.out_write('No function found\n')

    @command('CallGraphite', nargs='0', range='')
    def call_graphite(self, args, range):
        """Traverse the project and analyse functions via an LLM."""
        logger.info('CallGraphite')
        
        # 显示开始消息
        self.nvim.out_write("CallGraphite: Starting analysis...\n")
        
        # 设置状态栏消息
        self.nvim.command('let &statusline = "%#StatusLine#CallGraphite: Analyzing...%="')
        
        try:
            # 使用遍历管理器
            self.manager = traverse_project(self.nvim)
            
            # 恢复状态栏
            self.nvim.command('let &statusline = &statusline')
            
            # 显示完成消息
            self.nvim.out_write("CallGraphite: Analysis complete!\n")
        except Exception as e:
            # 处理错误
            logger.error(f"Error in CallGraphite: {e}")
            self.nvim.err_write(f"CallGraphite error: {e}\n")
            
            # 恢复状态栏
            self.nvim.command('let &statusline = &statusline')
        
        # 记录函数体，用于调试
        logger.info('CallGraphite, func body: %s', helpers.run_get_current_function_body(self.nvim, 1))

    @command('CallGraphiteBack', nargs='0', range='')
    def call_graphite_back(self, args, range):
        """Move back in the traversal stack."""
        if self.manager:
            self.manager.jumps.back()

    @command('CallGraphiteForward', nargs='0', range='')
    def call_graphite_forward(self, args, range):
        """Move forward in the traversal stack."""
        if self.manager:
            self.manager.jumps.forward()

    @function("_graphite_response", sync=False)
    def handle_graphite_response(self, args):
        try:
            logger.info("CallGraphite response: %s", args)
            logger.info("CallGraphite response: %s", args[0]['data'])
            self.populate_quickfix(self.nvim, args[0]['data'])
        except Exception:
            pass

    @staticmethod
    def jump_to_location(nvim, location):
        uri = location["uri"]
        path = uri.replace("file://", "")
        line = location["range"]["start"]["line"] + 1  # 1-based in Vim
        col = location["range"]["start"]["character"] + 1

        nvim.command(f"edit {path}")
        nvim.call("cursor", line, col)

    @staticmethod
    def populate_quickfix(nvim, locations):
        qf_list = []
        for loc in locations:
            uri = loc["uri"]
            path = uri.replace("file://", "")
            line = loc["range"]["start"]["line"] + 1
            col = loc["range"]["start"]["character"] + 1
            qf_list.append({
                "filename": path,
                "lnum": line,
                "col": col,
                "text": f"{path}:{line}:{col}"
            })
            # 修复这里的bug，使用loc而不是loc[1]
            CallGraphitePlugin.jump_to_location(nvim, loc)
            break

        # 取消注释这些行，启用quickfix列表
        nvim.call("setqflist", qf_list, 'r')
        nvim.command("copen")


@neovim.command('CallGraphiteVisualize', nargs='*', range='', sync=True)
def visualize_call_graph(self, args, range):
    """Generate and display call graph visualization for the current function."""
    try:
        # 获取当前函数文本
        source = get_current_function_text(self.nvim)
        if not source:
            self.nvim.command('echo "No function found at cursor position"')
            return

        # 创建遍历管理器
        traversal = TraversalManager(self.nvim)
        
        # 获取当前位置
        uri, line, col = traversal._cursor_location()
        symbol = f"{uri}:{line}:{col}"
        
        # 分析函数并生成可视化
        traversal.visit_function(symbol, source)
        
        # 单独生成可视化（如果用户只想要可视化而不进行完整遍历）
        traversal._generate_visualizations(symbol)
        
        self.nvim.command('echo "Call graph visualization generated"')
    except Exception as e:
        logger.error(f"Error in visualize_call_graph: {e}")
        self.nvim.command(f'echoerr "Error generating visualization: {str(e)}"')
