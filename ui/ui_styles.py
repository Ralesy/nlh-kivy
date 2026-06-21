#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI Styles: переиспользуемые компоненты и цветовая схема для красивого интерфейса.
"""

import os

from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.metrics import dp

# Repo root (ui/ui_styles.py -> ui/ -> project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUTTONS_DIR = os.path.join(PROJECT_ROOT, "assets", "ui", "buttons")
BACKGROUNDS_DIR = os.path.join(PROJECT_ROOT, "assets", "backgrounds")


# ============================================================================
# ЦВЕТОВАЯ ПАЛИТРА - Натуральные, земляные тона
# ============================================================================

COLORS = {
    # Основные нейтральные цвета
    'dark_bg': (0.08, 0.07, 0.06, 1),           # Тёмный фон
    'panel': (0.20, 0.17, 0.14, 0.97),          # Панели
    'panel_light': (0.28, 0.24, 0.20, 0.97),    # Светлые панели

    # Золотой акцент
    'gold_light': (0.95, 0.82, 0.40, 1),        # Светлое золото
    'gold': (0.85, 0.70, 0.30, 1),              # Основное золото
    'gold_dark': (0.65, 0.55, 0.20, 1),         # Тёмное золото

    # Зелень
    'green_leaf': (0.50, 0.60, 0.40, 1),        # Листва
    'green_moss': (0.40, 0.45, 0.30, 1),        # Мох
    'green_dark': (0.30, 0.35, 0.25, 1),        # Тёмная зелень

    # Камень
    'stone_light': (0.50, 0.47, 0.43, 1),       # Светлый камень
    'stone': (0.40, 0.37, 0.34, 1),             # Серый камень
    'stone_dark': (0.30, 0.28, 0.26, 1),        # Тёмный камень

    # Акценты действий
    'hp_red': (0.75, 0.35, 0.30, 1),            # Красный (здоровье)
    'hp_green': (0.55, 0.65, 0.40, 1),          # Зелёный
    'mana_blue': (0.40, 0.55, 0.65, 1),         # Синий (мана)
    'xp_purple': (0.60, 0.45, 0.55, 1),         # Фиолетовый (опыт)

    # Текст
    'text_light': (0.95, 0.92, 0.85, 1),        # Светлый текст
    'text_dark': (0.12, 0.11, 0.10, 1),         # Тёмный текст

    # Граница
    'border_gold': (0.85, 0.75, 0.45, 0.8),     # Золотая граница

    # Эффекты
    'shadow': (0, 0, 0, 0.5),                   # Тень
    'glow': (0.85, 0.75, 0.45, 0.3),            # Свечение
}


# ============================================================================
# СТИЛИЗОВАННЫЕ КОМПОНЕНТЫ
# ============================================================================

class StyledButton(Button):
    """Dark RPG кнопка с темным фоном и золотой рамкой."""

    def __init__(self, text="Button", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.font_size = kwargs.get('font_size', dp(18))
        self.bold = True
        self.color = COLORS['text_light']
        self.halign = 'center'
        self.valign = 'middle'

        self.button_bg_color = (0.1, 0.1, 0.12, 0.9)
        self.button_border_color = (0.7, 0.55, 0.3, 0.6)
        self.pressed = False

        self._update_canvas()
        self.bind(
            pos=lambda i, v: self._update_canvas(),
            size=lambda i, v: self._update_canvas()
        )

    def _update_canvas(self):
        """Отрендерить кнопку с темным фоном и золотой рамкой."""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.button_bg_color)
            RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(6)]
            )
            Color(*self.button_border_color)
            Line(
                rounded_rectangle=(
                    self.x, self.y, self.width, self.height, dp(6)
                ),
                width=dp(1.2)
            )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.pressed = True
            self.button_bg_color = (0.15, 0.15, 0.2, 1)
            self.button_border_color = (0.9, 0.7, 0.4, 0.8)
            self._update_canvas()
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.pressed:
            self.pressed = False
            self.button_bg_color = (0.1, 0.1, 0.12, 0.9)
            self.button_border_color = (0.7, 0.55, 0.3, 0.6)
            self._update_canvas()
        return super().on_touch_up(touch)


class StyledLabel(Label):
    """Стилизованная метка с тенью и иерархией."""

    def __init__(self, text="", color=None, font_size=dp(18),
                 bold=True, shadow=True, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.color = color or COLORS['text_light']
        self.font_size = font_size
        self.bold = bold
        self.shadow = shadow

        # Добавляем тень для лучшей читаемости
        if shadow:
            self.shadow_offset = (dp(1), -dp(1))
            self.shadow_color = (0, 0, 0, 0.7)


class StyledPanel(BoxLayout):
    """Современная панель с закруглёнными углами и текстурой."""

    def __init__(self, title="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(16)  # Отступы
        self.spacing = dp(12)  # Промежутки

        # Фон панели
        with self.canvas.before:
            # Тень под панелью
            Color(*COLORS['shadow'])
            self._shadow_rect = RoundedRectangle(
                pos=(self.x + dp(3), self.y - dp(3)),
                size=self.size,
                radius=[dp(10)]
            )

            # Основной фон
            Color(*COLORS['panel'])
            self._bg_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(10)]
            )

            # Граница
            Color(*COLORS['border_gold'])
            self._border_line = Line(
                rounded_rectangle=(
                    self.x, self.y, self.width, self.height, dp(10)
                ),
                width=dp(1.5)
            )

        self.bind(
            pos=lambda i, v: self._update_canvas(),
            size=lambda i, v: self._update_canvas()
        )

        # Заголовок если передан
        if title:
            header = BoxLayout(
                size_hint_y=None,
                height=dp(40),
                padding=(dp(10), 0)
            )

            # Текст заголовка
            title_label = StyledLabel(
                text=title,
                font_size=dp(22),
                color=COLORS['gold_light'],
                bold=True,
                halign='center',
                valign='middle'
            )
            header.add_widget(title_label)
            self.add_widget(header)

            # Разделитель
            with header.canvas.before:
                Color(*COLORS['border_gold'])
                Line(
                    points=[header.x, header.y, header.right, header.y],
                    width=dp(1.5)
                )

    def _update_canvas(self):
        """Обновить элементы canvas при изменении размера или позиции."""
        self._shadow_rect.pos = (self.x + dp(3), self.y - dp(3))
        self._shadow_rect.size = self.size
        self._shadow_rect.radius = [dp(10)]

        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._bg_rect.radius = [dp(10)]

        self._border_line.rounded_rectangle = (
            self.x, self.y, self.width, self.height, dp(10)
        )


class StatRow(BoxLayout):
    """Строка со статистикой (название: значение)."""

    def __init__(self, label_text="", value_text="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = dp(10)
        self.size_hint_y = None
        self.height = dp(28)

        # Левая метка (название)
        label = StyledLabel(
            text=label_text,
            font_size=dp(13),
            size_hint_x=0.5,
            color=COLORS['text_light']
        )
        self.add_widget(label)

        # Правое значение (значение)
        value = StyledLabel(
            text=value_text,
            font_size=dp(14),
            size_hint_x=0.5,
            color=COLORS['gold'],
            bold=True
        )
        self.value_label = value
        self.add_widget(value)

    def update_value(self, new_value):
        """Обновить значение на правой стороне."""
        self.value_label.text = str(new_value)


class CustomProgressBar(Widget):
    """Пользовательский прогресс-бар (не конфликт с Kivy ProgressBar)."""

    def __init__(self, max_value=100, current_value=50,
                 bar_color=None, bg_color=None, **kwargs):
        self.max_value = max_value
        self.current_value = current_value
        self.bar_color = bar_color or COLORS['hp_red']
        self.bg_color = bg_color or (0.12, 0.12, 0.12, 1)

        super().__init__(**kwargs)

        self.size_hint_y = None
        self.height = dp(20)

        with self.canvas:
            # Фон бара
            Color(*self.bg_color)
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
            # Передний план бара
            Color(*self.bar_color)
            bar_width = self._calculate_bar_width()
            self._bar_rect = Rectangle(
                pos=self.pos, size=(bar_width, self.height)
            )
            # Граница
            Color(0.5, 0.5, 0.5, 0.5)
            self._border = Line(
                rectangle=(self.x, self.y, self.width, self.height),
                width=dp(0.5)
            )

        self.bind(pos=self._update_pos, size=self._update_size)

    def __setattr__(self, name, value):
        """Переопределить setattr чтобы игнорировать странные атрибуты."""
        if name in ('max', 'min', 'value'):
            # Kivy иногда пытается установить эти атрибуты, игнорируем
            return
        super().__setattr__(name, value)

    def _calculate_bar_width(self):
        """Рассчитать ширину передней части бара."""
        if self.max_value <= 0:
            return 0
        ratio = self.current_value / self.max_value
        return self.width * max(0, min(1, ratio))

    def _update_pos(self, instance, value):
        """Обновить позицию бара."""
        self._bg_rect.pos = value
        self._bar_rect.pos = value
        self._border.rectangle = (
            self.x, self.y, self.width, self.height
        )

    def _update_size(self, instance, value):
        """Обновить размер бара."""
        self._bg_rect.size = value
        bar_width = self._calculate_bar_width()
        self._bar_rect.size = (bar_width, self.height)
        self._border.rectangle = (
            self.x, self.y, self.width, self.height
        )

    def set_value(self, current, max_val=None):
        """Обновить значение бара."""
        if max_val is not None:
            self.max_value = max_val
        self.current_value = min(current, self.max_value)
        self._update_size(self, self.size)


class StatGrid(GridLayout):
    """Сетка статистики в 2 колонки."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 2
        self.spacing = dp(15)
        self.padding = dp(10)
        self.size_hint_y = None


