"""Точка входа и основной игровой цикл Pac-Man.

Программа запускается с необязательным параметром ``--assets-dir``, который
позволяет выбрать произвольную папку с GIF-изображениями.
"""

import argparse
import math
import random
import time
import turtle
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict

from actors import Enemy, Player
from constants import (
    CELL_SIZE,
    CHARACTER_START_DELAY,
    ENEMY_NUMBER_PER_LEVEL,
    ENEMY_SHAPE_NAMES,
    FPS,
    FRIGHTENED_SCORE,
    FRIGHTENED_SHAPE_NAME,
    INITIAL_LIVES,
    PELLET_SCORE,
    PLAYER_SHAPE_NAMES,
    POWER_DURATION,
    POWER_PELLET_SCORE,
    POWER_PELLET_SHAPE_NAME,
    REQUIRED_ASSET_NAMES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WALL_SHAPE_NAME,
    WINDOW_CLOSE_DELAY,
)
from mazes import (
    ALL_MAZES,
    Coordinate,
    MazeValidationError,
    calculate_maze_data,
    validate_all_mazes,
)
from renderer import GameOverPopup, LivesPen, Pellet, PowerPellet, ScorePen, Wall


class AssetError(RuntimeError):
    """Ошибка расположения или загрузки графического ресурса."""


class GameStats(TypedDict):
    """Структура статистики всей игровой сессии.

    Атрибуты:
        start_time: Момент запуска монотонного таймера.
        total_score: Итоговое количество очков.
        pellets_eaten: Количество собранных обычных точек.
        power_pellets_eaten: Количество собранных усилителей.
        ghosts_defeated: Количество побеждённых призраков.
    """

    start_time: float
    total_score: int
    pellets_eaten: int
    power_pellets_eaten: int
    ghosts_defeated: int


game_stats: GameStats = {
    "start_time": 0.0,
    "total_score": 0,
    "pellets_eaten": 0,
    "power_pellets_eaten": 0,
    "ghosts_defeated": 0,
}


def reset_game_stats(start_time: float | None = None) -> None:
    """Сбрасывает статистику перед новой игровой сессией.

    Аргументы:
        start_time: Начальное значение таймера. Если значение не указано,
            используется текущий момент монотонного таймера.

    Исключения:
        ValueError: Переданное значение таймера отрицательно.
    """
    actual_start_time = time.monotonic() if start_time is None else start_time
    if actual_start_time < 0:
        raise ValueError("Начальное время не может быть отрицательным")
    game_stats.update(
        {
            "start_time": actual_start_time,
            "total_score": 0,
            "pellets_eaten": 0,
            "power_pellets_eaten": 0,
            "ghosts_defeated": 0,
        }
    )


def parse_arguments(arguments: Sequence[str] | None = None) -> argparse.Namespace:
    """Считывает параметры командной строки.

    Аргументы:
        arguments: Необязательный набор аргументов вместо ``sys.argv``.

    Возвращает:
        Пространство имён с выбранной папкой ресурсов.
    """
    default_assets = Path(__file__).parent / "assets"
    parser = argparse.ArgumentParser(description="Игра Pac-Man на трёх уровнях")
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=default_assets,
        help="папка с GIF-изображениями (по умолчанию: assets рядом с main.py)",
    )
    return parser.parse_args(arguments)


def resolve_asset_paths(
    assets_dir: Path,
    required_names: Sequence[str] = REQUIRED_ASSET_NAMES,
) -> dict[str, str]:
    """Проверяет ресурсы и формирует пути с разделителем ``/``.

    Аргументы:
        assets_dir: Папка с изображениями, выбранная пользователем.
        required_names: Имена обязательных файлов.

    Возвращает:
        Соответствие имени GIF-файла готовому пути.

    Исключения:
        AssetError: Папка не существует либо в ней отсутствует обязательный
            файл.
    """
    if not assets_dir.is_dir():
        raise AssetError(f"Папка с изображениями не найдена: {assets_dir}")

    paths: dict[str, str] = {}
    for name in required_names:
        asset_path = assets_dir / name
        if not asset_path.is_file():
            raise AssetError(f"Не найден обязательный файл: {asset_path}")
        paths[name] = asset_path.resolve().as_posix()
    return paths


