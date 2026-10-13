#!/usr/bin/env python3
"""在临时目录验证新游戏初始化及保留的开发流程，需要 Godot 和图形环境。"""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def run(project, arguments, env=None, success=True, timeout=180):
    result = subprocess.run([sys.executable, str(project / "tools/dev.py")] + arguments,
                            capture_output=True, text=True, env=env, timeout=timeout)
    assert (result.returncode == 0) == success, result.stdout + result.stderr
    return result


def snapshot(directory):
    return {path.relative_to(directory): path.read_bytes() for path in directory.rglob("*") if path.is_file()}


def main():
    with tempfile.TemporaryDirectory(prefix="godot-init-test-") as temp:
        source = Path(temp) / "template"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", ".godot", "__pycache__"))
        for relative in ["game/characters/player/notes.txt", "assets/source/art.txt", "docs/narrative/story.md",
                         ".git/local", ".godot/cache", "build/output", "builds/output", "exports/output"]:
            path = source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("保留检查：" + relative, encoding="utf-8")
        before = snapshot(source)
        output = Path(temp) / "new game"
        name = '星海 "初航"'
        # 初始化只生成文件，即使没有可用的 Godot 也应成功。
        env = {**os.environ, "GODOT_BIN": str(Path(temp) / "missing-godot"), "PYTHONDONTWRITEBYTECODE": "1"}
        run(source, ["init", "--name", name, "--output", str(output)], env=env)
        assert snapshot(source) == before, "原模板文件被修改"
        for directory in [".agents", ".codex", "addons", "tools"]:
            assert snapshot(output / directory) == snapshot(source / directory), directory
        for relative in ["game/characters/player/notes.txt", "assets/source/art.txt", "docs/narrative/story.md"]:
            assert (output / relative).read_bytes() == (source / relative).read_bytes(), relative
        for directory in [".git", ".godot", "build", "builds", "exports"]:
            assert not (output / directory).exists(), directory
        for relative in ["game/characters/player/player.gd", "game/characters/player/player.gd.uid",
                         "game/characters/player/player.tscn", "game/objects/pickup/pickup.gd",
                         "game/objects/pickup/pickup.gd.uid", "game/objects/pickup/pickup.tscn"]:
            assert not (output / relative).exists(), relative
        assert "StarterGame" not in (output / "game/main/main.gd").read_text(encoding="utf-8")
        assert "StarterPickup" not in (output / "tests/test_game.gd").read_text(encoding="utf-8")
        assert "[input]" not in (output / "project.godot").read_text(encoding="utf-8")
        assert (output / "game/main/main.gd.uid").read_bytes() == (source / "game/main/main.gd.uid").read_bytes()
        print("中文与引号项目名、示例清理、工具和额外文件保留、原模板不变检查通过", flush=True)

        existing = snapshot(output)
        run(source, ["init", "--name", "覆盖检查", "--output", str(output)], env=env, success=False)
        assert snapshot(output) == existing, "已有输出目录被覆盖"
        for index, invalid_name in enumerate([" ", "游戏\n名称"]):
            destination = Path(temp) / ("invalid-%d" % index)
            run(source, ["init", "--name", invalid_name, "--output", str(destination)], env=env, success=False)
            assert not destination.exists()
        nested = source / "nested-game"
        run(source, ["init", "--name", "递归复制检查", "--output", str(nested)], env=env, success=False)
        assert not nested.exists()
        print("已有目录、无效名称与模板内部输出的失败路径通过", flush=True)

        check = run(output, ["check"])
        assert "标题与项目名一致" in check.stdout, check.stdout
        preview = Path(temp) / "new-game.png"
        run(output, ["capture", "--output", str(preview)])
        target = ROOT / ".godot/init-game-preview.png"
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(preview, target)
        print("初始化后的新游戏检查与实际运行截图通过", flush=True)
        result = subprocess.run([sys.executable, str(output / "tests/test_mcp_run_project.py")],
                                capture_output=True, text=True, timeout=240)
        assert result.returncode == 0, result.stdout + result.stderr
        print(result.stdout, end="")
        print("新游戏初始化回归检查通过。", flush=True)


if __name__ == "__main__":
    main()
