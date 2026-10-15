# 发布指南

这篇文档记录如何把 `codex-image-generator` 发布到 PyPI，方便下次不记得流程时查阅。

## 前置条件

1. 已有 PyPI 账号：https://pypi.org/
2. 已创建 API Token（不要用账号密码）
   - PyPI 右上角 → Account settings → API tokens → Add API token
   - Scope 可以选 Entire account 或指定项目
   - 复制 token（格式：`pypi-Ag...`）
3. 本地已安装 twine

```bash
python -m pip install --upgrade twine build
```

## 配置 PyPI Token

**不要把 token 写进代码或发给别人。**

在 PowerShell 里设置环境变量（只在当前窗口有效）：

```powershell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-你的Token"
```

或者在用户目录创建 `.pypirc` 文件（文件权限要控制好）：

```ini
[pypi]
username = __token__
password = pypi-你的Token
```

## 发布步骤

### 1. 更新版本号

打开 `pyproject.toml`，修改 `version`：

```toml
[project]
version = "0.1.1"
```

同时更新 `src/codex_image_generator/__init__.py` 里的 `__version__`。

### 2. 检查作者和项目信息

确认 `pyproject.toml` 里的 `authors`、`description`、`urls` 没问题。

### 3. 清理旧构建产物

```powershell
cd C:\Users\logen\codex-image-generator
Remove-Item -Recurse -Force dist, build
```

### 4. 重新打包

```powershell
python -m build
```

成功后会生成：

```text
dist/
├── codex_image_generator-0.1.1-py3-none-any.whl
└── codex_image_generator-0.1.1.tar.gz
```

### 5. 上传到 PyPI

```powershell
python -m twine upload dist\*
```

如果环境变量配置正确，会直接上传成功。

### 6. 验证

过几分钟后访问：

https://pypi.org/project/codex-image-generator/

确认新版本已经显示。

## 安装测试

上传成功后，用 pipx 安装测试：

```powershell
pipx install codex-image-generator
```

或者临时运行：

```powershell
uvx codex-image-generator --help
```

## 本地开发安装

开发时不想每次发布，可以本地可编辑安装：

```powershell
cd C:\Users\logen\codex-image-generator
python -m pip install -e .
```

这样改代码后不需要重新安装也能生效。
