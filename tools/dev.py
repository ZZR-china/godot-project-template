#!/usr/bin/env python3
"""本项目的 Godot 开发入口，仅使用 Python 标准库。"""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
MCP_URL = "http://127.0.0.1:9080/mcp"


def godot_binary():
    # GODOT_BIN 优先；未设置时查找 PATH，再尝试 macOS 的标准安装位置。
    configured = os.environ.get("GODOT_BIN")
    if configured:
        binary = shutil.which(configured) or configured
        if not Path(binary).is_file():
            raise FileNotFoundError("GODOT_BIN 指向的文件不存在：" + configured)
        return binary
    binary = shutil.which("godot")
    if binary:
        return binary
    mac_app = Path("/Applications/Godot.app/Contents/MacOS/Godot")
    if mac_app.is_file():
        return str(mac_app)
    raise FileNotFoundError("未找到 Godot 4.7，请将 godot 加入 PATH 或设置 GODOT_BIN。")


def checked_run(binary, arguments, timeout):
    with tempfile.TemporaryDirectory(prefix="codex-godot-") as temp:
        command = [binary, "--path", str(ROOT), "--log-file", str(Path(temp) / "godot.log")]
        result = subprocess.run(command + arguments, cwd=ROOT, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    print(result.stdout, end="")
    # Godot 的脚本错误可能仍返回 0，因此也检查引擎错误输出。
    if result.returncode or re.search(r"^(SCRIPT ERROR:|ERROR:)", result.stdout, re.MULTILINE):
        raise RuntimeError("Godot 检查失败，请先修复上方的第一条错误。")


def mcp_request(method, params, request_id, session=""):
    message = {"jsonrpc": "2.0", "method": method, "params": params}
    if request_id is not None:
        message["id"] = request_id
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    request = urllib.request.Request(MCP_URL, json.dumps(message).encode(), headers)
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = response.read().decode()
        session = response.headers.get("Mcp-Session-Id", session)
    if not payload:
        return {}, session
    if payload.startswith("event:") or payload.startswith("data:"):
        payload = next(line[5:].strip() for line in payload.splitlines() if line.startswith("data:"))
    result = json.loads(payload)
    if "error" in result:
        raise RuntimeError(result["error"])
    return result.get("result", {}), session


def check_mcp():
    _, session = mcp_request("initialize", {
        "protocolVersion": "2025-03-26", "capabilities": {},
        "clientInfo": {"name": "codex-2d-starter", "version": "1.0"},
    }, 1)
    mcp_request("notifications/initialized", {}, None, session)
    result, _ = mcp_request("tools/call", {"name": "get_project_info", "arguments": {}}, 2, session)
    if result.get("isError"):
        raise RuntimeError(result)
    info = result.get("structuredContent")
    if info is None:
        info = json.loads(next(item["text"] for item in result["content"] if item["type"] == "text"))
    if Path(info["project_path"]).resolve() != ROOT:
        raise RuntimeError("MCP 连接到了其他项目：" + info["project_path"])
    print(json.dumps(info, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["editor", "run", "check", "capture", "mcp"])
    parser.add_argument("--output", type=Path, default=ROOT / ".godot/preview.png",
                        help="截图路径，默认 .godot/preview.png")
    args = parser.parse_args()
    if args.command == "mcp":
        check_mcp()
        return
    binary = godot_binary()
    if args.command == "check":
        checked_run(binary, ["--headless", "--editor", "--import"], 120)
        checked_run(binary, ["--headless", "--script", "res://tests/test_game.gd"], 30)
    elif args.command == "capture":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        checked_run(binary, ["--script", "res://tools/capture.gd", "--", str(args.output.resolve())], 30)
        print("截图已保存：", args.output.resolve())
    else:
        arguments = ["--editor", "--", "--mcp-server", "--mcp-port", "9080"] if args.command == "editor" else []
        subprocess.run([binary, "--path", str(ROOT)] + arguments, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
