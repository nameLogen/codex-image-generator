#!/usr/bin/env python3
"""Codex 可用的 MCP 图片生成工具，通过 codex-proxy 调用 image_generation。"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool


# 默认 Codex 配置路径
CODEX_CONFIG_PATH = Path.home() / ".codex" / "config.toml"
TOOL_SECTION = "mcp_servers.image_generator"


def get_proxy_config():
    """从环境变量读取 codex-proxy 配置。"""
    base_url = os.environ.get("CODEX_PROXY_URL", "").strip()
    api_key = os.environ.get("CODEX_PROXY_API_KEY", "").strip()

    if not base_url:
        raise ValueError(
            "未设置 CODEX_PROXY_URL 环境变量。\n"
            "示例：set CODEX_PROXY_URL=http://10.10.17.52:8080/v1"
        )
    if not api_key:
        raise ValueError(
            "未设置 CODEX_PROXY_API_KEY 环境变量。\n"
            "示例：set CODEX_PROXY_API_KEY=codex-proxy-xxx"
        )

    return base_url.rstrip("/"), api_key


# 图片生成使用的模型，可通过环境变量覆盖
DEFAULT_MODEL = "gpt-6.1-sol"


def get_model():
    """从环境变量读取模型名，未设置时使用默认模型。"""
    return os.environ.get("CODEX_PROXY_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def generate_image(
    prompt: str,
    size: str = "1024x1024",
    output_path: str = "output.png",
    reference_image_paths: list[str] | None = None,
):
    base_url, api_key = get_proxy_config()
    url = f"{base_url}/responses"

    content = prompt
    if reference_image_paths is not None and not isinstance(reference_image_paths, list):
        raise ValueError("reference_image_paths 必须是本地图片路径列表")
    if reference_image_paths:
        content = [{"type": "input_text", "text": prompt}]
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        for image_path in reference_image_paths:
            if not isinstance(image_path, str) or not image_path.strip():
                raise ValueError("参考图路径必须是非空字符串")
            path = Path(image_path).expanduser()
            mime_type = mime_types.get(path.suffix.lower())
            if mime_type is None:
                raise ValueError(f"不支持的参考图格式: {path}，请使用 PNG、JPEG、WebP 或非动画 GIF")
            image_bytes = path.read_bytes()
            if not image_bytes:
                raise ValueError(f"参考图文件为空: {path}")
            encoded_image = base64.b64encode(image_bytes).decode("ascii")
            content.append({
                "type": "input_image",
                "image_url": f"data:{mime_type};base64,{encoded_image}",
            })

    payload = {
        "model": get_model(),
        "stream": True,
        "input": [{"role": "user", "content": content}],
        "tools": [{"type": "image_generation", "size": size}],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    image_b64 = None
    revised_prompt = None

    with httpx.stream("POST", url, json=payload, headers=headers, timeout=300) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue

            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break

            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            if data.get("type") == "response.output_item.done":
                item = data.get("item", {})
                if item.get("type") == "image_generation_call":
                    image_b64 = item.get("result")
                    revised_prompt = item.get("revised_prompt")

    if not image_b64:
        raise RuntimeError("未从 codex-proxy 响应中获取到图片数据")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image_bytes = base64.b64decode(image_b64)
    with open(output_path, "wb") as f:
        f.write(image_bytes)

    return str(output_path.resolve()), revised_prompt or ""


def build_mcp_config():
    """生成需要写入 Codex 配置的 MCP 服务段落。"""
    script_path = Path(sys.argv[0]).resolve()
    is_script_invocation = script_path.suffix.lower() in (".py", ".pyw")

    if is_script_invocation:
        command = "python"
        args_line = f"args = ['{script_path}']"
    else:
        command = "codex-image-generator"
        args_line = ""

    config = f"""[{TOOL_SECTION}]
type = "stdio"
command = '{command}'
"""
    if args_line:
        config += args_line + "\n"
    config += "startup_timeout_sec = 120\n"
    return config


def write_codex_config():
    """把 MCP 服务配置写入 Codex 配置文件。"""
    config_text = build_mcp_config()

    CODEX_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not CODEX_CONFIG_PATH.exists():
        CODEX_CONFIG_PATH.write_text(config_text, encoding="utf-8")
        print(f"已创建配置: {CODEX_CONFIG_PATH}")
        print(config_text)
        return

    existing = CODEX_CONFIG_PATH.read_text(encoding="utf-8")

    if f"[{TOOL_SECTION}]" in existing:
        print(f"配置已存在，无需写入: {CODEX_CONFIG_PATH}")
        print("当前配置：")
        print(config_text)
        return

    with open(CODEX_CONFIG_PATH, "a", encoding="utf-8") as f:
        f.write("\n" + config_text + "\n")

    print(f"已追加配置到: {CODEX_CONFIG_PATH}")
    print(config_text)


# ===================== MCP 服务部分 =====================

app = Server("codex-image-generator")


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="generate_image",
            description="通过 codex-proxy 生成图片并保存到本地文件，可传入本地图片作为参考",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "图片生成提示词",
                    },
                    "size": {
                        "type": "string",
                        "description": "图片尺寸，例如 1024x1024、1024x1536、2048x2048、3840x2160",
                        "default": "1024x1024",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "输出图片路径，默认 output.png",
                        "default": "output.png",
                    },
                    "reference_image_paths": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "description": "可选的本地参考图路径列表，建议使用绝对路径；支持 PNG、JPEG、WebP 和非动画 GIF。图片必须在 MCP 服务所在机器上可读取",
                    },
                },
                "required": ["prompt"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name != "generate_image":
        raise ValueError(f"未知工具: {name}")

    prompt = arguments["prompt"]
    size = arguments.get("size", "1024x1024")
    output_path = arguments.get("output_path", "output.png")
    reference_image_paths = arguments.get("reference_image_paths")

    saved_path, revised_prompt = generate_image(
        prompt, size, output_path, reference_image_paths=reference_image_paths
    )

    return [
        TextContent(
            type="text",
            text=f"图片已生成并保存到: {saved_path}\n改写后提示词: {revised_prompt}",
        )
    ]


async def run_mcp_server():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    parser = argparse.ArgumentParser(description="Codex 图片生成 MCP 工具")
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="打印需要写入 Codex 配置的 MCP 段落",
    )
    parser.add_argument(
        "--write-config",
        action="store_true",
        help="自动把 MCP 配置写入 ~/.codex/config.toml",
    )
    args = parser.parse_args()

    if args.print_config:
        print(build_mcp_config())
        return

    if args.write_config:
        write_codex_config()
        return

    import asyncio

    asyncio.run(run_mcp_server())


if __name__ == "__main__":
    main()
