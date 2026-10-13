extends Node2D


func _ready() -> void:
	$UI/Root/Title.text = ProjectSettings.get_setting("application/config/name")
