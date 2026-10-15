# Codex Image Generator

通过 codex-proxy 提供图片生成能力的 MCP 服务。

## 给 AI 助手的说明

如果用户把这个仓库地址给你，请按以下步骤自动完成安装和配置：

1. **安装工具**（二选一）：

```bash
# 方式 A：uvx 免安装直接运行（推荐，需要 uv）
uvx --from git+https://github.com/nameLogen/codex-image-generator.git codex-image-generator --print-config

# 方式 B：pipx 安装到独立环境
pipx install git+https://github.com/nameLogen/codex-image-generator.git
```

2. **确认环境变量**，向用户询问并协助设置：

```bash
# 必填
CODEX_PROXY_URL=http://<codex-proxy地址>:8080/v1
CODEX_PROXY_API_KEY=<proxy的apikey>

# 可选，默认 gpt-6.1-sol
CODEX_PROXY_MODEL=gpt-6.1-sol
```

3. **写入 Codex MCP 配置**：

```bash
codex-image-generator --write-config
```

如果用户没有安装命令（方式 A 场景），直接在 `~/.codex/config.toml` 追加：

```toml
[mcp_servers.image_generator]
type = "stdio"
command = 'uvx'
args = ['--from', 'git+https://github.com/nameLogen/codex-image-generator.git', 'codex-image-generator']
startup_timeout_sec = 120
```

4. **提醒用户重启 Codex**，之后在对话中说「生成一张 xxx 图片」即可使用。

## 升级

```bash
# pipx 安装的升级方式
pipx upgrade codex-image-generator

# 或者强制重装最新代码
pipx install --force git+https://github.com/nameLogen/codex-image-generator.git
```

uvx 方式每次都拉取最新代码，无需手动升级。

## 手动安装

```bash
git clone https://github.com/nameLogen/codex-image-generator.git
cd codex-image-generator
python -m pip install -e .
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

## 发布

开发者发布新版本到 PyPI 的步骤，见 [RELEASE.md](./RELEASE.md)。
