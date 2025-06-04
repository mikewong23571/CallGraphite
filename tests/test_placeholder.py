import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rplugin/python3"))

from callgraphite import CallGraphitePlugin
from callgraphite.traversal import JumpStack

class DummyNvim:
    def exec_lua(self, script):
        return ''
    def out_write(self, msg):
        self.last_msg = msg
    def command(self, cmd):
        self.last_cmd = cmd
    def call(self, name, *args):
        self.last_call = (name, args)


def test_plugin_import():
    plugin = CallGraphitePlugin(DummyNvim())
    assert hasattr(plugin, 'capture_function')


def test_jump_stack_navigation():
    nvim = DummyNvim()
    js = JumpStack(nvim)
    js.push('file_a', 1, 1)
    js.push('file_b', 2, 1)
    js.back()
    assert js.index == 0
    js.forward()
    assert js.index == 1
