"""Отрисовка лабиринта, интерфейса и итоговой статистики игры."""

import turtle
from collections.abc import Mapping, Sequence

from constants import CELL_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH
from mazes import Coordinate

Font = tuple[str, int, str]


def format_elapsed_time(elapsed: float) -> str:
    """Преобразует продолжительность игры в строку ``минуты:секунды``.

    Аргументы:
        elapsed: Продолжительность игры в секундах.

    Возвращает:
        Время с двузначным количеством секунд.

    Исключения:
        ValueError: Продолжительность отрицательна.
    """
    if elapsed < 0:
        raise ValueError("Продолжительность игры не может быть отрицательной")
    minutes, seconds = divmod(int(elapsed), 60)
    return f"{minutes}:{seconds:02d}"


class Pen(turtle.Turtle):
    """Базовое перо для неподвижных игровых объектов."""

    def __init__(self) -> None:
        """Создаёт скрытое перо без следа при перемещении."""
        super().__init__(visible=False)
        self.penup()
        self.color("silver")
        self.speed(0)


class Wall(Pen):
    """Перо для стен лабиринта.

    Атрибуты:
        walls: Координаты стен текущего уровня.
    """

    def __init__(self, shape: str) -> None:
        """Создаёт перо для стен.

        Аргументы:
            shape: Имя зарегистрированного изображения стены.
        """
        super().__init__()
        self.shape(shape)
        self.walls: Sequence[Coordinate] = ()

    def draw(self) -> None:
        """Удаляет старые стены и рисует стены текущего уровня."""
        self.clear()
        self.clearstamps()
        for coordinate in self.walls:
            self.goto(coordinate)
            self.stamp()


class Pellet(Pen):
    """Перо для обычных точек.

    Атрибуты:
        pellets: Координаты точек текущего уровня.
        stamps: Соответствие координаты идентификатору отпечатка.
    """

    def __init__(self) -> None:
        """Создаёт перо с маленькой круглой формой точки."""
        super().__init__()
        self.shape("circle")
        self.shapesize(0.25, 0.25)
        self.pencolor("white")
        self.fillcolor("gold")
        self.pellets: Sequence[Coordinate] = ()
        self.stamps: dict[Coordinate, int] = {}

    def draw(self) -> None:
        """Удаляет старые точки и рисует точки текущего уровня."""
        self.clear()
        self.clearstamps()
        self.stamps.clear()
        for coordinate in self.pellets:
            self.goto(coordinate)
            self.stamps[coordinate] = self.stamp()


class PowerPellet(Pen):
    """Перо для усилителей.

    Атрибуты:
        power_pellets: Координаты усилителей текущего уровня.
        stamps: Соответствие координаты идентификатору отпечатка.
    """

    def __init__(self, shape: str) -> None:
        """Создаёт перо для усилителей.

        Аргументы:
            shape: Имя зарегистрированного изображения усилителя.
        """
        super().__init__()
        self.shape(shape)
        self.power_pellets: Sequence[Coordinate] = ()
        self.stamps: dict[Coordinate, int] = {}

    def draw(self) -> None:
        """Удаляет старые усилители и рисует усилители текущего уровня."""
        self.clear()
        self.clearstamps()
        self.stamps.clear()
        for coordinate in self.power_pellets:
            self.goto(coordinate)
            self.stamps[coordinate] = self.stamp()


class UiPen(Pen):
    """Базовое перо текстового интерфейса.

    Атрибуты:
        font: Параметры шрифта для turtle.
    """

    def __init__(self) -> None:
        """Создаёт перо со шрифтом интерфейса."""
        super().__init__()
        self.font: Font = ("Calibri", 25, "normal")


class ScorePen(UiPen):
    """Перо для счёта в левой части интерфейса."""

    def write_score(self, score: int) -> None:
        """Выводит текущее количество очков.

        Аргументы:
            score: Текущий счёт игрока.
        """
        self.clear()
        self.goto(-0.7 * SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 2 * CELL_SIZE)
        self.write(f"Score: {score}", align="left", font=self.font)


