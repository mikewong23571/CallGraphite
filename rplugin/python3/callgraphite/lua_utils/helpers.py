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


def run_get_buf_references(nvim, task_id: int):
    load_lua_and_exec(nvim, 'get_buf_references.lua', args=[task_id])


def run_get_current_function_body(nvim, task_id: int):
    pos = load_lua_and_exec(nvim, 'get_current_function_body.lua', args=[task_id])
    if not pos:
        logger.debug("no pos")
        return None

    sr, sc, er, ec = pos
    lines = nvim.current.buffer[sr:er + 1]
    lines[0] = lines[0][sc:] if sr == er else lines[0][sc:]
    lines[-1] = lines[-1][:ec] if sr != er else lines[-1]
    return "\n".join(lines)
