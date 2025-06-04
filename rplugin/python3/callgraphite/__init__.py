"""Entry point for the CallGraphite Neovim plugin."""

from pynvim import command, plugin

from .capture import get_current_function_text
from .traversal import TraversalManager, traverse_project

@plugin
class CallGraphitePlugin:
    """Neovim plugin for capturing function text using tree-sitter."""

    def __init__(self, nvim):
        self.nvim = nvim
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
        self.manager = traverse_project(self.nvim)

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



