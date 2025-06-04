"""Call graph traversal logic using LSP and LLM analysis."""
from __future__ import annotations

from typing import Set
from pynvim import Nvim

from .capture import get_current_function_text
from .llm import LLMClient


class TraversalManager:
    """Coordinate DFS traversal of functions within a project."""

    def __init__(self, nvim: Nvim, llm: LLMClient) -> None:
        self.nvim = nvim
        self.llm = llm
        self.visited: Set[str] = set()

    def run(self) -> None:
        """Start traversal from the function under the cursor."""
        source = get_current_function_text(self.nvim)
        if source is None:
            self.nvim.out_write("No root function found\n")
            return
        self.visit_function("<root>", source)

    def visit_function(self, symbol: str, source: str) -> None:
        """Analyse ``source`` and recursively visit its callees."""
        if symbol in self.visited:
            return
        self.visited.add(symbol)

        self.llm.analyse_function(source)
        # TODO: Query LSP for called functions and iterate over them.
        # for child_symbol in self._called_functions(symbol):
        #     child_source = ...
        #     self.visit_function(child_symbol, child_source)

    # def _called_functions(self, symbol: str) -> Iterable[str]:
    #     """Return the names of functions called by ``symbol`` via LSP."""
    #     pass


def traverse_project(nvim: Nvim) -> None:
    """Helper used by the ``:CallGraphite`` command."""
    manager = TraversalManager(nvim, LLMClient())
    manager.run()

