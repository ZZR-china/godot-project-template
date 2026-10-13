# 新游戏初始化

在模板根目录执行：

```bash
python3 tools/dev.py init --name "星海冒险" --output ../star-adventure
```

命令只需要 Python 3.9+，会在新的输出目录创建项目。输出目录必须位于当前模板之外且尚不存在；项目名必填，不能是空白或包含换行等控制字符。支持中文、空格和引号，命令行参数包含空格或引号时按 shell 规则引用。

## 生成内容

- `project.godot` 使用新项目名，保留 Godot 4.7、960 × 540 视口、渲染配置和 MCP 插件，主场景指向 `game/main/main.tscn`。
- 主场景替换为显示项目名的标题占位。`main.gd` 仅同步标题；角色、收集物、关卡、HUD、示例输入映射与碰撞层移除。
- `tests/test_game.gd` 替换为主场景和项目名的基础检查；MCP 联调检查同时支持模板和初始化后的空项目。
- 根 README、游戏设计、视觉约定和文档索引调整为新项目内容。
- `.agents/skills/`、`.codex/`、`addons/`、`tools/`、开发约定与第三方许可证保留。`assets/`、剧情文档和示例之外的文件也会复制。
- `.git/`、`.godot/`、Python 缓存、根目录的 `build/`、`builds/`、`exports/` 不复制。输出项目尚未建立 Git 历史。

命令保留原模板以便再次生成项目。初始化用于创建新的游戏起点；制作已有游戏的完整副本时，应直接复制项目。

## 下一步

```bash
cd ../star-adventure
python3 tools/dev.py check
python3 tools/dev.py capture
python3 tools/dev.py editor
```

当前画面只有项目名。先更新 `docs/design.md`，确定首个可玩的核心循环，再让 Codex 按相关技能实现。标题节点和同步脚本可以直接替换，增加玩法后同步更新行为测试。

Codex 打开新项目后需信任该项目才能加载项目级 MCP 配置。默认端口为 9080；同一端口一次连接一个项目，更换端口时同步修改 `.codex/config.toml` 和 `tools/dev.py` 的 `MCP_URL`。

修改初始化工具后运行 `python3 tests/test_init_game.py`。该检查在临时目录验证生成结果、文件保留、失败路径、实际场景检查、截图和新项目的 MCP 联调，需要 Godot 与图形环境。
