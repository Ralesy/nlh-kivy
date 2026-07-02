#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HireDialoguePopup — всплывающее окно найма спутника.

Стилизовано аналогично NpcDialoguePopup.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line

from ui.ui_styles import COLORS


class _HireButton(Button):
    """Стилизованная кнопка для диалога найма."""

    def __init__(self, text="", bg_color=None, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.text = text
        self.font_size = dp(13)
        self.size_hint_y = None
        self.height = dp(42)
        self.background_normal = ''
        self.background_down = ''
        self.bold = True
        self.color = (1, 1, 1, 1)
        self._bg_color = bg_color or (0.25, 0.30, 0.40, 0.9)
        self._update_canvas()
        self.bind(pos=lambda i, v: self._update_canvas(), size=lambda i, v: self._update_canvas())

    def _update_canvas(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
            Color(0.4, 0.35, 0.25, 0.5)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(4)), width=dp(1))


class HireDialoguePopup(BoxLayout):
    """Окно найма спутника с историей и ценой."""

    def __init__(self, npc_name, hire_cost, on_hire, on_leave, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(6)
        self.padding = dp(10)

        # Фон
        with self.canvas.before:
            Color(0.08, 0.1, 0.15, 0.94)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*COLORS.get('border_gold', (0.6, 0.5, 0.3, 0.6)))
            self.border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)),
                width=dp(1.2),
            )
        self.bind(
            pos=lambda i, v: self._update_bg(),
            size=lambda i, v: self._update_bg(),
        )

        # Имя NPC
        npc_label = Label(
            text=npc_name,
            font_size=dp(20),
            size_hint_y=None, height=dp(36),
            color=COLORS.get("gold_light", (0.9, 0.8, 0.5, 1)),
            bold=True,
        )
        self.add_widget(npc_label)

        # История (в ScrollView, чтобы текст не вылезал)
        story_text = (
            f"Меня не хотят брать в городскую стражу, "
            f"но я мечтаю стать воином. "
            f"Возьмёшь меня к себе в отряд? "
            f"В качестве оплаты мне хватит всего {hire_cost} монет."
        )
        story_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(110),
            padding=(dp(4), dp(2)),
        )
        story_label = Label(
            text=story_text,
            font_size=dp(14),
            size_hint_y=None,
            color=(0.85, 0.85, 0.85, 1),
            halign='left', valign='top',
        )
        story_label.bind(
            width=lambda *_: setattr(story_label, 'text_size', (story_label.width, None))
        )
        story_label.bind(texture_size=lambda *_: setattr(
            story_label, 'height', story_label.texture_size[1] + dp(8)
        ))
        story_container.add_widget(story_label)
        story_scroll = ScrollView(size_hint_y=None, height=dp(110))
        story_scroll.add_widget(story_container)
        self.add_widget(story_scroll)

        # Кнопки
        btn_hire = _HireButton(
            text=f"[Нанять] {hire_cost} монет",
            bg_color=(0.35, 0.55, 0.30, 0.9),
        )
        btn_hire.bind(on_press=lambda _: on_hire())
        self.add_widget(btn_hire)

        btn_leave = _HireButton(
            text="[Уйти]",
            bg_color=(0.30, 0.25, 0.25, 0.9),
        )
        btn_leave.bind(on_press=lambda _: on_leave())
        self.add_widget(btn_leave)

        spacer = BoxLayout(size_hint_y=1)
        self.add_widget(spacer)

    def _update_bg(self):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))