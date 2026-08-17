"""Настройки игрового мира и правил Pac-Man.

Модуль содержит только неизменяемые параметры. Значения сгруппированы здесь,
чтобы игровая логика не зависела от числовых литералов в разных файлах.
"""

CELL_SIZE = 20

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

PLAYER_MOVE_SPEED = 15
INITIAL_LIVES = 3

ENEMY_NUMBER_PER_LEVEL = (4, 4, 4)
ENEMY_MOVE_SPEED = 5
ENEMY_RADAR = CELL_SIZE * 5

PELLET_SCORE = 2
POWER_PELLET_SCORE = 50
FRIGHTENED_SCORE = 200

POWER_DURATION = 10_000
FRIGHTENED_SPEED = 0
CHARACTER_START_DELAY = 2_500
WINDOW_CLOSE_DELAY = 8_000

PLAYER_SHAPE_NAMES = {
    "stop": "pac.gif",
    "right": "right.gif",
    "left": "left.gif",
    "up": "up.gif",
    "down": "down.gif",
}
ENEMY_SHAPE_NAMES = (
    "red_enemy.gif",
    "pink_enemy.gif",
    "purple_enemy.gif",
    "blue_enemy.gif",
    "green_enemy.gif",
)
FRIGHTENED_SHAPE_NAME = "frightened.gif"
WALL_SHAPE_NAME = "wall.gif"
POWER_PELLET_SHAPE_NAME = "cherry.gif"

REQUIRED_ASSET_NAMES = (
    *PLAYER_SHAPE_NAMES.values(),
    *ENEMY_SHAPE_NAMES,
    FRIGHTENED_SHAPE_NAME,
    WALL_SHAPE_NAME,
    POWER_PELLET_SHAPE_NAME,
)
