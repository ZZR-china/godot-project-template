extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var scene: PackedScene = load(ProjectSettings.get_setting("application/run/main_scene"))
	if scene == null:
		printerr("主场景无法加载")
		quit(1)
		return
	var game: Node = scene.instantiate()
	root.add_child(game)
	current_scene = game
	await process_frame
	var title: Label = game.get_node_or_null("UI/Root/Title") as Label
	if not game is Node2D or title == null or title.text != ProjectSettings.get_setting("application/config/name"):
		printerr("新游戏主场景或项目名显示不正确")
		quit(1)
		return
	if not root.get_visible_rect().encloses(title.get_global_rect()):
		printerr("项目名显示超出视口边界")
		quit(1)
		return
	print("检查完成：新游戏主场景可加载，标题与项目名一致。")
	quit(0)
