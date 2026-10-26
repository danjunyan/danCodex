# danCodex

Windows 下运行的 Python 文件编辑 Agent，使用 Anthropic SDK 连接 ModelScope，并通过 MCP 获取时间。

## 环境安装

在 Anaconda Prompt 中切换到项目根目录。首次安装：

```powershell
conda env create -f environment.yml
conda activate dancodex
```

如果已有 `dancodex` 环境：

```powershell
conda activate dancodex
python -m pip install -r requirements-lock.txt
```

`requirements.txt` 记录直接依赖，`requirements-lock.txt` 固定已验证环境的依赖版本。项目使用 Python 3.13。

## 本地配置与运行

首次配置时复制 `.env.example` 为 `.env`，填写自己的 `MODELSCOPE_API_KEY`。若 `.env` 已存在，直接编辑，避免覆盖。

在项目根目录运行：

```powershell
conda activate dancodex
python agent/main.py
```

入口目前使用 `agent/main.py` 中的示例提示词，会调用模型和文件工具；写文件前会请求确认。运行需要有效的 ModelScope API Key 及网络连接。

PyCharm 解释器可选择 `D:\software\anaconda\envs\dancodex\python.exe`，工作目录设为项目根目录。

## Git

本地仓库使用 `main` 分支。`.env`、Python 缓存、虚拟环境和 IDE 配置已被忽略。

首次提交前配置自己的身份：

```powershell
git config user.name "你的名字"
git config user.email "你的邮箱"
git add .
git commit -m "Initial project setup"
```

在 GitHub / Gitee 等平台创建空仓库后，使用实际仓库地址：

```powershell
git remote add origin <仓库地址>
git push -u origin main
```

不要提交 `.env` 或在源码中写入 API Key。
