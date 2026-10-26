import json
import os
from pathlib import Path
import urllib.request
from tools import TOOLS
from mcp_client import run_tool, start
from system_prompt import SYSTEM
from permission import permission
import msvcrt
import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
API_KEY = os.environ.get("MODELSCOPE_API_KEY")
if not API_KEY:
    raise RuntimeError("请在项目根目录的 .env 中设置 MODELSCOPE_API_KEY")
# 官方客户端会在这个地址后面拼接 /v1/messages。
BASE_URL = "https://api-inference.modelscope.cn"
MODEL = "Qwen/Qwen3.5-27B"

client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)

# 检测是否按下ESC键
def esc_pressed() -> bool:
    pressed = False
    while msvcrt.kbhit():
        if msvcrt.getch() == b"\x1b":
            pressed = True
    return pressed

def call_model(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    # 最多50轮对话
    for round in range(50):
        print("用户输入：",messages)
        if esc_pressed():
            return "用户取消了对话"
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            system=SYSTEM,
            messages=messages,
        )
        print("模型输出：",message)
        # 如果模型输出不是工具调用，则返回模型输出
        if message.stop_reason != "tool_use":
            return "".join(block.text for block in message.content if block.type == "text")
        messages.append({"role": "assistant", "content": message.content})
        content = []
        # 工具调用结果，可能有多次调用，需要合并
        for block in message.content:
             if block.type == "tool_use":
                # 权限检查
                decision = permission(block.name, block.input)
                if decision is not None and decision != "allow":
                    output = decision
                    is_error = True
                else:
                    output = run_tool(block.name, block.input)
                    is_error = False
                content.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": is_error
                })
        messages.append({"role": "user", "content": content})
    return "已达到 50 次上限"

if __name__ == "__main__":
    start()
    prompt = r"在当前目录下新建一个txt文件并写yy我爱你，并写出当前时间"
    print("最终回答:", call_model(prompt))
