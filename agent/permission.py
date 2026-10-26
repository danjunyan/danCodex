from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 工作目录内直接允许。
ALLOW = {"readFile", "glob", "grep", "get_current_time", "convert_time"}
# 工作目录内要用户确认。
CONFIRM = {"writeFile", "editFile"}
# 无论路径在哪，都要用户确认。
CONFIRM_ALWAYS = {"bash"}


def _target(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate.resolve()


def _inside(path: Path) -> bool:
    try:
        path.relative_to(ROOT)
    except ValueError:
        return False
    return True


def _detail(name: str, arguments: dict) -> tuple[Path | None, str]:
    if name not in {"readFile", "writeFile", "editFile", "glob", "grep"}:
        text = arguments.get("command", arguments.get("timezone", ""))
        return None, str(text)
    raw = "." if name in {"glob", "grep"} and "path" not in arguments else arguments.get("path", "")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("缺少 path")
    path = _target(raw)
    return path, str(path)


def _ask(name: str, detail: str) -> str:
    answer = input(f"允许 {name}？{detail} [y/N] ").strip().lower()
    if answer == "y":
        return "allow"
    return f"用户拒绝了 {name}：{detail}"


def permission(name: str, arguments: dict) -> str:
    """返回 "allow"，或一段拒绝说明。调用方只在 "allow" 时执行工具。"""
    known = ALLOW | CONFIRM | CONFIRM_ALWAYS
    if name not in known:
        return f"未知工具：{name}"

    try:
        path, detail = _detail(name, arguments)
    except ValueError as exc:
        return f"参数错误：{exc}"

    outside = path is not None and not _inside(path)
    if name in ALLOW and not outside:
        return "allow"
    if name in CONFIRM and outside:
        return f"拒绝 {name}：路径超出工作目录 {detail}"
    if name in ALLOW and outside:
        return _ask(name, f"路径在工作目录外 {detail}")
    return _ask(name, detail)
