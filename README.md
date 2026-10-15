# Codex Image Generator

通过 codex-proxy 提供图片生成能力的 MCP 服务。

## 安装

```bash
pipx install codex-image-generator
```

## 发布

开发者发布新版本到 PyPI 的步骤，见 [RELEASE.md](./RELEASE.md)。

或者使用 uv：

```bash
uvx codex-image-generator
```

## 配置

设置环境变量：

```bash
# Windows
set CODEX_PROXY_URL=http://10.10.17.52:8080/v1
set CODEX_PROXY_API_KEY=codex-proxy-xxx

# Linux/macOS
export CODEX_PROXY_URL=http://10.10.17.52:8080/v1
export CODEX_PROXY_API_KEY=codex-proxy-xxx

# 可选：指定图片生成模型，默认 gpt-6.1-sol
export CODEX_PROXY_MODEL=gpt-6.1-sol
```

然后写入 Codex 配置：

```bash
codex-image-generator --write-config
```

这会向 `~/.codex/config.toml` 追加 MCP 服务配置。

## 手动配置

如果 `--write-config` 不适用，可以手动在 `~/.codex/config.toml` 中添加：

```toml
[mcp_servers.image_generator]
type = "stdio"
command = 'codex-image-generator'
startup_timeout_sec = 120
```

## 使用

重启 Codex 后，在对话中让 Codex 生成图片即可，例如：

> 生成一张白色背景上的红色圆形图片

## 前提条件

- codex-proxy 已部署并可通过 `CODEX_PROXY_URL` 访问
- 连接的 OpenAI 账号为 ChatGPT Plus 及以上（free 账号不支持图片生成）

## 支持参数

工具 `generate_image` 支持以下参数：

- `prompt`（必填）：图片生成提示词
- `size`（可选）：图片尺寸，默认 `1024x1024`
- `output_path`（可选）：输出路径，默认 `output.png`
