"""Карты уровней и преобразование символов карты в координаты объектов."""

from collections.abc import Sequence

from constants import CELL_SIZE, ENEMY_NUMBER_PER_LEVEL

Coordinate = tuple[float, float]
MazeData = tuple[
    list[Coordinate],
    list[Coordinate],
    list[Coordinate],
    Coordinate,
    list[Coordinate],
]

WALL_SYMBOL = "X"
PELLET_SYMBOL = "."
POWER_PELLET_SYMBOL = "O"
PLAYER_SYMBOL = "P"
GHOST_SYMBOL = "G"
EMPTY_SYMBOL = " "
ALLOWED_SYMBOLS = frozenset(
    {
        WALL_SYMBOL,
        PELLET_SYMBOL,
        POWER_PELLET_SYMBOL,
        PLAYER_SYMBOL,
        GHOST_SYMBOL,
        EMPTY_SYMBOL,
    }
)


class MazeValidationError(ValueError):
    """Ошибка структуры или содержимого карты уровня."""


def validate_maze(maze_level: Sequence[str], expected_ghosts: int) -> None:
    """Проверяет карту перед преобразованием в игровые координаты.

    Аргументы:
        maze_level: Последовательность строк проверяемой карты.
        expected_ghosts: Требуемое количество стартовых позиций призраков.

    Исключения:
        MazeValidationError: Карта пуста, не является прямоугольной, содержит
            неизвестные символы или неправильное количество стартовых позиций.
        ValueError: Ожидаемое количество призраков отрицательно.
    """
    if expected_ghosts < 0:
        raise ValueError("Количество призраков не может быть отрицательным")
    if not maze_level or not maze_level[0]:
        raise MazeValidationError("Карта уровня не должна быть пустой")

    expected_width = len(maze_level[0])
    for row_number, row in enumerate(maze_level, start=1):
        if len(row) != expected_width:
            raise MazeValidationError(
                f"Строка {row_number} имеет длину {len(row)}, "
                f"ожидалось {expected_width}"
            )
        unknown_symbols = set(row) - ALLOWED_SYMBOLS
        if unknown_symbols:
            symbols = ", ".join(repr(item) for item in sorted(unknown_symbols))
            raise MazeValidationError(
                f"Строка {row_number} содержит неизвестные символы: {symbols}"
            )

    player_count = sum(row.count(PLAYER_SYMBOL) for row in maze_level)
    ghost_count = sum(row.count(GHOST_SYMBOL) for row in maze_level)
    if player_count != 1:
        raise MazeValidationError(
            f"На карте должен быть один старт игрока, найдено: {player_count}"
        )
    if ghost_count != expected_ghosts:
        raise MazeValidationError(
            f"На карте должно быть {expected_ghosts} старта призраков, "
            f"найдено: {ghost_count}"
        )
