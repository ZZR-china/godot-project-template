# Codex 开发流程

本模板由三部分配合：项目技能提供 Godot 实现方法，MCP 读取和操作当前编辑器，`tools/dev.py` 负责导入、行为检查与独立截图。先阅读游戏设计，再按本次任务选择技能，完成一个可以运行和观察的改动。

## 选择技能

| 任务 | 项目技能 |
|---|---|
| GDScript、类型和生命周期 | [godot-gdscript](../.agents/skills/godot-gdscript/SKILL.md) |
| 场景组合、节点归属和资源实例化 | [godot-nodes-scenes](../.agents/skills/godot-nodes-scenes/SKILL.md) |
| 信号连接和节点组 | [godot-signals-groups](../.agents/skills/godot-signals-groups/SKILL.md) |
| 俯视角或横版角色移动 | [godot-2d-movement](../.agents/skills/godot-2d-movement/SKILL.md) |
| 碰撞体、Area、碰撞层和射线 | [godot-physics](../.agents/skills/godot-physics/SKILL.md) |
| HUD、菜单和布局 | [godot-ui-control](../.agents/skills/godot-ui-control/SKILL.md) |
| AnimationPlayer、AnimationTree 和 Tween | [godot-animation](../.agents/skills/godot-animation/SKILL.md) |
| 无界面行为测试 | [godot-gdscript-headless-testing](../.agents/skills/godot-gdscript-headless-testing/SKILL.md) |

技能示例里的通用路径需要替换为本仓库的 `game/` 和 `assets/` 路径，项目约定优先。上游提及的 `godot-tilemap`、`godot-resources`、`godot-shaders`、`godot-export`、`godot-csharp` 等专项未随模板安装；不要把相关技能名称当成本地已有文件，也不要为一次任务自动扩大依赖。

## 实现与验证

1. 运行 `python3 tools/dev.py editor`。MCP 连接后先调用 `get_project_info`，确认项目路径、实际引擎版本和主场景。工具未连接时用 `python3 tools/dev.py mcp` 诊断；Codex 没有显示 MCP 工具时按 README 重新加载连接。
2. 按任务读取技能，直接编辑项目文件或使用 MCP 编辑节点、场景与脚本。拿不准引擎 API 时用 `get_class_api_metadata` 查询当前引擎，例如类名 `CharacterBody2D`、过滤条件 `move_and_slide`。新增功能放进对应 `game/` 目录，新增运行时素材放进 `assets/`。
3. 使用 MCP 修改场景后调用 `save_scene`，并检查文件确实落盘。编辑器中的未保存改动不会被命令行检查覆盖到。代码修改后运行 `python3 tools/dev.py check`；该命令可以与当前编辑器配合使用，资源导入不启动 MCP 或注销编辑器的探针。
4. 使用 `run_project`，传入 `allow_window=true`，按需指定 `scene_path`。确认 `session_active` 和 `probe_ready` 后检查运行时节点、模拟输入并截图。截图应使用明确的 `save_path`；结果标记为 `stale` 时不能作为当前画面的验证依据。结束后调用 `stop_project`，再运行下一场景。
5. 无 MCP 时可用 `python3 tools/dev.py capture` 独立运行主场景并截图，或用 `python3 tools/dev.py run` 操作游戏。这两个命令会先导入项目，支持不含 `.godot/` 的新副本。报告分别说明行为检查、实际运行和画面检查的结果。

## 工具联调回归

修改开发入口、MCP 集成或更新插件后执行：

```bash
python3 tools/dev.py check
python3 tests/test_mcp_run_project.py
```

第二条命令需要图形环境。它使用临时项目、独立项目名和自动选择的本地端口，检查首次截图、编辑器在线时的行为测试、脚本读写、API 查询、场景与节点操作、三种启动方式、运行探针、截图、错误返回和连续停止／启动。测试不会连接开发项目的 9080 服务；主场景预览保存到 `.godot/mcp-run-project-preview.png`。

## Codex 配置依据

项目技能位于 `.agents/skills/`，受信任项目的 MCP 配置位于 `.codex/config.toml`，与官方说明一致：[技能发现](https://learn.chatgpt.com/docs/build-skills)、[MCP 配置](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)。这说明配置位置符合要求；实际连接与游戏行为仍由上述本地检查验证。
