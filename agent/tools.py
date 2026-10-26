import subprocess
from pathlib import Path

TOOLS = [
    {
        "name": "readFile",
        "description": "打开文本文件并返回带行号的内容。文件很长时用 offset 和 limit 分段读取。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "offset": {"type": "integer", "description": "起始行，从 1 开始，默认 1"},
                "limit": {"type": "integer", "description": "最多读取的行数，默认 200"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "writeFile",
        "description": "新建或覆盖整个文本文件。只在需要整篇重写时使用；修改局部内容用 editFile。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "文件的完整新内容"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "editFile",
        "description": "把文件中唯一的一段原文替换成新文本。old_text 必须与文件内容完全一致，且只出现一次。",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "old_text": {"type": "string", "description": "要替换的原文，必须唯一"},
                "new_text": {"type": "string", "description": "替换后的文本"},
            },
            "required": ["path", "old_text", "new_text"],
        },
    },
    {
        "name": "bash",
        "description": "在当前系统的 shell 中执行一条命令，返回退出码、标准输出和标准错误。",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的命令"},
                "timeout": {"type": "integer", "description": "超时秒数，默认 30"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "glob",
        "description": "按文件名模式查找文件，例如 **/*.py。返回匹配到的路径。",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "glob 模式"},
                "path": {"type": "string", "description": "搜索起点，默认当前目录"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "grep",
        "description": "在文件或目录中查询文本，返回路径、行号和匹配行。",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "要查询的文本；regex 为 true 时按正则表达式"},
                "path": {"type": "string", "description": "文件或目录路径，默认当前目录"},
                "glob": {"type": "string", "description": "只搜索匹配该模式的文件，例如 *.py"},
                "regex": {"type": "boolean", "description": "为 true 时把 pattern 当作正则，默认 false"},
            },
            "required": ["pattern"],
        },
    },
]


def _resolve(path: str) -> Path:
    return Path(path).expanduser().resolve()


def readFile(path: str, offset: int = 1, limit: int = 200) -> str:
    file = _resolve(path)
    if not file.is_file():
        return f"找不到文件：{path}"
    lines = file.read_text(encoding="utf-8").splitlines()
    start = max(offset, 1)
    chosen = lines[start - 1 : start - 1 + limit]
    if not chosen:
        return f"{path} 在第 {start} 行之后没有内容"
    body = "\n".join(f"{start + index}|{line}" for index, line in enumerate(chosen))
    return f"{path} 共 {len(lines)} 行，显示 {start}-{start + len(chosen) - 1} 行\n{body}"


def writeFile(path: str, content: str) -> str:
    file = _resolve(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")
    return f"已写入 {path}，共 {len(content.splitlines())} 行"


def editFile(path: str, old_text: str, new_text: str) -> str:
    if old_text == "":
        return "old_text 不能为空"
    file = _resolve(path)
    if not file.is_file():
        return f"找不到文件：{path}"
    original = file.read_text(encoding="utf-8")
    count = original.count(old_text)
    if count == 0:
        return "old_text 在文件中不存在"
    if count > 1:
        return f"old_text 出现了 {count} 次，需要提供更长的唯一片段"
    file.write_text(original.replace(old_text, new_text, 1), encoding="utf-8")
    return f"已编辑 {path}"


def bash(command: str, timeout: int = 30) -> str:
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"命令超时（{timeout} 秒）：{command}"
    return (
        f"exit_code: {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )


def glob(pattern: str, path: str = ".") -> str:
    root = _resolve(path)
    if not root.exists():
        return f"找不到路径：{path}"
    matches = sorted(item for item in root.glob(pattern) if item.is_file())
    if not matches:
        return "没有匹配的文件"
    shown = matches[:100]
    lines = [str(item.relative_to(root)) for item in shown]
    suffix = f"\n还有 {len(matches) - len(shown)} 个未显示" if len(matches) > len(shown) else ""
    return f"共 {len(matches)} 个文件\n" + "\n".join(lines) + suffix


def grep(pattern: str, path: str = ".", glob: str | None = None, regex: bool = False) -> str:
    import re

    root = _resolve(path)
    if not root.exists():
        return f"找不到路径：{path}"
    files = [root] if root.is_file() else sorted(item for item in root.glob(glob or "**/*") if item.is_file())
    matcher = re.compile(pattern) if regex else None
    hits: list[str] = []
    for file in files:
        try:
            lines = file.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for number, line in enumerate(lines, start=1):
            matched = matcher.search(line) if matcher else pattern in line
            if matched:
                location = file if root.is_file() else file.relative_to(root)
                hits.append(f"{location}:{number}:{line}")
                if len(hits) >= 50:
                    return "\n".join(hits) + "\n结果已截断为 50 条"
    return "\n".join(hits) if hits else "没有匹配"


HANDLERS = {
    "readFile": readFile,
    "writeFile": writeFile,
    "editFile": editFile,
    "bash": bash,
    "glob": glob,
    "grep": grep,
}


def run_tool(name: str, arguments: dict) -> str:
    handler = HANDLERS.get(name)
    if handler is None:
        return f"未知工具：{name}"
    try:
        return handler(**arguments)
    except TypeError as exc:
        return f"参数错误：{exc}"
    except OSError as exc:
        return f"执行失败：{exc}"