class LivesPen(UiPen):
    """Перо для жизней в правой части интерфейса."""

    def write_lives(self, lives: int) -> None:
        """Выводит количество оставшихся жизней.

        Аргументы:
            lives: Количество жизней игрока.
        """
        self.clear()
        self.goto(0.7 * SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 2 * CELL_SIZE)
        self.write(f"Lives: {lives}", align="right", font=self.font)

    def hide(self) -> None:
        """Удаляет надпись о жизнях после завершения игры."""
        self.clear()


class GameOverPopup(Pen):
    """Перо итогового окна со статистикой.

    Атрибуты:
        font_title: Шрифт заголовка результата.
        font_stats: Шрифт строк статистики.
    """

    def __init__(self) -> None:
        """Создаёт итоговое перо и настраивает шрифты."""
        super().__init__()
        self.font_title: Font = ("Calibri", 40, "bold")
        self.font_stats: Font = ("Calibri", 16, "normal")

    def _draw_box(
        self,
        title: str,
        title_color: str,
        lines: Sequence[str],
    ) -> None:
        """Рисует итоговое окно и строки статистики.

        Аргументы:
            title: Заголовок результата игры.
            title_color: Цвет заголовка в формате turtle.
            lines: Строки статистики.
        """
        box_width = 450
        line_height = 35
        box_height = 120 + len(lines) * line_height
        half_width = box_width / 2
        half_height = box_height / 2

        self.clear()
        self.pensize(3)
        self.pencolor("white")
        self.fillcolor("gray20")
        self.goto(-half_width, half_height)
        self.pendown()
        self.begin_fill()
        for coordinate in (
            (half_width, half_height),
            (half_width, -half_height),
            (-half_width, -half_height),
            (-half_width, half_height),
        ):
            self.goto(coordinate)
        self.end_fill()
        self.penup()

        self.color(title_color)
        self.goto(0, half_height - 65)
        self.write(title, align="center", font=self.font_title)

        self.color("white")
        y_position = half_height - 105
        for line in lines:
            self.goto(0, y_position)
            self.write(line, align="center", font=self.font_stats)
            y_position -= line_height

    def _show_result(
        self,
        title: str,
        title_color: str,
        stats: Mapping[str, int | float],
        elapsed: float,
    ) -> None:
        """Подготавливает общие строки статистики и показывает результат.

        Аргументы:
            title: Заголовок результата игры.
            title_color: Цвет заголовка.
            stats: Накопленная игровая статистика.
            elapsed: Продолжительность игры в секундах.

        Исключения:
            KeyError: В статистике отсутствует обязательный показатель.
            ValueError: Продолжительность игры отрицательна.
        """
        lines = (
            f"Game runtime: {format_elapsed_time(elapsed)}",
            f"Score: {stats['total_score']}",
            f"Collected pellets: {stats['pellets_eaten']}",
            f"Power pellets: {stats['power_pellets_eaten']}",
            f"Ghosts defeated: {stats['ghosts_defeated']}",
        )
        self._draw_box(title, title_color, lines)

    def show_game_over(
        self,
        stats: Mapping[str, int | float],
        elapsed: float,
    ) -> None:
        """Показывает окно поражения.

        Аргументы:
            stats: Накопленная игровая статистика.
            elapsed: Продолжительность игры в секундах.
        """
        self._show_result("GAME OVER", "red", stats, elapsed)

    def show_win(
        self,
        stats: Mapping[str, int | float],
        elapsed: float,
    ) -> None:
        """Показывает окно победы.

        Аргументы:
            stats: Накопленная игровая статистика.
            elapsed: Продолжительность игры в секундах.
        """
        self._show_result("YOU WIN!", "yellow", stats, elapsed)
