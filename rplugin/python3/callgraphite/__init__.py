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
        # self.manager = traverse_project(self.nvim)
        # command = 'lua vim.lsp.buf.references()'
        # output = self.nvim.command_output(command)
        # logger.info("command: %s, output: %s", command, output)

        logger.info('CallGraphite')

        # helpers.run_get_buf_references(self.nvim, 1)
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
            CallGraphitePlugin.jump_to_location(nvim, loc[1])
            break

        # nvim.call("setqflist", qf_list, 'r')
        # nvim.command("copen")