def minimum_distance_during_frame(
    player_start: Coordinate,
    player_end: Coordinate,
    enemy_start: Coordinate,
    enemy_end: Coordinate,
) -> float:
    """Вычисляет минимальное расстояние между персонажами за один кадр.

    Проверка учитывает весь путь персонажей между начальными и конечными
    координатами, поэтому столкновение не пропускается при быстром встречном
    движении.

    Аргументы:
        player_start: Позиция игрока в начале кадра.
        player_end: Позиция игрока в конце кадра.
        enemy_start: Позиция призрака в начале кадра.
        enemy_end: Позиция призрака в конце кадра.

    Возвращает:
        Минимальное расстояние между игроком и призраком за кадр.
    """
    player_jump = (
        abs(player_end[0] - player_start[0]) > CELL_SIZE * 2
        or abs(player_end[1] - player_start[1]) > CELL_SIZE * 2
    )
    enemy_jump = (
        abs(enemy_end[0] - enemy_start[0]) > CELL_SIZE * 2
        or abs(enemy_end[1] - enemy_start[1]) > CELL_SIZE * 2
    )
    if player_jump or enemy_jump:
        distance_before = math.dist(player_start, enemy_start)
        distance_after = math.dist(player_end, enemy_end)
        return min(distance_before, distance_after)

    relative_start_x = player_start[0] - enemy_start[0]
    relative_start_y = player_start[1] - enemy_start[1]
    relative_move_x = (
        player_end[0] - player_start[0] - enemy_end[0] + enemy_start[0]
    )
    relative_move_y = (
        player_end[1] - player_start[1] - enemy_end[1] + enemy_start[1]
    )
    relative_move_squared = relative_move_x**2 + relative_move_y**2

    if relative_move_squared == 0:
        return math.hypot(relative_start_x, relative_start_y)

    closest_time = -(
        relative_start_x * relative_move_x
        + relative_start_y * relative_move_y
    ) / relative_move_squared
    closest_time = max(0.0, min(1.0, closest_time))
    closest_x = relative_start_x + closest_time * relative_move_x
    closest_y = relative_start_y + closest_time * relative_move_y
    return math.hypot(closest_x, closest_y)


def init_screen() -> turtle.Screen:
    """Создаёт и настраивает главное окно игры.

    Возвращает:
        Настроенное окно turtle.
    """
    screen = turtle.Screen()
    screen.tracer(0)
    screen.title("PacMan Game - Level 1")
    screen.setup(SCREEN_WIDTH, SCREEN_HEIGHT)
    screen.bgcolor("black")
    return screen


def register_shapes(
    screen: turtle.Screen,
    asset_paths: Mapping[str, str],
) -> None:
    """Регистрирует GIF-файлы как фигуры turtle.

    Аргументы:
        screen: Главное окно игры.
        asset_paths: Проверенные пути к изображениям.

    Исключения:
        AssetError: Turtle не удалось зарегистрировать изображение.
    """
    try:
        for path in asset_paths.values():
            screen.register_shape(path)
    except turtle.TurtleGraphicsError as error:
        raise AssetError(f"Не удалось загрузить изображение: {error}") from error


def bind_controls(screen: turtle.Screen, player: Player) -> None:
    """Привязывает W-A-S-D к направлениям движения игрока.

    Аргументы:
        screen: Главное окно игры.
        player: Управляемый объект игрока.
    """
    screen.listen()
    screen.onkeypress(player.turn_right, "d")
    screen.onkeypress(player.turn_left, "a")
    screen.onkeypress(player.turn_up, "w")
    screen.onkeypress(player.turn_down, "s")


def get_random_enemy_shapes(count: int) -> list[str]:
    """Выбирает случайные изображения призраков без повторений.

    Аргументы:
        count: Требуемое количество изображений.

    Возвращает:
        Список имён GIF-файлов призраков.

    Исключения:
        ValueError: Количество отрицательно или превышает число изображений.
    """
    if count < 0:
        raise ValueError("Количество призраков не может быть отрицательным")
    if count > len(ENEMY_SHAPE_NAMES):
        raise ValueError(
            "Количество призраков превышает количество доступных изображений"
        )
    return random.sample(list(ENEMY_SHAPE_NAMES), count)


def create_enemies(
    walls: Sequence[Coordinate],
    player: Player,
    ghost_starts: Sequence[Coordinate],
    enemy_count: int,
    asset_paths: Mapping[str, str],
) -> list[Enemy]:
    """Создаёт призраков в заданных картой стартовых позициях.

    Аргументы:
        walls: Координаты стен текущего уровня.
        player: Объект игрока.
        ghost_starts: Стартовые координаты призраков.
        enemy_count: Количество призраков на уровне.
        asset_paths: Проверенные пути к изображениям.

    Возвращает:
        Список созданных призраков.

    Исключения:
        ValueError: Стартовых позиций недостаточно.
    """
    if len(ghost_starts) < enemy_count:
        raise ValueError("На карте недостаточно стартовых позиций призраков")

    shape_names = get_random_enemy_shapes(enemy_count)
    return [
        Enemy(
            start_x,
            start_y,
            walls,
            player,
            asset_paths[shape_name],
            asset_paths[FRIGHTENED_SHAPE_NAME],
        )
        for (start_x, start_y), shape_name in zip(ghost_starts, shape_names)
    ]