class PopupTitle(Label):
    """Красивый заголовок для Popup'ов."""

    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.font_size = dp(22)
        self.color = COLORS['gold']
        self.bold = True
        self.size_hint_y = None
        self.height = dp(40)


def create_styled_popup(
    title="", content_widget=None, width_hint=0.7, height_hint=0.5
):
    """Создать красивый Popup."""
    from kivy.uix.popup import Popup

    main_box = BoxLayout(
        orientation='vertical', spacing=dp(10), padding=dp(10)
    )

    # Заголовок
    title_label = PopupTitle(text=title)
    main_box.add_widget(title_label)

    # Контент
    if content_widget:
        main_box.add_widget(content_widget)

    popup = Popup(
        content=main_box,
        size_hint=(width_hint, height_hint),
        background='',
        separator_height=0
    )

    # Стилизованный фон Popup'а
    with popup.canvas.before:
        Color(*COLORS['panel'])
        popup_bg = Rectangle(pos=popup.pos, size=popup.size)
        # Граница
        Color(*COLORS['border_gold'])
        popup_border = Line(
            rectangle=(
                popup.x, popup.y, popup.width, popup.height
            ),
            width=dp(2)
        )

    def update_bg(instance, value):
        popup_bg.pos = instance.pos
        popup_bg.size = instance.size
        popup_border.rectangle = (
            instance.x, instance.y, instance.width, instance.height
        )

    popup.bind(pos=update_bg, size=update_bg)

    return popup