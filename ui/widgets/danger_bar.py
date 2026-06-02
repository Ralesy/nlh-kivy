#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Виджет шкалы глобальной опасности (Danger Bar).

Отображает полоску опасности с цветовой индикацией и текстом
текущей градации. Автоматически обновляется из DangerManager.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock


# Цвета шкалы в зависимости от градации
_TIER_COLORS = {
    "Безопасно":            (0.35, 0.55, 0.30, 1),   # зелёный
    "Повышенная опасность": (0.75, 0.65, 0.20, 1),   # жёлтый/янтарный
    "Критическая опасность": (0.80, 0.35, 0.20, 1),  # оранжево-красный
    "Апокалипсис":          (0.75, 0.10, 0.10, 1),   # ярко-красный
}

_TIER_ICONS = {
    "Безопасно":            "🟢",
    "Повышенная опасность": "🟡",
    "Критическая опасность": "🟠",
    "Апокалипсис":          "🔴",
}


class DangerBar(BoxLayout):
    """Компактная полоса опасности для отображения на HUD / карте."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (None, None)
        self.size = (dp(260), dp(36))
        self.spacing = dp(4)
        self.padding = [dp(6), dp(4), dp(6), dp(4)]

        # Фон панели
        with self.canvas.before:
            Color(0.10, 0.08, 0.06, 0.88)
            self._bg = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(6)]
            )
            Color(0.55, 0.45, 0.25, 0.5)
            self._border = Line(
                rounded_rectangle=(*self.pos, *self.size, dp(6)),
                width=dp(1),
            )
        self.bind(pos=self._redraw, size=self._redraw)

        # Иконка градации
        self._icon_label = Label(
            text="🟢",
            size_hint=(None, 1),
            width=dp(28),
            font_size=dp(16),
        )
        self.add_widget(self._icon_label)

        # Контейнер для полосы (вложенный Widget с canvas)
        self._bar_container = Widget(size_hint=(1, 1))
        self.add_widget(self._bar_container)

        # Текст справа (процент + название)
        self._text_label = Label(
            text="30% Безопасно",
            size_hint=(None, 1),
            width=dp(130),
            font_size=dp(11),
            color=(0.9, 0.88, 0.8, 1),
            halign="right",
            valign="middle",
        )
        self._text_label.text_size = (dp(130), None)
        self.add_widget(self._text_label)

        # Начальные значения
        self._danger = 30.0
        self._tier = "Безопасно"
        self._bar_bg_color = Color(0.18, 0.16, 0.14, 1)
        self._bar_fg_color = Color(*_TIER_COLORS["Безопасно"])
        self._bar_bg_rect = None
        self._bar_fg_rect = None

        # Рисуем полосу внутри контейнера (отложенно, после layout)
        Clock.schedule_once(self._draw_bar, 0.01)
        self._bar_container.bind(pos=self._draw_bar, size=self._draw_bar)

        # Периодическое авто-обновление из DangerManager
        self._update_ev = Clock.schedule_interval(self._auto_update, 0.5)

    # ------------------------------------------------------------------
    # Публичные методы
    # ------------------------------------------------------------------

    def set_danger(self, danger_level: float, tier_name: str) -> None:
        """Обновить отображение опасности."""
        self._danger = max(0.0, min(100.0, danger_level))
        self._tier = tier_name

        icon = _TIER_ICONS.get(tier_name, "🟢")
        bar_color = _TIER_COLORS.get(tier_name, _TIER_COLORS["Безопасно"])

        self._icon_label.text = icon
        self._text_label.text = f"{self._danger:.0f}% {tier_name}"
        self._bar_fg_color.rgba = bar_color

        self._update_bar_width()

    # ------------------------------------------------------------------
    # Внутренние методы
    # ------------------------------------------------------------------

    def _auto_update(self, dt):
        """Автоматически считывать состояние из DangerManager."""
        try:
            app = App.get_running_app()
            dm = getattr(getattr(app, "game", None), "danger_manager", None)
            if dm is not None:
                self.set_danger(dm.danger_level, dm.tier_name)
        except Exception:
            pass

    def _draw_bar(self, *args):
        """Нарисовать фон и полосу внутри контейнера."""
        c = self._bar_container
        c.canvas.before.clear()
        with c.canvas.before:
            # Фон полосы
            Color(0.18, 0.16, 0.14, 1)
            RoundedRectangle(
                pos=c.pos, size=c.size, radius=[dp(4)]
            )
            # Заполненная часть
            ratio = self._danger / 100.0 if self._danger > 0 else 0
            fill_w = max(0, c.width * ratio)
            bar_color = _TIER_COLORS.get(self._tier, _TIER_COLORS["Безопасно"])
            Color(*bar_color)
            if fill_w > 0:
                RoundedRectangle(
                    pos=c.pos, size=(fill_w, c.height), radius=[dp(4)]
                )
            # Рамка
            Color(0.55, 0.45, 0.25, 0.4)
            Line(
                rounded_rectangle=(*c.pos, *c.size, dp(4)),
                width=dp(0.8),
            )

    def _update_bar_width(self):
        """Перерисовать полосу (вызывается при изменении danger)."""
        self._draw_bar()

    def _redraw(self, *args):
        """Обновить фон и рамку самого виджета."""
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.rounded_rectangle = (*self.pos, *self.size, dp(6))

    def cleanup(self):
        """Остановить авто-обновление (вызывать при удалении виджета)."""
        if self._update_ev:
            self._update_ev.cancel()
            self._update_ev = None