def reset_level(
    screen: turtle.Screen,
    wall_pen: Wall,
    pellet_pen: Pellet,
    power_pen: PowerPellet,
    player: Player,
    enemies: list[Enemy],
    level_index: int,
    asset_paths: Mapping[str, str],
) -> tuple[Coordinate, list[Coordinate]]:
    """Загружает следующий уровень и возвращает стартовые позиции.

    Аргументы:
        screen: Главное окно игры.
        wall_pen: Перо стен.
        pellet_pen: Перо обычных точек.
        power_pen: Перо усилителей.
        player: Объект игрока.
        enemies: Изменяемый список призраков.
        level_index: Индекс загружаемого уровня.
        asset_paths: Проверенные пути к изображениям.

    Возвращает:
        Старт игрока и список стартов призраков.

    Исключения:
        MazeValidationError: Карта уровня некорректна.
        IndexError: Индекс уровня находится вне списка карт.
    """
    enemy_count = ENEMY_NUMBER_PER_LEVEL[level_index]
    maze_data = ALL_MAZES[level_index]
    walls, pellets, power_pellets, player_start, ghost_starts = calculate_maze_data(
        maze_data, enemy_count
    )

    wall_pen.walls = walls
    pellet_pen.pellets = pellets
    power_pen.power_pellets = power_pellets
    wall_pen.draw()
    pellet_pen.draw()
    power_pen.draw()

    player.walls = walls
    player.lives = INITIAL_LIVES
    player.shape(player.shapes["stop"])
    player.goto(player_start)
    player.state = "stop"
    player.showturtle()

    for enemy in enemies:
        enemy.hideturtle()
    enemies.clear()
    enemies.extend(
        create_enemies(
            walls,
            player,
            ghost_starts,
            enemy_count,
            asset_paths,
        )
    )
    for enemy in enemies:
        screen.ontimer(enemy.start_move, CHARACTER_START_DELAY)

    return player_start, ghost_starts


def game_loop(
    screen: turtle.Screen,
    player: Player,
    score_pen: ScorePen,
    lives_pen: LivesPen,
    pellet_pen: Pellet,
    power_pen: PowerPellet,
    enemies: list[Enemy],
    popup: GameOverPopup,
    wall_pen: Wall,
    current_level: int,
    player_start: Coordinate,
    ghost_starts: list[Coordinate],
    asset_paths: Mapping[str, str],
) -> None:
    """Обрабатывает один кадр игры и планирует следующий.

    Аргументы:
        screen: Главное окно игры.
        player: Объект игрока.
        score_pen: Перо счёта.
        lives_pen: Перо жизней.
        pellet_pen: Перо обычных точек.
        power_pen: Перо усилителей.
        enemies: Текущий список призраков.
        popup: Перо итогового окна.
        wall_pen: Перо стен.
        current_level: Индекс текущего уровня.
        player_start: Стартовая позиция игрока.
        ghost_starts: Стартовые позиции призраков.
        asset_paths: Проверенные пути к изображениям.
    """
    score_pen.write_score(player.score)
    lives_pen.write_lives(player.lives)

    for coordinate, stamp_id in list(pellet_pen.stamps.items()):
        if player.distance(coordinate) < CELL_SIZE / 2:
            pellet_pen.clearstamp(stamp_id)
            del pellet_pen.stamps[coordinate]
            player.score += PELLET_SCORE
            game_stats["pellets_eaten"] += 1

    for coordinate, stamp_id in list(power_pen.stamps.items()):
        if player.distance(coordinate) < CELL_SIZE / 2:
            power_pen.clearstamp(stamp_id)
            del power_pen.stamps[coordinate]
            player.score += POWER_PELLET_SCORE
            game_stats["power_pellets_eaten"] += 1
            for enemy in enemies:
                enemy.make_frightened(POWER_DURATION)

    player_position_before = tuple(player.position())
    player.move()
    player.check_wall_collision()
    player_position_after = tuple(player.position())

    for enemy in enemies[:]:
        enemy_position_before = tuple(enemy.position())
        enemy.move()
        enemy.check_wall_collision()
        enemy.go_after_player()
        enemy_position_after = tuple(enemy.position())

        distance = minimum_distance_during_frame(
            player_position_before,
            player_position_after,
            enemy_position_before,
            enemy_position_after,
        )
        if distance >= CELL_SIZE / 2:
            continue
        if enemy.is_frightened:
            player.score += FRIGHTENED_SCORE
            game_stats["ghosts_defeated"] += 1
            enemy.hideturtle()
            enemies.remove(enemy)
        else:
            player.goto(player_start)
            player.shape(player.shapes["stop"])
            player.state = "move"
            for index, current_enemy in enumerate(enemies):
                current_enemy.goto(ghost_starts[index])
                current_enemy.shape(current_enemy.enemy_shape)
                current_enemy.move_speed = current_enemy.normal_speed
                current_enemy.is_frightened = False
                current_enemy.start_move()
            player.lives -= 1
            break

    if not power_pen.stamps and not pellet_pen.stamps:
        current_level += 1
        if current_level < len(ALL_MAZES):
            screen.title(f"PacMan Game - Level {current_level + 1}")
            player_start, ghost_starts = reset_level(
                screen,
                wall_pen,
                pellet_pen,
                power_pen,
                player,
                enemies,
                current_level,
                asset_paths,
            )
        else:
            player.state = "stop"
            for enemy in enemies:
                enemy.hideturtle()
                enemy.state = "stop"
            lives_pen.hide()
            elapsed = time.monotonic() - game_stats["start_time"]
            game_stats["total_score"] = player.score
            popup.show_win(game_stats, elapsed)
            screen.update()
            screen.ontimer(screen.bye, WINDOW_CLOSE_DELAY)
            return

    if player.lives <= 0:
        player.state = "stop"
        player.hideturtle()
        for enemy in enemies:
            enemy.state = "stop"
        lives_pen.hide()
        elapsed = time.monotonic() - game_stats["start_time"]
        game_stats["total_score"] = player.score
        popup.show_game_over(game_stats, elapsed)
        screen.update()
        screen.ontimer(screen.bye, WINDOW_CLOSE_DELAY)
        return

    screen.update()
    screen.ontimer(
        lambda: game_loop(
            screen,
            player,
            score_pen,
            lives_pen,
            pellet_pen,
            power_pen,
            enemies,
            popup,
            wall_pen,
            current_level,
            player_start,
            ghost_starts,
            asset_paths,
        ),
        1000 // FPS,
    )


