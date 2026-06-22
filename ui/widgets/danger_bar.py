#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Виджет шкалы глобальной опасности (Danger Bar).
Отображает полоску опасности с цветовой индикацией и текстом поверх неё.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock

# Премиальные чистые цвета для градаций опасности
_TIER_COLORS = {
    "Безопасно":            (0.25, 0.55, 0.25, 0.85),   # Изумрудно-зелёный
    "Повышенная опасность": (0.75, 0.55, 0.15, 0.85),   # Янтарно-жёлтый
    "Критическая опасность": (0.85, 0.35, 0.15, 0.85),  # Огненно-оранжевый
    "Апокалипсис":          (0.75, 0.10, 0.10, 0.85),   # Глубокий красный
}

class DangerBar(BoxLayout):
    """Компактная полоса опасности, стилизованная под основной HUD."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (None, None)
        self.width = dp(240)   # Оптимальная ширина для правого угла
        self.height = dp(40)  # Идеально совпадает по высоте с GameHUD
        self.padding = [dp(6), dp(6), dp(6), dp(6)]

        # Глобальный фон панели (точно такой же, как у GameHUD)
        with self.canvas.before:
            Color(0.08, 0.08, 0.1, 0.7)
            self._bg = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(4)]
            )
            Color(0.55, 0.45, 0.25, 0.5) # Золотая рамка
            self._border = Line(
                rounded_rectangle=(*self.pos, *self.size, dp(4)),
                width=dp(1.2),
            )
        self.bind(pos=self._redraw, size=self._redraw)

        # Контейнер RelativeLayout, чтобы текст лежал строго поверх полосы закраски
        self._bar_container = RelativeLayout(size_hint=(1, 1))
        
        with self._bar_container.canvas.before:
            # Внутренний фон шкалы (куда заливается цвет)
            Color(0.05, 0.05, 0.07, 0.6)
            self._bar_bg_rect = RoundedRectangle(pos=(0, 0), size=self._bar_container.size, radius=[dp(3)])
            # Сама полоса прогресса
            self._bar_fg_color = Color(0.25, 0.55, 0.25, 0.85)
            self._bar_fg_rect = RoundedRectangle(pos=(0, 0), size=(0, self._bar_container.height), radius=[dp(3)])

        # Текст по центру полосы
        self._text_label = Label(
            text="Опасность: 0%",
            font_size=dp(11),
            bold=True,
            color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        self._bar_container.add_widget(self._text_label)
        self._bar_container.bind(size=self._draw_bar)
        self.add_widget(self._bar_container)

        # Логические переменные
        self._danger = 0.0
        self._tier = "Безопасно"

        # Периодическое авто-обновление из DangerManager
        self._update_ev = Clock.schedule_interval(self._auto_update, 0.4)

    def set_danger(self, danger_level: float, tier_name: str) -> None:
        """Обновить уровень угрозы и перерисовать интерфейс."""
        self._danger = max(0.0, min(100.0, danger_level))
        self._tier = tier_name

        # Обновляем текст и цвет полосы
        self._text_label.text = f"Угроза: {self._danger:.0f}% [{tier_name}]"
        bar_color = _TIER_COLORS.get(tier_name, (0.25, 0.55, 0.25, 0.85))
        self._bar_fg_color.rgba = bar_color

        # Триггерим перерисовку заполнения
        self._draw_bar(self._bar_container, self._bar_container.size)

    def _auto_update(self, dt):
        try:
            app = App.get_running_app()
            dm = getattr(getattr(app, "game", None), "danger_manager", None)
            if dm is not None:
                self.set_danger(dm.danger_level, dm.tier_name)
        except Exception:
            pass

    def _draw_bar(self, instance, size):
        """Динамически пересчитывает ширину заполнения при изменении размеров или данных."""
        self._bar_bg_rect.size = size
        
        ratio = self._danger / 100.0
        fill_w = max(0, size[0] * ratio)
        self._bar_fg_rect.size = (fill_w, size[1])

    def _redraw(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.rounded_rectangle = (*self.pos, *self.size, dp(4))

    def cleanup(self):
        if self._update_ev:
            self._update_ev.cancel()
            self._update_ev = None