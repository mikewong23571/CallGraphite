"""Call graph traversal logic using LSP and LLM analysis."""
from __future__ import annotations

from typing import Iterable, List, Set, Tuple
from pynvim import Nvim

from .capture import get_current_function_text
from .llm import LLMClient


class JumpStack:
    """Maintain jump history for forward/backward navigation."""

    def __init__(self, nvim: Nvim) -> None:
        self.nvim = nvim
        self.stack: List[Tuple[str, int, int]] = []
        self.index: int = -1

    def _jump(self, path: str, line: int, col: int) -> None:
        """Perform a jump within Neovim."""
        self.nvim.command(f"keepjumps edit {path}")
        self.nvim.call("cursor", line, col)

    def push(self, path: str, line: int, col: int) -> None:
        """Jump to ``path`` and record the location."""
        if self.index < len(self.stack) - 1:
            self.stack = self.stack[: self.index + 1]
        self.stack.append((path, line, col))
        self.index += 1
        self._jump(path, line, col)

    def back(self) -> None:
        """Jump backward in the history if possible."""
        if self.index <= 0:
            return
        self.index -= 1
        path, line, col = self.stack[self.index]
        self._jump(path, line, col)

    def forward(self) -> None:
        """Jump forward in the history if possible."""
        if self.index + 1 >= len(self.stack):
            return
        self.index += 1
        path, line, col = self.stack[self.index]
        self._jump(path, line, col)


class TraversalManager:
    """Coordinate DFS traversal of functions within a project."""

    def __init__(self, nvim: Nvim, llm: LLMClient) -> None:
        self.nvim = nvim
        self.llm = llm
        self.visited: Set[str] = set()
        self.jumps = JumpStack(nvim)

    def _cursor_location(self) -> Tuple[str, int, int]:
        """Return the current buffer path, line and column."""
        path = self.nvim.current.buffer.name
        line = int(self.nvim.funcs.line('.'))
        col = int(self.nvim.funcs.col('.'))
        return path, line, col

    def run(self) -> None:
        """Start traversal from the function under the cursor."""
        source = get_current_function_text(self.nvim)
        if source is None:
            self.nvim.out_write("No root function found\n")
            return
        self.jumps.push(*self._cursor_location())
        self.visit_function("<root>", source)

    def visit_function(self, symbol: str, source: str) -> None:
        """Analyse ``source`` and recursively visit its callees."""
        if symbol in self.visited:
            return
        self.visited.add(symbol)

        self.llm.analyse_function(source)
        for uri, line, col in self._called_functions(symbol):
            self.jumps.push(uri, line, col)
            child_source = get_current_function_text(self.nvim)
            if child_source:
                child_symbol = f"{uri}:{line}:{col}"
                self.visit_function(child_symbol, child_source)
            self.jumps.back()

    def _called_functions(self, symbol: str) -> Iterable[Tuple[str, int, int]]:
        """Return locations of functions referenced by ``symbol``."""
        # TODO: Implement real LSP queries. ``symbol`` is unused for now.
        return []

    # def _called_functions(self, symbol: str) -> Iterable[str]:
    #     """Return the names of functions called by ``symbol`` via LSP."""
    #     pass


def traverse_project(nvim: Nvim) -> TraversalManager:
    """Helper used by the ``:CallGraphite`` command."""
    manager = TraversalManager(nvim, LLMClient())
    manager.run()
    return manager

