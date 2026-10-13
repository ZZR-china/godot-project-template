extends SceneTree

var failures: int = 0
var checks: int = 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var packed: PackedScene = load("res://scenes/main.tscn")
	var game: StarterGame = packed.instantiate()
	root.add_child(game)
	current_scene = game
	await physics_frame
	await process_frame
	_check(game.score_label.text == "0 / 5", "启动后显示收集目标")
	_check(game.pickups.get_child_count() == 5, "启动后存在五个收集物")

	var player: StarterPlayer = game.get_node("Player")
	var start: Vector2 = player.position
	Input.action_press("move_right")
	await create_timer(0.15).timeout
	Input.action_release("move_right")
	_check(player.position.x > start.x + 10.0, "方向输入使玩家移动")

	player.position = Vector2(80, 300)
	Input.action_press("move_left")
	await create_timer(0.2).timeout
	Input.action_release("move_left")
	_check(player.position.x >= 60.0, "边界墙阻止玩家离开场地")

	for pickup in game.pickups.get_children():
		player.global_position = (pickup as Area2D).global_position
		# 传送后等待物理服务器同步位置并派发 Area2D 信号。
		for frame in range(4):
			await physics_frame
		await process_frame
	_check(game.score_label.text == "5 / 5", "碰到收集物后累计得分")
	_check(game.pickups.get_child_count() == 0, "收集物从场景移除")
	_check(game.status_label.text.begins_with("全部收集完成"), "收集全部后显示完成反馈")

	var restart_event: InputEventAction = InputEventAction.new()
	restart_event.action = "restart"
	restart_event.pressed = true
	Input.parse_input_event(restart_event)
	await scene_changed
	var restarted: StarterGame = current_scene as StarterGame
	_check(restarted.score_label.text == "0 / 5", "重开输入重置分数")
	_check(restarted.pickups.get_child_count() == 5, "重开输入恢复全部收集物")
	current_scene.queue_free()
	await process_frame
	print("检查完成：%d 项，失败 %d 项" % [checks, failures])
	quit(1 if failures else 0)


func _check(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error(description)
