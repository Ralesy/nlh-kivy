#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Всплывающее окно повышения уровня."""

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp


class LevelUpPopup(Popup):
    """Окно повышения уровня с очками навыков."""

    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self._player = player
        self.title = f"🎉 Уровень повышен! (Ур. {player.level})"
        self.size_hint = (0.7, 0.5)
        self.auto_dismiss = False

        content = BoxLayout(orientation='vertical', spacing=dp(15), padding=dp(20))
        msg = (
            f"Поздравляем! Вы достигли {player.level} уровня!\n\n"
            f"Доступно очков навыков: {getattr(player, 'skill_points_available', 0)}"
        )
        content.add_widget(Label(
            text=msg,
            text_size=(dp(300), None),
            halign='center',
            valign='middle',
            font_size=dp(18),
        ))
        btn = Button(
            text='Отлично!',
            size_hint=(None, None),
            size=(dp(200), dp(50)),
            pos_hint={'center_x': 0.5},
        )
        btn.bind(on_press=self._on_close)
        content.add_widget(btn)
        self.content = content

    def _on_close(self, *args):
        self.dismiss()

    def on_open(self):
        try:
            app = App.get_running_app()
            screen = getattr(app, 'local_location_screen', None)
            if screen:
                screen.pause_game()
        except Exception:
            pass

    def on_dismiss(self):
        try:
            app = App.get_running_app()
            screen = getattr(app, 'local_location_screen', None)
            if screen:
                Clock.schedule_once(lambda dt: screen.resume_game(), 0.02)
        except Exception:
            pass