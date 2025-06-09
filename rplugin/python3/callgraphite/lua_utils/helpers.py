# ~/.config/nvim/pythonx/callgraphite.py
import logging
import os

# 设置日志文件路径
LOG_PATH = os.path.expanduser("~/.local/share/nvim/callgraphite.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# 初始化日志
logging.basicConfig(
    level=logging.DEBUG,
    filename=LOG_PATH,
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("CallGraphite")


def load_lua_and_exec(nvim, filename: str, args: list = None):
    """
    Loads and executes a Lua file relative to this plugin's lua_utils directory.

    :param nvim: pynvim.Nvim instance
    :param filename: Lua file name (e.g., 'graphite_request.lua')
    :param args: Optional list of arguments passed to exec_lua()
    """
    base_dir = os.path.dirname(__file__)
    full_path = os.path.join(base_dir, filename)

    try:
        with open(full_path, 'r') as f:
            lua_code = f.read()
        return nvim.exec_lua(lua_code, args or [])
    except Exception as e:
        nvim.err_write(f"[CallGraphite] Failed to load Lua file: {filename}\n")
        nvim.err_write(f"Error: {e}\n")
        return None


def run_get_buf_references(nvim, task_id: int, position=None):
    """
    Execute the Lua script to get buffer references.
    
    This function executes 'get_buf_references.lua' to retrieve reference information
    from the current buffer, typically used for analyzing function call relationships
    and reference dependencies.
    
    :param nvim: pynvim.Nvim instance for interacting with Neovim
    :param task_id: Task identifier for tracking and managing asynchronous tasks
    """
    load_lua_and_exec(nvim, 'get_buf_references.lua', args=[{'id': task_id, 'position': position}])


class FunctionBody:
    def __init__(self, sr, sc, er, ec, lines):
        self.start_row = sr
        self.start_col = sc
        self.end_row = er
        self.end_col = ec
        self.lines = lines  # list of strings (already trimmed by col range)

    def get_content(self):
        return "\n".join(self.lines)

    def search(self, query):
        """
        Search for the first occurrence of query.
        :return: (absolute_row, absolute_col) if found, else None
        """
        for i, line in enumerate(self.lines):
            col = line.find(query)
            if col != -1:
                absolute_row = self.start_row + i
                absolute_col = col if i > 0 else self.start_col + col
                return (absolute_row, absolute_col)
        return None

    def search_all(self, query):
        results = []
        for i, line in enumerate(self.lines):
            offset = 0
            while True:
                col = line.find(query, offset)
                if col == -1:
                    break
                absolute_row = self.start_row + i
                absolute_col = col if i > 0 else self.start_col + col
                results.append((absolute_row, absolute_col))
                offset = col + 1
        return results


def run_get_current_function_body_new(nvim):
    pos = load_lua_and_exec(nvim, 'get_current_function_body.lua', args=[])
    if not pos:
        return None

    sr, sc, er, ec = pos
    lines = nvim.current.buffer[sr:er + 1]
    lines[0] = lines[0][sc:] if sr == er else lines[0][sc:]
    lines[-1] = lines[-1][:ec] if sr != er else lines[-1]

    return FunctionBody(sr, sc, er, ec, lines)


def run_get_current_function_body(nvim):
    """
    Retrieve the body of the function at the current cursor position.
    
    This function executes 'get_current_function_body.lua' to extract the function body
    from the current buffer. It processes the position information returned by the Lua
    script to accurately extract the function's content, handling both single-line and
    multi-line functions.
    
    :param nvim: pynvim.Nvim instance for interacting with Neovim
    :return: str - The extracted function body as a string, or None if no function is found
    
    The function works by:
    1. Getting position coordinates (start_row, start_col, end_row, end_col) from Lua
    2. Extracting the relevant lines from the buffer
    3. Properly handling the first and last lines to get exact function boundaries
    """
    pos = load_lua_and_exec(nvim, 'get_current_function_body.lua', args=[])
    if not pos:
        logger.debug("no pos")
        return None

    sr, sc, er, ec = pos
    lines = nvim.current.buffer[sr:er + 1]
    lines[0] = lines[0][sc:] if sr == er else lines[0][sc:]
    lines[-1] = lines[-1][:ec] if sr != er else lines[-1]
    return "\n".join(lines)
