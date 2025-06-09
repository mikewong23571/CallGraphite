"""Abstractions for interacting with a language model service."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import json
import requests
from .log import logger
from .config import load_config


class LLMClient:
    """Client used to send prompts to a language model service."""

    # 在文件顶部添加导入
    from .config import load_config

    # 更新__init__方法
    def __init__(self, endpoint: str | None = None, api_key: str | None = None) -> None:
        """Initialize the LLM client.
        
        Args:
            endpoint: The API endpoint URL. If None, uses config or default.
            api_key: The API key. If None, reads from config or environment.
        """
        config = load_config()
        llm_config = config.get("llm", {})

        self.endpoint = endpoint or llm_config.get("endpoint") or "https://api.openai.com/v1/chat/completions"
        self.api_key = api_key or llm_config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        self.model = llm_config.get("model") or "gpt-3.5-turbo"
        self.temperature = llm_config.get("temperature", 0.3)
        self.max_tokens = llm_config.get("max_tokens", 500)

        # 缓存已分析的函数，避免重复请求
        self.cache: Dict[int, Any] = {}

    def analyse_function(self, source: str) -> Dict[str, Any]:
        """初步分析函数，识别关键调用和变量。"""
        # 检查缓存
        cache_key = hash(source)
        if cache_key in self.cache:
            logger.info("Using cached analysis for function")
            return self.cache[cache_key]

        # 构建提示
        prompt = self._build_analysis_prompt(source)

        try:
            # 调用LLM API
            response = self._call_llm_api(prompt)

            # 解析响应
            result = self._parse_analysis_response(response)

            # 缓存结果
            self.cache[cache_key] = result

            return result
        except Exception as e:
            logger.error(f"Error analyzing function: {e}")
            # 返回空结果作为后备
            return {"function_calls": [], "global_vars": [], "key_operations": []}

    def comprehensive_analysis(self, source: str, subcalls_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """基于函数代码和子调用结果进行全面分析。
        
        Args:
            source: 函数源代码
            subcalls_results: 子函数分析结果的字典，键为函数标识符，值为分析结果
            
        Returns:
            全面的函数分析结果
        """
        # 构建提示数据
        prompt_data = {
            "function_source": source,
            "subcalls_results": subcalls_results
        }

        # 构建系统提示
        system_prompt = """You are a code analysis assistant. 
        Based on the function source code and its subcalls' analysis results, provide a comprehensive summary.
        Focus on how the function orchestrates its subcalls and the overall data flow.
        
        Respond in JSON format with the following structure:
        {
            "function_calls": ["function1", "function2"], 
            "global_vars": ["var1", "var2"], 
            "key_operations": ["description1", "description2"],
            "summary": "Overall description of what the function does",
            "data_flow": "Description of how data flows through this function and its subcalls"
        }
        """

        # 构建用户提示
        user_prompt = f"Analyze this function and its subcalls:\n```\n{json.dumps(prompt_data, indent=2)}\n```"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # 调用LLM API
            response = self._call_llm_api(messages)

            # 解析响应
            result = self._parse_analysis_response(response)

            return result
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            # 返回初步分析结果作为后备
            return self.analyse_function(source)

    def _build_analysis_prompt(self, source: str) -> List[Dict[str, str]]:
        """Build a prompt for the LLM to analyze the function."""
        return [
            {
                "role": "system",
                "content": """
            You are a code analysis assistant. 
            Analyze the provided function and identify:
            1. Function calls made within the code (exclude logging calls like log.info, print, console.log and language built-in functions like len, str, int, append, etc.)
            2. Global variables accessed (exclude language constants and built-in variables)
            3. Key operations performed (focus on business logic, data processing, and algorithmic operations)
            4. A brief summary of what the function does
            5. The data flow within the function
            
            EXCLUSIONS - Do NOT include:
            - Logging functions (log.*, print, console.log, fmt.Printf, etc.)
            - Language built-ins with clear semantics (len, str, int, append, range, etc.)
            - Standard library functions with obvious purposes (json.loads, os.path.join, etc.)
            - Error handling keywords (try, catch, throw, panic, etc.)
            - Control flow keywords (if, for, while, return, break, continue, etc.)
            
            FOCUS ON:
            - Custom/user-defined function calls
            - External API calls
            - Database operations
            - File I/O operations (beyond basic open/close)
            - Complex data transformations
            - Business logic functions
            
            EXAMPLE JSON OUTPUT:
            {
                "function_calls": ["calculateTax", "sendNotification", "validateUser"], 
                "global_vars": ["CONFIG_TIMEOUT", "DATABASE_URL"], 
                "key_operations": ["validates user credentials", "calculates tax based on income brackets", "sends email notification"],
                "summary": "Processes user tax calculation request and sends notification",
                "data_flow": "Takes user input -> validates credentials -> calculates tax -> stores result -> sends notification"
            }
            """
            },
            {"role": "user", "content": f"Analyze this function:\n```\n{source}\n```"}
        ]

    def _call_llm_api(self, messages: List[Dict[str, str]]) -> str:
        """Call the LLM API with the given messages."""
        if not self.api_key:
            logger.warning("No API key provided. Using mock response.")
            # 返回一个模拟响应用于测试
            return '{"function_calls": ["example_function"], "global_vars": ["example_var"], "key_operations": ["Example operation"]}'

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,  # 低温度以获得更确定性的响应
            "max_tokens": self.max_tokens,
            "response_format": {
                'type': 'json_object'
            }
        }

        response = requests.post(self.endpoint, headers=headers, json=data)
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]

    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into a structured format."""
        try:
            # 尝试解析JSON响应
            result = json.loads(response)

            # 确保所有必要的键都存在
            result.setdefault("function_calls", [])
            result.setdefault("global_vars", [])
            result.setdefault("key_operations", [])
            result.setdefault("summary", "")
            result.setdefault("data_flow", "")

            return result
        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response as JSON: {response}")
            # 尝试从文本中提取信息（简单的后备方案）
            function_calls = []
            global_vars = []
            key_operations = []
            summary = ""
            data_flow = ""

            # 简单的文本解析逻辑
            lines = response.split("\n")
            current_section = None

            for line in lines:
                line = line.strip()
                if "function call" in line.lower():
                    current_section = "function_calls"
                elif "global variable" in line.lower():
                    current_section = "global_vars"
                elif "key operation" in line.lower():
                    current_section = "key_operations"
                elif "summary" in line.lower():
                    current_section = "summary"
                    summary = ""
                elif "data flow" in line.lower():
                    current_section = "data_flow"
                    data_flow = ""
                elif line and current_section:
                    # 提取项目（假设格式为"- item"或"* item"）
                    if current_section in ["function_calls", "global_vars", "key_operations"] and (
                            line.startswith("-") or line.startswith("*")):
                        item = line[1:].strip()
                        if current_section == "function_calls":
                            function_calls.append(item)
                        elif current_section == "global_vars":
                            global_vars.append(item)
                        elif current_section == "key_operations":
                            key_operations.append(item)
                elif current_section == "summary":
                    summary += line + " "
                elif current_section == "data_flow":
                    data_flow += line + " "

            return {
                "function_calls": function_calls,
                "global_vars": global_vars,
                "key_operations": key_operations,
                "summary": summary.strip(),
                "data_flow": data_flow.strip()
            }
