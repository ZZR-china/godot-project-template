extends SceneTree


func _initialize() -> void:
	call_deferred("_capture")


func _capture() -> void:
	var scene: PackedScene = load(ProjectSettings.get_setting("application/run/main_scene"))
	var game: Node = scene.instantiate()
	root.add_child(game)
	current_scene = game
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var output: String = OS.get_cmdline_user_args()[0]
	var error: Error = root.get_texture().get_image().save_png(output)
	if error != OK:
		printerr("截图保存失败：", error)
	quit(0 if error == OK else 1)
