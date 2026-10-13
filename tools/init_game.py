"""从当前模板生成空白游戏，保留项目的 Codex 开发环境。"""

import json
from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = Path(__file__).parent / "templates/new_game"


def init_game(name, output):
    name = name.strip()
    if not name or any(ord(character) < 32 for character in name):
        raise ValueError("项目名不能为空，也不能包含换行等控制字符。")
    output = output.resolve()
    if output.is_relative_to(ROOT):
        raise ValueError("输出目录必须位于当前模板目录之外。")
    if output.exists():
        raise FileExistsError("输出目录已存在：" + str(output))

    quoted_name = json.dumps(name, ensure_ascii=False)
    config = (ROOT / "project.godot").read_text(encoding="utf-8")
    for key, value in [("config/name", quoted_name),
                       ("config/description", '"以 Codex 为主开发的 Godot 2D 游戏"'),
                       ("run/main_scene", '"res://game/main/main.tscn"')]:
        config, count = re.subn(r"^" + re.escape(key) + r"=.*$", lambda _: key + "=" + value,
                               config, count=1, flags=re.MULTILINE)
        if count != 1:
            raise ValueError("project.godot 缺少配置：" + key)
    # 输入映射和碰撞层属于收集示例；探针由新项目的编辑器重新注册。
    config = re.sub(r"(?ms)^\[(input|layer_names)\]\n.*?(?=^\[|\Z)", "", config)
    config = re.sub(r"^MCPRuntimeProbe=.*\n", "", config, flags=re.MULTILINE)
    config = re.sub(r"(?m)^\[autoload\]\n\s*(?=\[|\Z)", "", config)

    def ignore(directory, names):
        ignored = set(shutil.ignore_patterns(".git", ".godot", "__pycache__", "*.pyc", ".DS_Store")(directory, names))
        if Path(directory) == ROOT:
            ignored.update({"build", "builds", "exports"})
        return ignored

    shutil.copytree(ROOT, output, ignore=ignore)
    (output / "project.godot").write_text(config, encoding="utf-8")
    for folder, stem in [("game/characters/player", "player"), ("game/objects/pickup", "pickup")]:
        for suffix in [".gd", ".gd.uid", ".tscn"]:
            (output / folder / (stem + suffix)).unlink(missing_ok=True)
        for directory in [output / folder, (output / folder).parent]:
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()

    files = {"game/main/main.tscn": "main.tscn", "game/main/main.gd": "main.gd",
             "tests/test_game.gd": "test_game.gd", "README.md": "README.md",
             "docs/design.md": "design.md", "docs/art_direction.md": "art_direction.md"}
    for target, template in files.items():
        text = (TEMPLATES / template).read_text(encoding="utf-8")
        text = text.replace("{{GODOT_NAME}}", quoted_name) if template.endswith(".tscn") else text.replace("{{GAME_NAME}}", name)
        path = output / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    for file, introduction in [
        ("docs/README.md", "这里保存当前游戏的设计资料和开发依赖说明。先确定一个可玩的核心循环，再实现和验证。"),
        ("assets/credits.md", "当前游戏从标题占位场景开始。第三方开发工具的来源与许可证见 [依赖说明](../docs/dependencies.md)。"),
    ]:
        path = output / file
        heading, _, body = path.read_text(encoding="utf-8").split("\n\n", 2)
        path.write_text(heading + "\n\n" + introduction + "\n\n" + body, encoding="utf-8")
    agents = output / "AGENTS.md"
    text = re.sub(r"^- 主场景是 .*", "- 主场景是 `game/main/main.tscn`。当前为标题占位场景；先更新 `docs/design.md`，再实现新游戏的核心循环。",
                  agents.read_text(encoding="utf-8"), flags=re.MULTILINE)
    agents.write_text(text, encoding="utf-8")
    print("新游戏已创建：", output)
    print("项目名：", name)
    print("接下来在新目录中运行 python3 tools/dev.py check 和 python3 tools/dev.py editor。")
