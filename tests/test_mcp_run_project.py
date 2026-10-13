#!/usr/bin/env python3
"""在临时项目中检查真实 MCP 启动、错误返回及编辑器日志；需要图形环境和空闲的 9080 端口。"""

import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import dev


def verify(project):
    session = ""
    request_id = 0

    def call(name, arguments, expected_error=""):
        nonlocal session, request_id
        request_id += 1
        result, session = dev.mcp_request("tools/call", {
            "name": name, "arguments": arguments,
        }, request_id, session)
        if expected_error:
            assert result.get("isError") and expected_error in json.dumps(result), result
            return
        assert not result.get("isError"), result
        value = result.get("structuredContent")
        if value is None:
            value = json.loads(next(item["text"] for item in result["content"] if item["type"] == "text"))
        assert not value.get("error"), value
        return value

    deadline = time.monotonic() + 30
    while True:
        try:
            _, session = dev.mcp_request("initialize", {
                "protocolVersion": "2025-03-26", "capabilities": {},
                "clientInfo": {"name": "run-project-regression", "version": "1"},
            }, 0)
            break
        except urllib.error.URLError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.2)
    dev.mcp_request("notifications/initialized", {}, None, session)

    info = call("get_project_info", {})
    assert Path(info["project_path"]).resolve() == project.resolve(), info
    try:
        main_scene = info["main_scene"]
        assert not call("get_editor_state", {})["active_scene"], "主场景回退检查需要空编辑器"
        call("run_project", {"scene_path": "res://missing_scene.tscn", "allow_window": True},
             expected_error="Scene file not found")
        assert call("get_editor_state", {})["editor_mode"] == "editor"

        cases = [
            ("未打开场景时运行主场景", {}, main_scene, "/root/Main"),
            ("运行当前场景", {}, main_scene, "/root/Main"),
            ("运行指定角色场景", {"scene_path": "res://game/characters/player/player.tscn"},
             "res://game/characters/player/player.tscn", "/root/Player"),
        ]
        for index, (label, arguments, scene, runtime_root) in enumerate(cases):
            if index == 1:
                call("open_scene", {"scene_path": main_scene, "allow_ui_focus": True})
            result = call("run_project", {**arguments, "allow_window": True})
            assert result["status"] == "success" and result["scene"] == scene, result
            assert result["session_active"], result
            call("run_project", {"allow_window": True}, expected_error="Project is already running")
            if index > 0:
                assert result["probe_ready"], result
                capture_path = ".godot/mcp-run-project-%d.png" % index
                shot = call("get_runtime_screenshot", {
                    "save_path": "res://" + capture_path, "format": "png", "timeout_ms": 5000,
                })
                assert shot.get("width", 0) > 0 and shot.get("height", 0) > 0, shot
                assert not shot.get("stale"), shot
                assert shot["current_scene"] == runtime_root, shot
                if index == 1:
                    preview = ROOT / ".godot/mcp-run-project-preview.png"
                    preview.parent.mkdir(exist_ok=True)
                    shutil.copyfile(project / capture_path, preview)
            result = call("stop_project", {"allow_window": True})
            assert result["status"] == "success" and result["mode"] == "editor", result
            # stop_project 返回时子进程的调试连接仍可能正在关闭。
            time.sleep(0.5)
            print(label + "：启动、重复启动拒绝与停止通过" + ("，运行探针与截图通过" if index > 0 else ""), flush=True)
    finally:
        call("execute_editor_script", {"code": "get_tree().quit.call_deferred()"})


def main():
    binary = dev.godot_binary()
    with tempfile.TemporaryDirectory(prefix="godot-mcp-run-test-") as temp:
        project = Path(temp) / "project"
        shutil.copytree(ROOT, project, ignore=shutil.ignore_patterns(".git", ".godot", "__pycache__"))
        # 独立的项目名隔离插件的 user:// 设置，避免改变开发项目的面板配置。
        config = project / "project.godot"
        config.write_text(re.sub(r'^config/name=.*$', 'config/name="%s"' % Path(temp).name,
                                 config.read_text(), count=1, flags=re.MULTILINE))
        dev.ROOT = project
        dev.checked_run(binary, ["--headless", "--editor", "--import"], 120)
        with socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("127.0.0.1", 9080))
            port = 9080
        dev.MCP_URL = "http://127.0.0.1:%d/mcp" % port
        log_path = Path(temp) / "editor.log"
        with log_path.open("w") as log:
            editor = subprocess.Popen([
                binary, "--path", str(project), "--editor", "--", "--mcp-server", "--mcp-port=" + str(port),
            ], stdout=log, stderr=subprocess.STDOUT)
            try:
                verify(project)
                assert editor.wait(timeout=15) == 0
            finally:
                if editor.poll() is None:
                    editor.terminate()
                    editor.wait(timeout=15)
                log.flush()
                output = log_path.read_text()
                if re.search(r"^(SCRIPT ERROR:|ERROR:)", output, re.MULTILINE):
                    print(output)
                    raise AssertionError("编辑器出现引擎错误，MCP 回归检查失败")
        assert "MCPRuntimeProbe" not in (project / "project.godot").read_text()
        print("MCP 启动回归检查通过；编辑器退出无引擎错误，运行探针已移除。")


if __name__ == "__main__":
    main()
