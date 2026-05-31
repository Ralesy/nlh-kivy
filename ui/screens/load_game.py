#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран загрузки игры."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp

from ui.ui_styles import COLORS
from core.session import GameSession


class LoadGameScreen(Screen):
    """Экран загрузки игры."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(20))

        title = Label(
            text="💾 Загрузка игры",
            font_size=dp(36),
            size_hint_y=None,
            height=dp(80),
        )
        layout.add_widget(title)

        scroll = ScrollView()
        self.save_list = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        self.save_list.bind(minimum_height=self.save_list.setter("height"))
        scroll.add_widget(self.save_list)
        layout.add_widget(scroll)

        btn_back = Button(
            text="← Назад",
            size_hint_y=None,
            height=dp(50),
            font_size=dp(20),
        )
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def update_saves(self, saves):
        self.save_list.clear_widgets()
        for save_name in saves:
            btn = Button(
                text=save_name,
                size_hint_y=None,
                height=dp(55),
                font_size=dp(21),
                background_color=COLORS["stone_light"],
            )
            btn.bind(on_press=lambda x, name=save_name: self.load_save(name))
            self.save_list.add_widget(btn)

    def load_save(self, save_name):
        session = GameSession()
        if session.load_from_file(save_name):
            app = App.get_running_app()
            app.game = session
            app.bind_session_player(session.player)
            try:
                if getattr(app, "location_select_screen", None):
                    app.location_select_screen.update_locations()
            except Exception:
                pass
            self.manager.current = "location_select"
        else:
            popup = Popup(
                title="Ошибка",
                content=Label(text="Ошибка загрузки."),
                size_hint=(0.6, 0.3),
            )
            popup.open()

    def on_back(self, instance):
        try:
            app = App.get_running_app()
            if getattr(app, "hud", None):
                try:
                    app.hud.unbind_player()
                except Exception:
                    app.hud.opacity = 0
        except Exception:
            pass
        self.manager.current = "main_menu"
