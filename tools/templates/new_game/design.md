# {{GAME_NAME}}：游戏设计

当前项目只有显示项目名的主场景，没有预设角色、关卡、收集或战斗玩法。先补充以下目标，再让 Codex 实现一个可玩的核心循环。

- 玩家要做什么，怎样判断成功或失败？
- 首个可玩版本包含哪些操作、角色和场景？
- 哪些反馈需要通过运行画面确认？

主入口为 `game/main/main.tscn`。当前检查验证场景可加载、项目名显示正确；实现玩法后更新 `tests/test_game.gd`，覆盖核心行为与关键失败路径。

运行 `python3 tools/dev.py check` 检查行为，用 `python3 tools/dev.py capture` 或 MCP 截图检查画面。