def main(arguments: Sequence[str] | None = None) -> None:
    """Проверяет данные, создаёт объекты и запускает игру.

    Аргументы:
        arguments: Необязательные аргументы командной строки.

    Исключения:
        AssetError: Графические ресурсы отсутствуют или повреждены.
        MazeValidationError: Хотя бы одна карта некорректна.
    """
    parsed_arguments = parse_arguments(arguments)
    asset_paths = resolve_asset_paths(parsed_arguments.assets_dir)
    validate_all_mazes()

    screen = init_screen()
    register_shapes(screen, asset_paths)
    reset_game_stats()

    wall_pen = Wall(asset_paths[WALL_SHAPE_NAME])
    pellet_pen = Pellet()
    power_pen = PowerPellet(asset_paths[POWER_PELLET_SHAPE_NAME])
    score_pen = ScorePen()
    lives_pen = LivesPen()
    popup = GameOverPopup()

    current_level = 0
    enemy_count = ENEMY_NUMBER_PER_LEVEL[current_level]
    walls, pellets, power_pellets, player_start, ghost_starts = calculate_maze_data(
        ALL_MAZES[current_level], enemy_count
    )

    wall_pen.walls = walls
    pellet_pen.pellets = pellets
    power_pen.power_pellets = power_pellets
    wall_pen.draw()
    pellet_pen.draw()
    power_pen.draw()

    player_shapes = {key: asset_paths[name] for key, name in PLAYER_SHAPE_NAMES.items()}
    player = Player(walls, player_shapes)
    player.goto(player_start)
    enemies = create_enemies(
        walls,
        player,
        ghost_starts,
        enemy_count,
        asset_paths,
    )

    screen.ontimer(
        lambda: bind_controls(screen, player),
        CHARACTER_START_DELAY,
    )
    for enemy in enemies:
        screen.ontimer(enemy.start_move, CHARACTER_START_DELAY)

    game_loop(
        screen,
        player,
        score_pen,
        lives_pen,
        pellet_pen,
        power_pen,
        enemies,
        popup,
        wall_pen,
        current_level,
        player_start,
        ghost_starts,
        asset_paths,
    )
    screen.mainloop()


if __name__ == "__main__":
    try:
        main()
    except (AssetError, MazeValidationError, ValueError, IndexError) as error:
        print(f"Ошибка запуска игры: {error}")
    except turtle.Terminator:
        pass
