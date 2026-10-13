# {{GAME_NAME}}

Godot 4.7 / GDScript 的 2D 游戏项目，保留项目级 Codex 技能、Godot MCP 和 Python 开发入口。当前主场景只显示项目名，尚未实现玩法。

## 开始开发

需要 Godot 4.7.x 和 Python 3.9+。先更新 [游戏设计](docs/design.md)，确定最小可玩的核心循环，再从 `game/main/` 开始实现。

```bash
python3 tools/dev.py check
python3 tools/dev.py editor
```

编辑器启动后按 F5 运行主场景。也可以独立运行或截图：

```bash
python3 tools/dev.py run
python3 tools/dev.py capture
python3 tools/dev.py mcp
```

`mcp` 命令需要编辑器已启动。Godot 不在默认位置时设置 `GODOT_BIN`；MCP 端口默认 9080，更换时同步修改 `.codex/config.toml` 和 `tools/dev.py` 的 `MCP_URL`。

## 目录与验证

- `game/`：场景、脚本和玩法资源，按功能组织。主场景为 `game/main/main.tscn`，标题节点可直接在编辑器修改或删除。
- `assets/`：运行时素材；制作原稿放在 `assets/source/`，外部素材来源登记到 `assets/credits.md`。
- `docs/`：设计、剧情、视觉约定和依赖说明，从 [文档索引](docs/README.md) 开始。
- `.agents/skills/`、`.codex/`、`addons/godot_mcp/`：Codex 技能、MCP 配置和固定版本插件。
- `tools/`、`tests/`：开发入口与检查；`tests/test_game.gd` 当前检查主场景和项目名，增加玩法后同步更新。

工具配合见 [Codex 开发流程](docs/development.md)，开发约定见 [AGENTS.md](AGENTS.md)。修改开发工具或 MCP 后运行 `python3 tests/test_mcp_run_project.py`；检查使用临时项目和独立端口，需要图形环境。原模板和本项目的生成方式见 [新游戏初始化](docs/new_game.md)。
