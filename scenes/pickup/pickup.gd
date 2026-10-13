class_name StarterPickup
extends Area2D

signal collected


func _ready() -> void:
	var tween: Tween = create_tween().set_loops()
	tween.tween_property($Crystal, "scale", Vector2(1.15, 1.15), 0.6)
	tween.tween_property($Crystal, "scale", Vector2.ONE, 0.6)


func _on_body_entered(_body: Node2D) -> void:
	collected.emit()
	queue_free()
