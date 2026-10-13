# 开发依赖与上游来源

本模板的游戏逻辑只依赖 Godot。技能、MCP、Python 开发入口用于开发和验证；第三方内容保留许可证，MCP 的本地补丁记录如下。

## 引擎与开发入口

- Godot：目标版本 4.7.x，本机使用 `4.7.2.stable.official.ed1daf0bf` 验证。
- Python：3.9+，`tools/dev.py` 使用标准库，无需 `pip install`。
- Codex：读取 `.agents/skills/` 与受信任项目内的 `.codex/config.toml`。

## Godot 技能

来源：[gamedev-skills/awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills)。2026-10-13 查询为 1,467 stars（整个仓库）。

固定提交：`0a70cfc64672d512c5b5b6006b5dcb5cf90dbdbd`。

安装目录：`.agents/skills/`。许可证：Apache-2.0，原文位于 `.agents/skills/LICENSE`。

| 技能 | 用途 |
|---|---|
| `godot-gdscript` | GDScript、类型、生命周期与异步 |
| `godot-nodes-scenes` | 节点、场景、实例化与资源路径 |
| `godot-signals-groups` | 信号连接与节点组 |
| `godot-2d-movement` | 俯视角和横版角色移动 |
| `godot-physics` | 碰撞层、物理体、Area 与射线 |
| `godot-ui-control` | HUD、菜单、容器与键盘／手柄焦点 |
| `godot-animation` | AnimationPlayer、AnimationTree 与 Tween |
| `godot-gdscript-headless-testing` | 无界面的 GDScript 行为测试与退出码 |

只复制了以上技能目录及其参考资料，没有安装整个技能库。技能按任务读取，项目约定优先；例如对象池和全局事件总线只在当前需求需要时使用。

## Godot MCP

来源：[yurineko73/Godot-MCP-Native](https://github.com/yurineko73/Godot-MCP-Native)。2026-10-13 查询为 848 stars。

固定版本：`v1.0.8`，提交 `2e138eda1a206e2bc1f147fa021de28727b47644`。

安装目录：`addons/godot_mcp/`。许可证：MIT，原文位于 `addons/godot_mcp/LICENSE`。

插件原生运行于 Godot 编辑器，项目配置使用 HTTP MCP。没有安装可选的 `gdmcp` CLI、聊天客户端、云服务或其他 MCP。

本地补丁：`mcp_server_native.gd` 的 `_exit_tree()` 断开调试工具对服务器的反向引用，清空工具实例、移除引擎元数据并注销运行探针自动加载项。原版在导入退出时出现循环引用，报告 495 个实例和 10 个资源残留；补丁用于正常释放开发工具，避免关闭编辑器后留下探针。启动工具的补丁单独记录如下。更新插件时应确认上游是否已修复再迁移补丁，保留 MIT 许可证。

模板默认工具：启动成功后，在上游 30 个核心工具之外启用 `get_class_api_metadata`、`get_scene_structure`、`get_editor_screenshot`、`get_runtime_scene_tree`、`inspect_runtime_node`、`simulate_runtime_input_event`、`get_runtime_screenshot`、`await_runtime_condition`，用于 API 查询、场景检查、输入和画面验证。其他高级工具仍按需启用。

开发命令通过 `--mcp-server --mcp-port 9080` 启动插件；保持上游默认的本地访问设置。插件临时注册的 `MCPRuntimeProbe` 用于运行时调试；游戏交付前需停用插件并检查导出。

### 运行工具的本地补丁

补丁文件：`addons/godot_mcp/tools/editor_tools_native.gd`，函数 `_tool_run_project()`。

HTTP MCP 请求来自 Godot 的延迟消息队列。直接调用编辑器的场景启动 API 会触发 `Do not use progress dialog (task) while flushing the message queue or using call_deferred()!`。工具内部现在先等待 `SceneTree.process_frame`，离开消息队列刷新阶段后再启动；指定场景、当前场景和主场景回退都经过这一处理。

启动前同时调用调试桥已有的 `reset_probe_ready()`，清除上一轮运行留下的就绪标记，避免连续运行时将旧探针当作本轮启动完成。保留原有的调试会话与探针等待，以及场景不存在、项目已经运行时的错误返回。

调用方式：先通过 `get_project_info` 确认项目路径，再调用 `run_project`，参数为 `{"allow_window": true}`；指定场景时增加 `"scene_path": "res://game/main/main.tscn"`。省略场景路径时优先运行当前场景，没有打开场景时运行主场景。使用运行时调试工具前确认返回的 `session_active` 和 `probe_ready`；结束时调用 `stop_project`。截图参数使用 `save_path`，例如 `res://.godot/preview.png`。

回归入口为 `python3 tests/test_mcp_run_project.py`，需要图形环境和空闲的 9080 端口。脚本复制不含缓存的临时项目，使用独立项目名隔离插件用户配置，直接调用 MCP，并检查编辑器输出；任何 `ERROR:` 或 `SCRIPT ERROR:` 都会使检查失败。截图检查使用独立路径并拒绝过期缓存。主场景截图保存到当前仓库的 `.godot/mcp-run-project-preview.png`，临时项目在结束后删除。

## 更新

更新前阅读上游变更和目标 Godot 版本，选择明确的发布版本或提交。替换对应第三方目录时保留许可证，更新本文中的版本记录，然后执行：

```bash
python3 tools/dev.py check
python3 tests/test_mcp_run_project.py
python3 tools/dev.py editor
# 在另一个终端中
python3 tools/dev.py mcp
python3 tools/dev.py capture
```

确认脚本导入、核心玩法、MCP 项目路径与画面后再采用新版本。第三方仓库的许可证覆盖对应第三方目录，不能视为本仓库所有内容的统一许可证。

## 验证记录

2026-10-13 在 macOS / Godot 4.7.2 上验证：

- 资源导入与 9 项核心行为检查通过；不包含 `.godot/` 的临时副本也通过相同检查。
- Codex CLI 正确读取项目级 MCP 配置，HTTP 握手确认连接到本仓库，工具列表为 38 项。
- MCP 启动游戏后，模拟 D 键使玩家 x 从 160 移动至 280，模拟 R 键使其恢复至 160；运行时截图已生成并人工检查。
- 编辑器关闭后没有引擎资源残留错误，`project.godot` 不保留运行探针自动加载项。

当前目录与启动补丁复验：

- 主场景为 `res://game/main/main.tscn`；角色和收集物移入 `game/` 对应功能目录，保留原有脚本 UID。
- 当前工作区和不包含 `.godot/` 的副本均通过资源导入与 9 项行为检查。
- 主场景回退、当前场景和指定角色场景均通过直接 `run_project` 启动、重复启动拒绝与停止检查；当前场景和指定场景均通过新探针与非过期截图检查。
- 不存在的场景返回明确错误，编辑器保持未运行状态；编辑器退出码为 0，日志无引擎错误，运行探针自动加载项已移除。
- 在临时副本中移除帧等待后，相同回归检查捕获到原始进度对话框错误并失败，确认检查能够识别此次问题。
