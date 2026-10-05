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


maze_level_1 = (
    "XXXXXXXXXXXXXX.XXXXXXXXXXXXXX",
    "XO........X.......X....G....X",
    "X.XXX.X.X.X.X...X.X.X.X.XXX.X",
    "X.X X.X.X.X.XXXXX.X.X.X.X X.X",
    "X.XXX.X.X...........X.X.XXX.X",
    "X.....X...X.XXXXXXX...X.....X",
    "X.XXXXX.X.X.......X.X.XXXXX.X",
    "X..G....X.XXXXXXX.X.X.......X",
    "X.X.X.X.X.X.....X.X.X.X.X.X.X",
    "X.X.X.X.X.X.XXX.X.X.X.X.X.X.X",
    "X.X.X...X.X.XOX.X.X.X.G.X.X.X",
    "X.X.XXX.X.X.X...X.X.X.XXX.X.X",
    "X.......X.X.XXXXX.X.X.......X",
    "X.XXXXX.X....P....X.X.XXXXX.X",
    "X.....X...XXXXXXXXX...X.....X",
    "X.XXX.X.X..G........X.X.XXX.X",
    "X.X X.X.X.X.XXXXX.X.X.X.X X.X",
    "X.XXX.X.X.X.X...X.X.X.X.XXX.X",
    "X.........X.......X.........X",
    "XXXXXXXXXXXXXX.XXXXXXXXXXXXXX",
)

maze_level_2 = (
    "XXXXXXXXXXXXXXX.XXXXXXXXXXXXX",
    "X.X.X.................O.X.X.X",
    "X.X.X.XXXX.XXXXXXX.XXXX.X.X.X",
    "X.X.X.X  X.........X  X.X.X.X",
    "X.G...X  X.X.X.X.X.X  X.....X",
    "X.XXX.XXXX.X.X.X.X.XXXX.XXX.X",
    "X.X X...................X X.X",
    "X.XXX.XX.XXXXXXXXXXX.XX.XXX.X",
    "X........X.........X........X",
    "X.XXXX.X...XXXX.XX...X.XXXX.X",
    "X.X  X.X.X.XP....X.X.X.X  X.X",
    "X.X  X.X.X.X.XXX.X.X.X.X  X.X",
    "X.XXXX.X.X...X X.X.X.X.XXXX.X",
    "X......X.X.X.X X.X.X.X..G...X",
    "X.XXXX.X.X.X.XXX.X.X.X.XXXX.X",
    "X.X  X.X.X.X.......X.X.X  X.X",
    "XOXXXX.X...XXXXXXX...X.XXXX.X",
    "X........X.........X........X",
    "X.XXX.XX.XXXXXXXXXXX.XX.XXX.X",
    "X.X X...................X X.X",
    "X.XXX.XXXX.X.X.X.X.XXXX.XXX.X",
    "X.....X  X.X.X.X.X.X  X.G...X",
    "X.X.X.X  X.........X  X.X.X.X",
    "X.X.X.XXXX.XXXXXXX.XXXX.X.X.X",
    "X.X.X..G................X.X.X",
    "XXXXXXXXXXXXXXX.XXXXXXXXXXXXX",
)

maze_level_3 = (
    "XXXXXXXXXXXXXXXX.XXXXXXXXXXXXXXXX",
    "X.................G............OX",
    "X.XXX.XXX.XXXXXX.XXXXXX.XXX.XXX.X",
    "X.X X.X X.X    X.X    X.X X.X X.X",
    "X.XXX.X X.XXXXXX.XXXXXX.X X.XXX.X",
    "X.....XXX.X....X.X....X.XXX.....X",
    "XXXXX.......XX.X.X.XX.......XXXXX",
    "X..P..XXXXX...........XXXXX.....X",
    "X.XXX.......XXXXXXXXX.......XXX.X",
    "X.....XXXXX...........XXXXX.G...X",
    "X.XXX...O...XXXX.XXXX.......XXX.X",
    "X.X X.XXXXX.X  X.X  X.XXXXX.X X.X",
    "X.X X.X   X.X  X.X  X.X   X.X X.X",
    "X.X X.X   X.X  X.X  X.X   X.X X.X",
    "X.X X.XXXXX.X  X.X  X.XXXXX.X X.X",
    "X.XXX.......XXXX.XXXX...O...XXX.X",
    "X..G..XXXXX...........XXXXX.....X",
    "X.XXX.......XXXXXXXXX.......XXX.X",
    "X.....XXXXX...........XXXXX.....X",
    "XXXXX.......XX.X.X.XX.......XXXXX",
    "X.....XXX.X....X.X....X.XXX.....X",
    "X.XXX.X X.XXXXXX.XXXXXX.X X.XXX.X",
    "X.X X.X X.X    X.X    X.X X.X X.X",
    "X.XXX.XXX.XXXXXX.XXXXXX.XXX.XXX.X",
    "XO.....................G........X",
    "XXXXXXXXXXXXXXXX.XXXXXXXXXXXXXXXX",
)

ALL_MAZES = (maze_level_1, maze_level_2, maze_level_3)


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


def calculate_maze_data(
    maze_level: Sequence[str],
    expected_ghosts: int = 4,
) -> MazeData:
    """Преобразует символы прямоугольной карты в координаты объектов.

    Аргументы:
        maze_level: Последовательность строк карты уровня.
        expected_ghosts: Требуемое количество стартовых позиций призраков.

    Возвращает:
        Кортеж со стенами, обычными точками, усилителями, стартом игрока и
        стартовыми позициями призраков.

    Исключения:
        MazeValidationError: Карта не соответствует требованиям.
        ValueError: Ожидаемое количество призраков отрицательно.
    """
    validate_maze(maze_level, expected_ghosts)

    walls: list[Coordinate] = []
    pellets: list[Coordinate] = []
    power_pellets: list[Coordinate] = []
    player_start: Coordinate | None = None
    ghost_starts: list[Coordinate] = []

    rows = len(maze_level)
    columns = len(maze_level[0])
    start_x = -(columns * CELL_SIZE) / 2
    start_y = (rows * CELL_SIZE) / 2

    for row_index, row in enumerate(maze_level):
        for column_index, character in enumerate(row):
            coordinate = (
                start_x + CELL_SIZE * column_index,
                start_y - CELL_SIZE * row_index,
            )
            if character == WALL_SYMBOL:
                walls.append(coordinate)
            elif character == PELLET_SYMBOL:
                pellets.append(coordinate)
            elif character == POWER_PELLET_SYMBOL:
                power_pellets.append(coordinate)
            elif character == PLAYER_SYMBOL:
                player_start = coordinate
            elif character == GHOST_SYMBOL:
                ghost_starts.append(coordinate)

    if player_start is None:
        raise MazeValidationError("Не удалось определить старт игрока")

    return walls, pellets, power_pellets, player_start, ghost_starts


def validate_all_mazes() -> None:
    """Проверяет все встроенные карты и их настройки призраков.

    Исключения:
        MazeValidationError: Хотя бы одна встроенная карта некорректна.
        ValueError: Количество настроек уровней не совпадает с числом карт.
    """
    if len(ALL_MAZES) != len(ENEMY_NUMBER_PER_LEVEL):
        raise ValueError(
            "Количество карт не совпадает с количеством настроек призраков"
        )
    for maze_level, enemy_count in zip(ALL_MAZES, ENEMY_NUMBER_PER_LEVEL):
        validate_maze(maze_level, enemy_count)
