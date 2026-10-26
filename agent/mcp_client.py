import asyncio
import sys
from threading import Event, Thread

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from tools import run_tool as run_local_tool
from tools import TOOLS

_mcp_names: set[str] = set()
_session: ClientSession | None = None
_loop: asyncio.AbstractEventLoop | None = None
_ready = Event()
_error: BaseException | None = None


def start() -> None:
    """启动 Time MCP，并把 get_current_time 追加进 TOOLS。"""
    Thread(target=lambda: asyncio.run(_serve()), daemon=True).start()
    _ready.wait()
    if _error is not None:
        raise _error


async def _serve() -> None:
    global _session, _loop, _error
    _loop = asyncio.get_running_loop()
    parameters = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server_time"])
    try:
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for tool in (await session.list_tools()).tools:
                    _mcp_names.add(tool.name)
                    TOOLS.append(
                        {
                            "name": tool.name,
                            "description": tool.description or "",
                            "input_schema": tool.input_schema,
                        }
                    )
                _session = session
                _ready.set()
                await asyncio.Event().wait()
    except BaseException as exc:
        _error = exc
        _ready.set()


def run_tool(name: str, arguments: dict) -> str:
    if name not in _mcp_names:
        return run_local_tool(name, arguments)
    if _session is None or _loop is None:
        return "Time MCP 尚未启动"
    result = asyncio.run_coroutine_threadsafe(
        _session.call_tool(name, arguments=dict(arguments)),
        _loop,
    ).result()
    return "".join(
        item.text for item in result.content if getattr(item, "type", None) == "text"
    )
