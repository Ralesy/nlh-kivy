#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ActionBar - панель действий внизу экрана карты."""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp


class ActionBarButton(Button):
    """Dark RPG кнопка для ActionBar'а на карте."""

    def __init__(self, icon_path=None, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.size_hint = (None, None)
        self.size = (dp(46), dp(46))
        self.font_size = dp(18)

        with self.canvas.before:
            Color(0.05, 0.05, 0.05, 0.85)
            self._bg = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(4)]
            )
            Color(0.7, 0.55, 0.3, 0.6)
            self._border = Line(
                rounded_rectangle=(*self.pos, *self.size, dp(4)),
                width=dp(1)
            )
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.rounded_rectangle = (*self.pos, *self.size, dp(4))


class ActionBar(BoxLayout):
    """Горизонтальная панель действий внизу экрана карты."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.height = dp(60)
        self.width = dp(400)  # Will be adjusted by parent
        self.spacing = dp(12)
        self.padding = [dp(16), dp(8), dp(16), dp(8)]

        with self.canvas.before:
            Color(0.05, 0.05, 0.07, 0.8)
            self._bg = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(6)]
            )
            Color(0.7, 0.55, 0.3, 0.8)
            self._border = Line(
                points=[0, 0],
                width=dp(1)
            )
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._border.points = [
            self.x, self.top,
            self.right, self.top
        ]
        self._border.width = dp(1)