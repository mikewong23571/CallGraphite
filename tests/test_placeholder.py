import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rplugin/python3"))

from callgraphite import CallGraphitePlugin

class DummyNvim:
    def exec_lua(self, script):
        return ''
    def out_write(self, msg):
        self.last_msg = msg


def test_plugin_import():
    plugin = CallGraphitePlugin(DummyNvim())
    assert hasattr(plugin, 'capture_function')
