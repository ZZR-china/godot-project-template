class_name StarterGame
extends Node2D

var score: int = 0
var target_score: int = 0

@onready var pickups: Node2D = $Pickups
@onready var score_label: Label = %Score
@onready var status_label: Label = %Status


func _ready() -> void:
	target_score = pickups.get_child_count()
	for child in pickups.get_children():
		var pickup: StarterPickup = child as StarterPickup
		pickup.collected.connect(_on_pickup_collected)
	_update_score()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("restart"):
		restart()


func restart() -> void:
	var error: Error = get_tree().reload_current_scene()
	assert(error == OK, "无法重新加载主场景")


func _on_pickup_collected() -> void:
	score += 1
	_update_score()
	if score == target_score:
		status_label.text = "全部收集完成！按 R 或点击按钮再来一次。"


func _update_score() -> void:
	score_label.text = "%d / %d" % [score, target_score]
