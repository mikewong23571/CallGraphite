"""Call graph traversal logic using LSP and LLM analysis."""
from __future__ import annotations

from typing import Iterable, List, Set, Tuple
from pynvim import Nvim

from .capture import get_current_function_text
from .llm import LLMClient
from .log import logger

# 添加用于生成图表的库
import json


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
    """Coordinate a DFS traversal of function calls."""

    def __init__(self, nvim: Nvim) -> None:
        """Initialize with the current Neovim instance."""
        self.nvim = nvim
        self.jumps = JumpStack(nvim)
        self.visited: Set[str] = set()
        self.llm = LLMClient()
        # 添加调用关系图数据结构
        self.call_graph = {}
        # 添加函数分析结果缓存
        self.analysis_cache = {}
        # 添加子调用结果缓存
        self.subcalls_results = {}

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

    def visit_function(self, symbol: str, source: str) -> Dict[str, Any]:
        """分析函数并递归访问其调用的函数。"""
        if symbol in self.visited:
            return self.subcalls_results.get(symbol, {})
        self.visited.add(symbol)
    
        # 第一阶段：初步分析函数
        initial_analysis = self.llm.analyse_function(source)
        
        # 获取函数调用位置
        called_functions = self._called_functions(symbol)
        
        # 过滤调用，优先处理LLM识别的重要函数调用
        prioritized_calls = self._prioritize_calls(called_functions, initial_analysis)
        
        # 子调用的分析结果
        subcalls_analysis = {}
        
        # 遍历调用
        for uri, line, col in prioritized_calls:
            self.jumps.push(uri, line, col)
            child_source = get_current_function_text(self.nvim)
            if child_source:
                child_symbol = f"{uri}:{line}:{col}"
                # 递归访问子函数，并获取其分析结果
                child_analysis = self.visit_function(child_symbol, child_source)
                if child_analysis:
                    subcalls_analysis[child_symbol] = child_analysis
            self.jumps.back()
        
        # 第二阶段：基于子调用结果进行全面分析
        if subcalls_analysis:
            comprehensive_analysis = self.llm.comprehensive_analysis(source, subcalls_analysis)
        else:
            # 如果没有子调用，直接使用初步分析结果
            comprehensive_analysis = initial_analysis
        
        # 显示分析结果给用户
        self._display_analysis(symbol, comprehensive_analysis, subcalls_analysis)
        
        # 缓存分析结果
        self.subcalls_results[symbol] = comprehensive_analysis
        
        return comprehensive_analysis
    
    def _comprehensive_analysis(self, symbol: str, current_analysis: dict, subcalls_analysis: dict) -> dict:
        """基于当前函数分析和子调用结果进行更全面的分析。"""
        # 如果没有子调用，直接返回当前分析
        if not subcalls_analysis:
            return current_analysis
            
        # 准备提交给LLM的数据
        prompt_data = {
            "current_function": symbol,
            "current_analysis": current_analysis,
            "subcalls": {}
        }
        
        # 添加子调用信息
        for child_symbol, child_analysis in subcalls_analysis.items():
            prompt_data["subcalls"][child_symbol] = child_analysis
        
        # 构建提示
        prompt = [
            {"role": "system", "content": """You are a code analysis assistant. 
            Based on the current function analysis and its subcalls' analyses, provide a comprehensive summary.
            Focus on how the function orchestrates its subcalls and the overall data flow.
            
            Respond in JSON format with the following structure:
            {
                "function_calls": ["function1", "function2"], 
                "global_vars": ["var1", "var2"], 
                "key_operations": ["description1", "description2"],
                "summary": "Overall description of what the function does",
                "data_flow": "Description of how data flows through this function and its subcalls"
            }
            """}, 
            {"role": "user", "content": f"Analyze this function and its subcalls:\n```\n{json.dumps(prompt_data, indent=2)}\n```"}
        ]
        
        try:
            # 调用LLM API
            response = self.llm._call_llm_api(prompt)
            
            # 解析响应
            result = self.llm._parse_analysis_response(response)
            
            # 确保包含原始分析的所有字段
            for key, value in current_analysis.items():
                if key not in result:
                    result[key] = value
            
            return result
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return current_analysis
    
    def _display_analysis(self, symbol: str, analysis: dict, subcalls_analysis: dict = None) -> None:
        """显示函数分析结果。"""
        # 创建一个新的缓冲区来显示分析结果
        self.nvim.command("botright new CallGraphite-Analysis")
        self.nvim.command("setlocal buftype=nofile bufhidden=wipe noswapfile nowrap")
        
        # 准备显示内容
        lines = [f"# Analysis of {symbol}", ""]
        
        # 添加综合摘要（如果有）
        if "summary" in analysis:
            lines.append("## Summary")
            lines.append(analysis["summary"])
            lines.append("")
        
        # 添加数据流（如果有）
        if "data_flow" in analysis:
            lines.append("## Data Flow")
            lines.append(analysis["data_flow"])
            lines.append("")
        
        # 添加函数调用
        lines.append("## Function Calls")
        for func in analysis.get("function_calls", []):
            lines.append(f"- {func}")
        lines.append("")
        
        # 添加全局变量
        lines.append("## Global Variables")
        for var in analysis.get("global_vars", []):
            lines.append(f"- {var}")
        lines.append("")
        
        # 添加关键操作
        lines.append("## Key Operations")
        for op in analysis.get("key_operations", []):
            lines.append(f"- {op}")
        
        # 如果有子调用分析，添加子调用摘要
        if subcalls_analysis and subcalls_analysis:
            lines.append("")
            lines.append("## Subcalls Summary")
            for child_symbol, child_analysis in subcalls_analysis.items():
                lines.append(f"### {child_symbol}")
                if "summary" in child_analysis:
                    lines.append(child_analysis["summary"])
                else:
                    # 如果没有摘要，显示关键操作
                    for op in child_analysis.get("key_operations", [])[:2]:  # 只显示前两个操作
                        lines.append(f"- {op}")
                lines.append("")
        
        # 设置缓冲区内容
        self.nvim.current.buffer[:] = lines
        
        # 设置为markdown语法高亮
        self.nvim.command("setlocal filetype=markdown")
        
        # 返回到原始缓冲区
        self.nvim.command("wincmd p")
    
    def _generate_visualizations(self, root_symbol: str) -> None:
        """生成并显示调用图和流程图。"""
        # 创建一个新的缓冲区来显示可视化
        self.nvim.command("botright vnew CallGraphite-Visualizations")
        self.nvim.command("setlocal buftype=nofile bufhidden=wipe noswapfile nowrap")
        
        # 准备显示内容
        lines = [f"# Visualizations for {root_symbol}", ""]
        
        # 生成ASCII调用图
        lines.append("## Call Graph (ASCII)")
        lines.append("```")
        lines.extend(self._generate_ascii_call_graph(root_symbol))
        lines.append("```")
        lines.append("")
        
        # 生成Mermaid调用图
        lines.append("## Call Graph (Mermaid)")
        lines.append("```mermaid")
        lines.append("graph TD")
        lines.extend(self._generate_mermaid_call_graph(root_symbol))
        lines.append("```")
        lines.append("")
        
        # 生成Mermaid流程图
        lines.append("## Flow Chart (Mermaid)")
        lines.append("```mermaid")
        lines.append("flowchart TD")
        lines.extend(self._generate_mermaid_flow_chart(root_symbol))
        lines.append("```")
        
        # 设置缓冲区内容
        self.nvim.current.buffer[:] = lines
        
        # 设置为markdown语法高亮
        self.nvim.command("setlocal filetype=markdown")
        
        # 返回到原始缓冲区
        self.nvim.command("wincmd p")
    
    def _generate_ascii_call_graph(self, root_symbol: str, indent: str = "", visited: Set[str] = None) -> List[str]:
        """生成ASCII格式的调用图。"""
        if visited is None:
            visited = set()
            
        if root_symbol in visited:
            return [f"{indent}└── {root_symbol} (recursive)"]
            
        visited.add(root_symbol)
        
        lines = [f"{indent}└── {root_symbol}"]
        
        # 获取子调用
        calls = self.call_graph.get(root_symbol, {}).get("calls", [])
        
        for i, call in enumerate(calls):
            is_last = i == len(calls) - 1
            new_indent = indent + "    "
            
            # 递归生成子调用的图
            child_lines = self._generate_ascii_call_graph(call, new_indent, visited.copy())
            lines.extend(child_lines)
        
        return lines
    
    def _generate_mermaid_call_graph(self, root_symbol: str, visited: Set[str] = None) -> List[str]:
        """生成Mermaid格式的调用图。"""
        if visited is None:
            visited = set()
            
        if root_symbol in visited:
            return []  # 避免循环引用
            
        visited.add(root_symbol)
        
        lines = []
        
        # 为节点创建唯一ID
        node_id = f"node_{hash(root_symbol) % 10000}"
        
        # 添加节点定义
        short_name = root_symbol.split("/")[-1].split(":")[0]  # 简化显示名称
        lines.append(f"    {node_id}[\"{short_name}\"]")
        
        # 获取子调用
        calls = self.call_graph.get(root_symbol, {}).get("calls", [])
        
        for call in calls:
            # 为子节点创建唯一ID
            child_id = f"node_{hash(call) % 10000}"
            
            # 添加边
            lines.append(f"    {node_id} --> {child_id}")
            
            # 递归生成子调用的图
            child_lines = self._generate_mermaid_call_graph(call, visited.copy())
            lines.extend(child_lines)
        
        return lines
    
    def _generate_mermaid_flow_chart(self, root_symbol: str, visited: Set[str] = None) -> List[str]:
        """生成Mermaid格式的流程图。"""
        if visited is None:
            visited = set()
            
        if root_symbol in visited:
            return []  # 避免循环引用
            
        visited.add(root_symbol)
        
        lines = []
        
        # 为节点创建唯一ID
        node_id = f"node_{hash(root_symbol) % 10000}"
        
        # 获取函数分析
        analysis = self.call_graph.get(root_symbol, {}).get("analysis", {})
        
        # 添加节点定义，包含关键操作
        short_name = root_symbol.split("/")[-1].split(":")[0]  # 简化显示名称
        key_ops = "<br>".join(analysis.get("key_operations", [])[:2])  # 只显示前两个关键操作
        if key_ops:
            lines.append(f"    {node_id}[\"{short_name}<br>{key_ops}\"]")
        else:
            lines.append(f"    {node_id}[\"{short_name}\"]")
        
        # 获取子调用
        calls = self.call_graph.get(root_symbol, {}).get("calls", [])
        
        for i, call in enumerate(calls):
            # 为子节点创建唯一ID
            child_id = f"node_{hash(call) % 10000}"
            
            # 添加边，包含数据流信息（如果有）
            if "data_flow" in analysis:
                lines.append(f"    {node_id} -->|data flow| {child_id}")
            else:
                lines.append(f"    {node_id} --> {child_id}")
            
            # 递归生成子调用的图
            child_lines = self._generate_mermaid_flow_chart(call, visited.copy())
            lines.extend(child_lines)
        
        return lines

    def _prioritize_calls(self, calls, analysis: dict) -> list:
        """根据LLM分析结果对函数调用进行优先级排序。"""
        # 获取LLM识别的函数调用
        important_calls = set(analysis.get("function_calls", []))
        
        # 对调用进行排序，优先处理LLM识别的重要函数
        prioritized = []
        other_calls = []
        
        for call in calls:
            uri, line, col = call
            # 从URI中提取函数名（简化处理，实际可能需要更复杂的逻辑）
            func_name = uri.split("/")[-1].split(".")[0]
            
            if any(important in func_name.lower() for important in important_calls):
                prioritized.append(call)
            else:
                other_calls.append(call)
        
        # 返回排序后的调用列表
        return prioritized + other_calls

    def _called_functions(self, symbol: str) -> Iterable[Tuple[str, int, int]]:
        """Return locations of functions referenced by ``symbol``."""
        # 创建一个Future对象来存储异步结果
        from concurrent.futures import Future
        result_future = Future()
        
        # 定义回调函数
        def on_references_result(args):
            if args and 'data' in args and args['data']:
                result_future.set_result(args['data'])
            else:
                result_future.set_result([])
        
        # 保存原始回调
        original_handler = self.nvim.vars.get('_graphite_handler', None)
        
        # 设置我们的回调
        self.nvim.vars['_graphite_handler'] = on_references_result
        
        # 获取当前位置的引用
        from .lua_utils.helpers import run_get_buf_references
        run_get_buf_references(self.nvim, 1)
        
        # 等待结果（这里可能需要超时处理）
        try:
            locations = result_future.result(timeout=2.0)
            
            # 恢复原始回调
            if original_handler:
                self.nvim.vars['_graphite_handler'] = original_handler
            else:
                del self.nvim.vars['_graphite_handler']
                
            # 转换为需要的格式
            result = []
            for loc in locations:
                uri = loc["uri"]
                line = loc["range"]["start"]["line"] + 1  # 1-based in Vim
                col = loc["range"]["start"]["character"] + 1
                result.append((uri, line, col))
            return result
        except Exception as e:
            # 处理超时或其他错误
            self.nvim.out_write(f"Error getting references: {e}\n")
            return []

    # def _called_functions(self, symbol: str) -> Iterable[str]:
    #     """Return the names of functions called by ``symbol`` via LSP."""
    #     pass


def traverse_project(nvim: Nvim) -> TraversalManager:
    """Helper used by the ``:CallGraphite`` command."""
    manager = TraversalManager(nvim, LLMClient())
    manager.run()
    return manager

