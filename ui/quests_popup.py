#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QuestsPopup — всплывающее окно активных квестов слева экрана.

Стилизовано аналогично InventoryPopup: полупрозрачный фон, скролл,
список квестов с прогрессом и наградами.
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle

from ui.ui_styles import COLORS


class QuestsPopup(BoxLayout):
    """Полупрозрачное окно активных квестов (левая сторона экрана)."""

    def __init__(self, player, on_done=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(6)
        self.padding = dp(8)
        self.player = player
        self.on_done = on_done

        # Фон — тёмный полупрозрачный со скруглёнными углами
        with self.canvas.before:
            Color(0.08, 0.1, 0.15, 0.94)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*COLORS['border_gold'])
            self.border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)),
                width=dp(1.2),
            )
        self.bind(
            pos=lambda i, v: self._update_bg(),
            size=lambda i, v: self._update_bg(),
        )

        # ── Заголовок ──
        title = Label(
            text='[Квесты] АКТИВНЫЕ КВЕСТЫ',
            font_size=dp(22),
            size_hint_y=None,
            height=dp(38),
            color=(0.9, 0.8, 0.3, 1),
        )
        self.add_widget(title)

        # ── Скролл со списком квестов ──
        scroll = ScrollView(size_hint_y=1)
        self.quests_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(4),
            size_hint_y=None,
        )
        self.quests_layout.bind(minimum_height=self.quests_layout.setter('height'))
        scroll.add_widget(self.quests_layout)
        self.add_widget(scroll)

        # ── Кнопка закрытия ──
        btn_close = Button(
            text='✕ Закрыть',
            size_hint_y=None,
            height=dp(44),
            font_size=dp(16),
            background_color=(0.2, 0.22, 0.25, 1),
            color=(0.9, 0.9, 0.9, 1),
        )
        btn_close.bind(on_press=lambda _: self._close())
        self.add_widget(btn_close)

        self._build_quests()

    def _update_bg(self):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))

    def _build_quests(self):
        """Заполнить список квестов."""
        self.quests_layout.clear_widgets()

        if not self.player.accepted_quests:
            empty_label = Label(
                text="Нет активных квестов.\n"
                     "Поговорите с NPC в городе!",
                font_size=dp(16),
                size_hint_y=None,
                height=dp(60),
                halign='center',
                valign='center',
                color=(0.8, 0.8, 0.8, 1),
            )
            self.quests_layout.add_widget(empty_label)
            return

        for quest in self.player.accepted_quests:
            quest_box = BoxLayout(
                orientation='vertical',
                spacing=dp(6),
                size_hint_y=None,
                height=dp(110),
                padding=dp(8),
            )

            with quest_box.canvas.before:
                Color(0.2, 0.22, 0.28, 0.9)
                q_bg = Rectangle(pos=quest_box.pos, size=quest_box.size)
            quest_box.bind(pos=lambda i, v: setattr(q_bg, 'pos', i.pos),
                           size=lambda i, v: setattr(q_bg, 'size', i.size))

            # Заголовок
            title_lbl = Label(
                text=f"[Свиток] {quest.title.upper()}",
                font_size=dp(15),
                size_hint_y=None,
                height=dp(26),
                halign='left',
                valign='top',
                color=(0.9, 0.9, 0.3, 1),
                bold=True,
            )
            quest_box.add_widget(title_lbl)

            # Описание
            desc_lbl = Label(
                text=quest.description,
                font_size=dp(12),
                size_hint_y=None,
                height=dp(28),
                halign='left',
                valign='top',
                color=(0.8, 0.8, 0.8, 1),
            )
            quest_box.add_widget(desc_lbl)

            # Прогресс
            prog_lbl = Label(
                text=quest.progress_display(),
                font_size=dp(12),
                size_hint_y=None,
                height=dp(20),
                halign='left',
                valign='center',
                color=(0.7, 0.9, 0.7, 1),
            )
            quest_box.add_widget(prog_lbl)

            # Награда
            reward_lbl = Label(
                text=f"[Монеты] {quest.reward_gold} монет | [Опыт] {quest.reward_xp} XP",
                font_size=dp(11),
                size_hint_y=None,
                height=dp(18),
                halign='left',
                valign='center',
                color=(0.9, 0.7, 0.3, 1),
            )
            quest_box.add_widget(reward_lbl)

            self.quests_layout.add_widget(quest_box)

    def _close(self):
        if self.on_done:
            self.on_done()