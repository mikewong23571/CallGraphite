"""Configuration management for CallGraphite."""
import json
import os
from typing import Dict, Any


def default_config() -> dict:
    """Return the default configuration."""
    return {
        "llm": {
            "endpoint": "https://api.deepseek.com/v1/chat/completions",
            "api_key": "",  # 用户需要设置自己的API密钥
            "model": "deepseek-chat",
            "temperature": 0.3,
            "max_tokens": 4096
        },
        "visualization": {
            "enabled": True,
            "ascii_graph": True,
            "mermaid_graph": True,
            "mermaid_flow": True,
            "max_depth": 5  # 可视化的最大深度
        },
        "analysis": {
            "comprehensive": True,  # 是否进行综合分析
            "cache_results": True  # 是否缓存分析结果
        }
    }


def load_config() -> Dict[str, Any]:
    """Load configuration from file or environment variables."""
    config = default_config()

    # 尝试从文件加载
    config_path = os.path.expanduser("~/.config/callgraphite/config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                # 递归更新配置
                _update_dict(config, file_config)
        except Exception as e:
            print(f"Error loading config file: {e}")

    # 从环境变量加载
    if "OPENAI_API_KEY" in os.environ:
        config.setdefault("llm", {})["api_key"] = os.environ["OPENAI_API_KEY"]
    if "OPENAI_MODEL" in os.environ:
        config.setdefault("llm", {})["model"] = os.environ["OPENAI_MODEL"]

    return config


def _update_dict(target: Dict, source: Dict) -> None:
    """递归更新字典，保留嵌套结构。"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _update_dict(target[key], value)
        else:
            target[key] = value
