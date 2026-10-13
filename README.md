# Codex 2D Starter

以 Codex 为主开发的 Godot 2D 游戏模板。使用 Godot 4.7、GDScript 和 Compatibility 渲染器，带项目级技能、Godot MCP（让 Codex 直接操作编辑器的工具接口）、运行检查与截图入口。

示例是一段可删除的俯视角收集玩法：移动角色、绕过障碍、收集五个晶体、重新开始。场景和 UI 都保存在 `.tscn` 中，可以直接在 Godot 编辑器查看和修改。模板不预置战斗、背包或全局游戏框架。

## 快速开始

需要 Godot 4.7.x 和 Python 3.9+。Python 工具仅使用标准库。开发入口依次查找 `GODOT_BIN`、PATH 中的 `godot`、`/Applications/Godot.app/Contents/MacOS/Godot`；显式设置的 `GODOT_BIN` 无效时直接报错。

从仓库根目录执行：

```bash
python3 tools/dev.py editor
```

这会打开 Godot 编辑器，并启动当前项目的 MCP 服务。按 **F6** 运行当前场景，或按 **F5** 运行主场景。使用 WASD、方向键或手柄左摇杆移动；按 R、手柄 Y 或点击“重新开始”重开。

也可以直接运行游戏：

```bash
python3 tools/dev.py run
```

Godot 不在默认位置时，例如：

```bash
GODOT_BIN=/path/to/Godot python3 tools/dev.py editor
```

## 使用 Codex 开发

用 Codex 打开这个仓库。项目技能位于 `.agents/skills/`，MCP 配置位于 `.codex/config.toml`；新安装的技能在下一轮对话中可用。MCP 配置如果没有出现，重新打开项目或重启 Codex。项目需要在 Codex 中被信任，项目级 MCP 配置才会加载。

可以从这样的任务开始：

> 把示例改成一个 2D 横版跳跃游戏。先做一个能左右移动、跳跃、到达终点并重开的关卡，使用占位图形。完成后运行检查并截图验证。

> 在当前俯视角示例里加入一个追逐玩家的敌人。先实现碰撞失败和重开，保持脚本短小。

> 用已有 2D 技能为游戏增加一个暂停菜单，支持键盘和手柄，保持 UI 在编辑器中可见。

Codex 应先确认 Godot 版本和当前 MCP 连接的项目，再按任务读取对应技能，完成最小玩法、运行检查、查看画面。项目边界见 `AGENTS.md`；依赖版本与许可证见 [docs/dependencies.md](docs/dependencies.md)。

## 检查与截图

```bash
# 导入资源并执行示例的行为测试
python3 tools/dev.py check

# 运行主场景并截图，默认保存到 .godot/preview.png
python3 tools/dev.py capture

# 另存截图
python3 tools/dev.py capture --output /tmp/game-preview.png

# 确认 MCP 能读取当前项目
python3 tools/dev.py mcp
```

`check` 检查启动、移动、墙体碰撞、收集、完成反馈与重开。Godot 的退出码有时无法反映脚本错误，因此开发入口同时检查引擎错误输出，并为非交互检查设置超时。截图需要图形环境；命令行行为检查不验证美术、布局或操作手感。

## MCP 的使用方式

已安装 [Godot-MCP-Native v1.0.8](https://github.com/yurineko73/Godot-MCP-Native/releases/tag/v1.0.8)，无需额外 Node/Python 服务。通过 `python3 tools/dev.py editor` 启动时，插件提供 `http://127.0.0.1:9080/mcp`，Codex 可以检查场景、修改节点与脚本、运行项目、读取日志和截图。

- 直接双击 `project.godot` 打开时，在 MCP 插件面板中点击启动；插件上游默认不开启自动启动。
- 9080 被其他项目占用时，先关闭那个项目的 MCP，或同时修改启动命令中的 `--mcp-port`、`.codex/config.toml` 的 URL 和 `tools/dev.py` 的 `MCP_URL`。操作前始终确认项目路径。
- 插件使用本地用户数据保存面板配置。开启编辑器时会注册 `MCPRuntimeProbe` 自动加载项，用于运行时调试；正常关闭插件时会移除。它是开发工具，交付游戏前应停用插件并检查导出内容。
- 当前会话不会因为修改配置就立即获得新的 MCP 工具。重新加载 Codex 后连接，或先用 `python3 tools/dev.py mcp` 验证服务。
- 模板默认启用 30 个核心工具和 8 个画面／运行检查工具。运行和切换编辑器场景时，按工具 schema 传入 `allow_window=true` 或 `allow_ui_focus=true`；上游默认保留编辑器焦点，不擅自弹窗。

## 目录

```text
project.godot              引擎配置、输入映射和主场景入口
scenes/main.tscn           示例关卡与 HUD
scenes/main.gd             得分、完成反馈与重开
scenes/player/            可复用的角色场景与移动脚本
scenes/pickup/            可复用的收集物场景与信号
tests/test_game.gd        核心行为测试
tools/dev.py              编辑器、运行、检查、截图和 MCP 诊断入口
.agents/skills/           项目级 Godot 技能与参考资料
.codex/config.toml        项目级 Codex MCP 配置
addons/godot_mcp/         固定版本的第三方编辑器插件
docs/dependencies.md      来源、版本和更新说明
```

新增功能时，优先把它的脚本、场景和专用资源放在同一目录，例如 `scenes/enemy/`。需要共享素材时再建立 `assets/`。保留 Godot 生成的 `.uid` 与资源导入元数据；`.godot/` 缓存和导出产物不提交。

## 用作新游戏模板

复制仓库内容到新项目，保留 `.agents/`、`.codex/`、`AGENTS.md` 和第三方许可证；不复制 `.git/`、`.godot/` 或构建产物。在 `project.godot` 修改游戏名称，替换 `scenes/main.tscn` 及示例测试，然后运行检查。新项目沿用同一 MCP 端口，一次连接一个项目。

技能与 MCP 都来自超过 200 stars 的仓库，具体查询值和固定版本记录在依赖文档中。游戏代码与上游工具分开放置，替换示例时无需修改工具。
