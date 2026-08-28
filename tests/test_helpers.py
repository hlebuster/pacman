"""Положительные и отрицательные тесты вспомогательных функций."""

from pathlib import Path

import pytest

from main import (
    AssetError,
    game_stats,
    get_random_enemy_shapes,
    minimum_distance_during_frame,
    reset_game_stats,
    resolve_asset_paths,
)
from renderer import format_elapsed_time

PROJECT_ROOT = Path(__file__).parent.parent


def test_get_random_enemy_shapes_returns_unique_names() -> None:
    """Запрошенное допустимое количество изображений не содержит повторов."""
    shapes = get_random_enemy_shapes(4)
    assert len(shapes) == 4
    assert len(set(shapes)) == 4


def test_get_random_enemy_shapes_rejects_excessive_count() -> None:
    """Запрос лишних изображений отклоняется."""
    with pytest.raises(ValueError, match="превышает"):
        get_random_enemy_shapes(100)


def test_resolve_asset_paths_returns_posix_paths(tmp_path: Path) -> None:
    """Существующие ресурсы возвращаются с универсальными разделителями."""
    for name in ("first.gif", "second.gif"):
        (tmp_path / name).write_bytes(b"GIF89a")
    paths = resolve_asset_paths(tmp_path, ("first.gif", "second.gif"))
    assert set(paths) == {"first.gif", "second.gif"}
    assert all("\\" not in path for path in paths.values())


def test_resolve_asset_paths_rejects_missing_file(tmp_path: Path) -> None:
    """Отсутствующий обязательный ресурс вызывает AssetError."""
    with pytest.raises(AssetError, match="Не найден обязательный файл"):
        resolve_asset_paths(tmp_path, ("missing.gif",))


def test_project_assets_are_complete() -> None:
    """Финальная папка содержит весь комплект ресурсов игры."""
    paths = resolve_asset_paths(PROJECT_ROOT / "assets")
    assert len(paths) == 13


def test_format_elapsed_time_formats_minutes_and_seconds() -> None:
    """Секунды преобразуются в формат минуты:секунды."""
    assert format_elapsed_time(125.9) == "2:05"


def test_format_elapsed_time_rejects_negative_value() -> None:
    """Отрицательная продолжительность отклоняется."""
    with pytest.raises(ValueError, match="отрицательной"):
        format_elapsed_time(-1)


def test_reset_game_stats_sets_start_and_zeroes_counters() -> None:
    """Сброс устанавливает таймер и обнуляет все счётчики."""
    game_stats["pellets_eaten"] = 10
    reset_game_stats(start_time=123.0)
    assert game_stats == {
        "start_time": 123.0,
        "total_score": 0,
        "pellets_eaten": 0,
        "power_pellets_eaten": 0,
        "ghosts_defeated": 0,
    }


def test_reset_game_stats_rejects_negative_start_time() -> None:
    """Отрицательное начальное время отклоняется."""
    with pytest.raises(ValueError, match="не может быть отрицательным"):
        reset_game_stats(start_time=-1)


def test_minimum_distance_detects_crossing_paths() -> None:
    """Пересечение между кадрами даёт нулевое минимальное расстояние."""
    distance = minimum_distance_during_frame(
        (-15.0, 0.0),
        (0.0, 0.0),
        (0.0, 0.0),
        (-5.0, 0.0),
    )
    assert distance == pytest.approx(0.0)


def test_minimum_distance_rejects_distant_parallel_paths() -> None:
    """Параллельное движение на расстоянии не считается столкновением."""
    distance = minimum_distance_during_frame(
        (0.0, 0.0),
        (15.0, 0.0),
        (0.0, 20.0),
        (5.0, 20.0),
    )
    assert distance == pytest.approx(20.0)
