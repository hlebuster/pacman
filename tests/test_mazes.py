"""Положительные и отрицательные тесты обработки карт."""

import pytest

from mazes import (
    ALL_MAZES,
    MazeValidationError,
    calculate_maze_data,
    validate_maze,
)

VALID_MAZE = (
    "XXXXXXX",
    "XP...GX",
    "X.GOG.X",
    "X..G..X",
    "XXXXXXX",
)


def test_validate_maze_accepts_correct_map() -> None:
    """Правильная карта проходит проверку без исключений."""
    assert validate_maze(VALID_MAZE, expected_ghosts=4) is None


def test_validate_maze_rejects_unknown_symbol() -> None:
    """Неизвестный символ приводит к MazeValidationError."""
    invalid_maze = (*VALID_MAZE[:-1], "XXX?XXX")
    with pytest.raises(MazeValidationError, match="неизвестные символы"):
        validate_maze(invalid_maze, expected_ghosts=4)


def test_calculate_maze_data_returns_all_object_types() -> None:
    """Функция находит стены, точки, усилитель и старты персонажей."""
    walls, pellets, power_pellets, player_start, ghost_starts = calculate_maze_data(
        VALID_MAZE, expected_ghosts=4
    )
    assert walls
    assert pellets
    assert len(power_pellets) == 1
    assert player_start not in walls
    assert len(ghost_starts) == 4


def test_calculate_maze_data_rejects_missing_player() -> None:
    """Карта без старта игрока не преобразуется в координаты."""
    invalid_maze = tuple(row.replace("P", ".") for row in VALID_MAZE)
    with pytest.raises(MazeValidationError, match="один старт игрока"):
        calculate_maze_data(invalid_maze, expected_ghosts=4)


@pytest.mark.parametrize("maze_level", ALL_MAZES)
def test_project_maze_has_expected_character_starts(
    maze_level: tuple[str, ...],
) -> None:
    """Каждая встроенная карта содержит один старт игрока и четыре призрака."""
    data = calculate_maze_data(maze_level, expected_ghosts=4)
    assert data[3] is not None
    assert len(data[4]) == 4
