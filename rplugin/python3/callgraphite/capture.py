# -*- coding: utf-8 -*-
"""Utilities for extracting source code from the current buffer."""
from __future__ import annotations
from typing import Optional
from pynvim import Nvim

from .lua_utils.helpers import run_get_current_function_body


def get_current_function_text(nvim: Nvim) -> Optional[str]:
    """Return the text of the function under the cursor.

    The implementation relies on tree-sitter to locate the nearest parent
    function node and then extracts the lines for that range. This function
    uses the Lua implementation in get_current_function_body.lua.
    """
    # 使用task_id=0，因为我们不需要异步回调
    return run_get_current_function_body(nvim)

