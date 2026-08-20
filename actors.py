"""Движущиеся персонажи и их взаимодействие со стенами лабиринта."""

import random
import time
import turtle
from collections.abc import Callable, Sequence

from constants import (
    CELL_SIZE,
    ENEMY_MOVE_SPEED,
    ENEMY_RADAR,
    FRIGHTENED_SPEED,
    INITIAL_LIVES,
    PLAYER_MOVE_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from mazes import Coordinate


class Actor(turtle.Turtle):
    """Базовый класс движущегося персонажа.

    Атрибуты:
        walls: Координаты стен текущего уровня.
        state: Текущее состояние движения персонажа.
        move_speed: Расстояние, проходимое за один кадр.
    """

    def __init__(self, walls: Sequence[Coordinate]) -> None:
        """Создаёт скрытого персонажа без следа при движении.

        Аргументы:
            walls: Координаты стен текущего уровня.
        """
        super().__init__(visible=False)
        self.penup()
        self.speed(0)
        self.walls = walls
        self.state = "stop"
        self.move_speed = 0

    def get_heading(self) -> int:
        """Возвращает направление движения, округлённое до целого градуса."""
        return round(self.heading())

    def check_wall_collision(self, on_wall_hit: Callable[[], None]) -> None:
        """Проверяет столкновение со стенами и корректирует положение.

        Проверка зависит от направления: при лобовом столкновении персонаж
        возвращается к краю клетки, а при движении около угла выравнивается по
        соседней свободной клетке.

        Аргументы:
            on_wall_hit: Обработчик лобового столкновения со стеной.
        """
        round_x = round(self.xcor())
        round_y = round(self.ycor())
        heading = self.get_heading()
        half_cell = round(CELL_SIZE / 2)

        for x_coordinate, y_coordinate in self.walls:
            delta_x = round_x - x_coordinate
            delta_y = round_y - y_coordinate

            if heading == 0:
                if (
                    -half_cell < delta_x + half_cell < half_cell
                    and -half_cell <= delta_y <= half_cell
                ):
                    self.setx(x_coordinate - CELL_SIZE)
                    on_wall_hit()
                elif (
                    -half_cell < delta_x + half_cell < half_cell
                    and delta_y > half_cell
                    and abs(delta_y) < CELL_SIZE
                ):
                    self.sety(y_coordinate + CELL_SIZE)
                elif (
                    -half_cell < delta_x + half_cell < half_cell
                    and delta_y < -half_cell
                    and abs(delta_y) < CELL_SIZE
                ):
                    self.sety(y_coordinate - CELL_SIZE)

            elif heading == 180:
                if (
                    -half_cell < delta_x - half_cell < half_cell
                    and -half_cell <= delta_y <= half_cell
                ):
                    self.setx(x_coordinate + CELL_SIZE)
                    on_wall_hit()
                elif (
                    -half_cell < delta_x - half_cell < half_cell
                    and delta_y > half_cell
                    and abs(delta_y) < CELL_SIZE
                ):
                    self.sety(y_coordinate + CELL_SIZE)
                elif (
                    -half_cell < delta_x - half_cell < half_cell
                    and delta_y < -half_cell
                    and abs(delta_y) < CELL_SIZE
                ):
                    self.sety(y_coordinate - CELL_SIZE)

            elif heading == 90:
                if (
                    -half_cell <= delta_x <= half_cell
                    and -half_cell < delta_y + half_cell < half_cell
                ):
                    self.sety(y_coordinate - CELL_SIZE)
                    on_wall_hit()
                elif (
                    delta_x > half_cell
                    and abs(delta_x) < CELL_SIZE
                    and -half_cell < delta_y + half_cell < half_cell
                ):
                    self.setx(x_coordinate + CELL_SIZE)
                elif (
                    delta_x < -half_cell
                    and abs(delta_x) < CELL_SIZE
                    and -half_cell < delta_y + half_cell < half_cell
                ):
                    self.setx(x_coordinate - CELL_SIZE)

            elif heading == 270:
                if (
                    -half_cell <= delta_x <= half_cell
                    and -half_cell < delta_y - half_cell < half_cell
                ):
                    self.sety(y_coordinate + CELL_SIZE)
                    on_wall_hit()
                elif (
                    delta_x > half_cell
                    and abs(delta_x) < CELL_SIZE
                    and -half_cell < delta_y - half_cell < half_cell
                ):
                    self.setx(x_coordinate + CELL_SIZE)
                elif (
                    delta_x < -half_cell
                    and abs(delta_x) < CELL_SIZE
                    and -half_cell < delta_y - half_cell < half_cell
                ):
                    self.setx(x_coordinate - CELL_SIZE)

    def _wrap_around_screen(self) -> None:
        """Переносит персонажа на противоположный край игрового поля."""
        if round(self.ycor()) > SCREEN_HEIGHT / 2 - 2 * CELL_SIZE:
            self.sety(-SCREEN_HEIGHT / 2)
        elif round(self.ycor()) < -SCREEN_HEIGHT / 2:
            self.sety(SCREEN_HEIGHT / 2 - 2 * CELL_SIZE)
        elif round(self.xcor()) < -SCREEN_WIDTH / 2:
            self.setx(SCREEN_WIDTH / 2)
        elif round(self.xcor()) > SCREEN_WIDTH / 2:
            self.setx(-SCREEN_WIDTH / 2)


class Player(Actor):
    """Управляемый игрок Пакман.

    Атрибуты:
        shapes: Изображения игрока для состояния покоя и направлений.
        lives: Количество оставшихся жизней.
        score: Текущее количество очков.
    """

    def __init__(
        self,
        walls: Sequence[Coordinate],
        shapes: dict[str, str],
    ) -> None:
        """Создаёт игрока.

        Аргументы:
            walls: Координаты стен текущего уровня.
            shapes: Зарегистрированные изображения игрока по состояниям.
        """
        super().__init__(walls)
        self.shapes = shapes
        self.shape(shapes["stop"])
        self.move_speed = PLAYER_MOVE_SPEED
        self.lives = INITIAL_LIVES
        self.score = 0
        self.showturtle()

    def move(self) -> None:
        """Перемещает игрока и обрабатывает переход через края поля."""
        if self.state != "stop":
            self.forward(self.move_speed)
            self._wrap_around_screen()

    def _on_wall_hit(self) -> None:
        """Останавливает игрока после лобового столкновения со стеной."""
        self.state = "stop"
        self.shape(self.shapes["stop"])

    def check_wall_collision(self) -> None:
        """Проверяет столкновение игрока со стенами."""
        super().check_wall_collision(self._on_wall_hit)

    def _turn(self, heading: int, shape_key: str) -> None:
        """Устанавливает направление, изображение и состояние движения.

        Аргументы:
            heading: Новое направление в градусах.
            shape_key: Ключ изображения в словаре ``shapes``.
        """
        self.setheading(heading)
        self.shape(self.shapes[shape_key])
        self.state = "move"

    def turn_right(self) -> None:
        """Поворачивает игрока вправо."""
        self._turn(0, "right")

    def turn_left(self) -> None:
        """Поворачивает игрока влево."""
        self._turn(180, "left")

    def turn_up(self) -> None:
        """Поворачивает игрока вверх."""
        self._turn(90, "up")

    def turn_down(self) -> None:
        """Поворачивает игрока вниз."""
        self._turn(270, "down")

    def reset_speed(self) -> None:
        """Возвращает базовую скорость игрока."""
        self.move_speed = PLAYER_MOVE_SPEED


class Enemy(Actor):
    """Призрак с режимами движения, преследования и испуга.

    Атрибуты:
        enemy_shape: Обычное изображение призрака.
        frightened_shape: Изображение испуганного призрака.
        player: Игрок, которого преследует призрак.
        normal_speed: Обычная скорость движения.
        is_frightened: Активен ли режим испуга.
        frightened_end_time: Момент окончания режима испуга.
    """

    def __init__(
        self,
        start_x: float,
        start_y: float,
        walls: Sequence[Coordinate],
        player: Player,
        enemy_shape: str,
        frightened_shape: str,
    ) -> None:
        """Создаёт призрака в стартовой позиции.

        Аргументы:
            start_x: Начальная координата X.
            start_y: Начальная координата Y.
            walls: Координаты стен текущего уровня.
            player: Объект игрока для логики преследования.
            enemy_shape: Зарегистрированное обычное изображение.
            frightened_shape: Зарегистрированное изображение испуга.
        """
        super().__init__(walls)
        self.enemy_shape = enemy_shape
        self.frightened_shape = frightened_shape
        self.shape(enemy_shape)
        self.goto(start_x, start_y)
        self.player = player
        self.move_speed = ENEMY_MOVE_SPEED
        self.normal_speed = ENEMY_MOVE_SPEED
        self.is_frightened = False
        self.frightened_end_time = 0.0
        self.showturtle()

    def move(self) -> None:
        """Обновляет режим испуга и перемещает призрака."""
        if self.state != "stop":
            if self.is_frightened and time.monotonic() >= self.frightened_end_time:
                self._end_frightened()
            self.forward(self.move_speed)
            self._wrap_around_screen()

    def _on_wall_hit(self) -> None:
        """Выбирает новое направление после столкновения со стеной."""
        self.start_move()

    def check_wall_collision(self) -> None:
        """Проверяет столкновение призрака со стенами."""
        super().check_wall_collision(self._on_wall_hit)

    def make_frightened(self, duration_ms: int) -> None:
        """Включает режим испуга на заданное время.

        Аргументы:
            duration_ms: Продолжительность режима в миллисекундах.

        Исключения:
            ValueError: Продолжительность не является положительной.
        """
        if duration_ms <= 0:
            raise ValueError("Продолжительность испуга должна быть положительной")
        self.is_frightened = True
        self.frightened_end_time = time.monotonic() + duration_ms / 1000
        self.shape(self.frightened_shape)
        self.move_speed = FRIGHTENED_SPEED
        self.setheading((self.get_heading() + 180) % 360)

    def _end_frightened(self) -> None:
        """Возвращает обычное изображение и скорость призрака."""
        self.is_frightened = False
        self.shape(self.enemy_shape)
        self.move_speed = self.normal_speed

    def start_move(self) -> None:
        """Выбирает случайное направление без стены в соседней клетке."""
        current_x = round(self.xcor() / CELL_SIZE) * CELL_SIZE
        current_y = round(self.ycor() / CELL_SIZE) * CELL_SIZE

        direction_cells = {
            0: (current_x + CELL_SIZE, current_y),
            180: (current_x - CELL_SIZE, current_y),
            90: (current_x, current_y + CELL_SIZE),
            270: (current_x, current_y - CELL_SIZE),
        }
        possible_headings = [
            heading
            for heading, cell in direction_cells.items()
            if cell not in self.walls
        ]

        if possible_headings:
            self.setheading(random.choice(possible_headings))
        else:
            self.setheading((self.get_heading() + 180) % 360)
        self.state = "move"

    def go_after_player(self) -> None:
        """Поворачивает к игроку, если он находится в радиусе обнаружения."""
        if self.is_frightened:
            return

        player_x = round(self.player.xcor())
        player_y = round(self.player.ycor())
        enemy_x = round(self.xcor())
        enemy_y = round(self.ycor())
        distance_to_player = self.distance(self.player)
        heading = self.get_heading()

        if heading in (0, 180) and distance_to_player <= ENEMY_RADAR:
            if (
                player_y > enemy_y
                and player_x + CELL_SIZE / 2 > enemy_x > player_x - CELL_SIZE / 2
            ):
                self.setheading(90)
            elif (
                player_y < enemy_y
                and player_x + CELL_SIZE / 2 > enemy_x > player_x - CELL_SIZE / 2
            ):
                self.setheading(270)
        elif heading in (90, 270) and distance_to_player <= ENEMY_RADAR:
            if (
                player_y + CELL_SIZE / 2 > enemy_y > player_y - CELL_SIZE / 2
                and player_x > enemy_x
            ):
                self.setheading(0)
            elif (
                player_y + CELL_SIZE / 2 > enemy_y > player_y - CELL_SIZE / 2
                and player_x < enemy_x
            ):
                self.setheading(180)

        if player_y == enemy_y and distance_to_player < ENEMY_RADAR:
            self.setheading(0 if player_x > enemy_x else 180)
        elif player_x == enemy_x and distance_to_player < ENEMY_RADAR:
            self.setheading(90 if player_y > enemy_y else 270)
