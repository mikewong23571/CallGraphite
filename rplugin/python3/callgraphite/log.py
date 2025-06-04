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
