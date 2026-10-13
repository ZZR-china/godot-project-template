#!/usr/bin/env python3
"""在临时项目和独立端口上检查开发工具与真实 MCP 的完整配合；需要图形环境。"""

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
    # MCP 在插件初始化时已可连接，稍后编辑器才完成场景标签恢复。
    time.sleep(1)

    info = call("get_project_info", {})
    assert Path(info["project_path"]).resolve() == project.resolve(), info
    try:
        diagnostic = subprocess.run([sys.executable, str(project / "tools/dev.py"), "mcp"],
                                    capture_output=True, text=True, timeout=20)
        assert diagnostic.returncode == 0, diagnostic.stdout + diagnostic.stderr
        assert Path(json.loads(diagnostic.stdout)["project_path"]).resolve() == project.resolve()
        version = subprocess.check_output([dev.godot_binary(), "--version"], text=True).strip()
        assert info["godot_version"].startswith(".".join(version.split(".")[:3])), info
        tools, session = dev.mcp_request("tools/list", {}, 100, session)
        names = {tool["name"] for tool in tools["tools"]}
        assert {"read_script", "modify_script", "run_project", "inspect_runtime_node",
                "get_runtime_screenshot", "simulate_runtime_input_event"} <= names, names
        api = call("get_class_api_metadata", {"class_name": "CharacterBody2D", "filter": "move_and_slide"})
        assert any(method["name"] == "move_and_slide" for method in api["methods"]), api
        main_scene = info["main_scene"]
        state = call("get_editor_state", {})
        if state["active_scene"]:
            closed = call("execute_editor_script", {"code": "_custom_print(error_string(EditorInterface.close_scene()))"})
            assert closed["output"] == ["OK"], closed
        state = call("get_editor_state", {})
        assert not state["active_scene"], state
        config_before = (project / "project.godot").read_bytes()
        assert b"MCPRuntimeProbe" in config_before
        check = subprocess.run([sys.executable, str(project / "tools/dev.py"), "check"],
                               capture_output=True, text=True, timeout=150)
        assert check.returncode == 0, check.stdout + check.stderr
        assert b"MCPRuntimeProbe" in (project / "project.godot").read_bytes(), check.stdout + check.stderr
        print("编辑器在线时运行 check：9 项行为检查通过，探针配置保留", flush=True)

        script_path = "res://game/characters/player/player.gd"
        script = call("read_script", {"script_path": script_path})["content"]
        changed_script = script.replace("240.0", "260.0")
        assert changed_script != script
        call("modify_script", {"script_path": script_path, "content": changed_script})
        assert call("read_script", {"script_path": script_path})["content"] == changed_script
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
                node = call("create_node", {"parent_path": "/root/Main", "node_type": "Marker2D",
                                             "node_name": "AuditMarker"})
                assert node["status"] == "success", node
                call("save_scene", {})
                assert 'name="AuditMarker"' in (project / "game/main/main.tscn").read_text()
            result = call("run_project", {**arguments, "allow_window": True})
            assert result["status"] == "success" and result["scene"] == scene, result
            assert result["session_active"] and result["probe_ready"], result
            call("run_project", {"allow_window": True}, expected_error="Project is already running")
            player_path = runtime_root + "/Player" if index < 2 else runtime_root
            player = call("inspect_runtime_node", {"node_path": player_path, "timeout_ms": 5000})
            assert player["properties"]["speed"] == 260.0, player
            if index == 0:
                event = {"type": "key", "keycode": 68, "physical_keycode": 68, "pressed": True}
                call("simulate_runtime_input_event", {"event": event})
                moved = call("await_runtime_condition", {
                    "expression": 'get_node("/root/Main/Player").position.x > 220.0', "timeout_ms": 5000,
                })
                call("simulate_runtime_input_event", {"event": {**event, "pressed": False}})
                assert moved["condition_met"], moved
                call("await_runtime_condition", {"expression": "false", "timeout_ms": 200,
                                                   "poll_interval_ms": 50},
                     expected_error="Timeout waiting for runtime condition")
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
            print(label + "：新探针、脚本参数、截图、重复启动拒绝与停止通过", flush=True)
        call("modify_script", {"script_path": script_path, "content": script})
        created = call("create_scene", {"scene_path": "res://game/main/audit_scene.tscn", "root_node_type": "Node2D"})
        assert created["status"] == "success", created
        assert (project / "game/main/audit_scene.tscn").is_file()
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
        # 首次截图同时验证无缓存导入，不预先运行 check 或打开编辑器。
        fresh_capture = subprocess.run([sys.executable, str(project / "tools/dev.py"), "capture",
                                        "--output", str(Path(temp) / "first-preview.png")],
                                       capture_output=True, text=True, timeout=150)
        assert fresh_capture.returncode == 0, fresh_capture.stdout + fresh_capture.stderr
        assert (Path(temp) / "first-preview.png").is_file()
        print("无缓存副本直接截图通过", flush=True)
        settings_script = Path(temp) / "settings.gd"
        settings_script.write_text('extends SceneTree\nfunc _initialize() -> void:\n'
                                   '\tvar manager = load("res://addons/godot_mcp/native_mcp/settings_manager.gd").new()\n'
                                   '\tvar settings: Dictionary = manager.load_settings()\n'
                                   '\tsettings["transport_mode"] = "stdio"\n'
                                   '\tsettings["http_port"] = 9080\n'
                                   '\tassert(manager.save_settings(settings))\n\tquit()\n')
        dev.checked_run(binary, ["--headless", "--script", str(settings_script)], 30)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        prior_url = dev.MCP_URL
        dev.MCP_URL = "http://127.0.0.1:%d/mcp" % port
        for path in [project / "tools/dev.py", project / ".codex/config.toml"]:
            path.write_text(path.read_text().replace(prior_url, dev.MCP_URL))
        log_path = Path(temp) / "editor.log"
        with log_path.open("w") as log:
            editor = subprocess.Popen([binary, "--path", str(project)] + dev.editor_arguments(),
                                      stdout=log, stderr=subprocess.STDOUT)
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
