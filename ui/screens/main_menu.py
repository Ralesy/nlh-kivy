#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран главного меню."""

import sys

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui.ui_styles import StyledButton, StyledLabel, COLORS
from systems.save_system import get_save_list


class MainMenuScreen(Screen):
    """Главное меню."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(20))

        with layout.canvas.before:
            Color(*COLORS["dark_bg"])
            self.bg_rect = Rectangle()
            layout.bind(
                size=lambda i, v: setattr(self.bg_rect, "size", i.size),
                pos=lambda i, v: setattr(self.bg_rect, "pos", i.pos),
            )

        title = StyledLabel(
            text="Nameless Hero: Fears of Emberfall",
            font_size=dp(48),
            size_hint_y=None,
            height=dp(100),
            color=COLORS["gold"],
            bold=True,
        )
        layout.add_widget(title)

        button_container = AnchorLayout(anchor_x='center', anchor_y='center')
        button_layout = BoxLayout(orientation="vertical", spacing=dp(14), size_hint_y=None, size_hint_x=None, width=dp(380))
        button_layout.bind(minimum_height=button_layout.setter("height"))

        btn_continue = StyledButton(
            text="ПРОДОЛЖИТЬ",
            size_hint_y=None,
            height=dp(60),
            font_size=dp(20),
        )
        btn_continue.bind(on_press=self.on_continue_game)
        button_layout.add_widget(btn_continue)

        btn_new = StyledButton(
            text="НОВАЯ ИГРА",
            size_hint_y=None,
            height=dp(60),
            font_size=dp(20),
        )
        btn_new.bind(on_press=self.on_new_game)
        button_layout.add_widget(btn_new)

        btn_load = StyledButton(
            text="ЗАГРУЗИТЬ",
            size_hint_y=None,
            height=dp(60),
            font_size=dp(20),
        )
        btn_load.bind(on_press=self.on_load_game)
        button_layout.add_widget(btn_load)

        btn_save = StyledButton(
            text="СОХРАНИТЬ",
            size_hint_y=None,
            height=dp(60),
            font_size=dp(20),
        )
        btn_save.bind(on_press=self.on_save_game)
        button_layout.add_widget(btn_save)

        btn_exit = StyledButton(
            text="ВЫХОД",
            size_hint_y=None,
            height=dp(60),
            font_size=dp(20),
        )
        btn_exit.bind(on_press=self.on_exit)
        button_layout.add_widget(btn_exit)

        button_container.add_widget(button_layout)
        layout.add_widget(button_container)
        self.add_widget(layout)

    def on_new_game(self, instance):
        self.manager.current = "character_creation"

    def on_save_game(self, instance):
        app = App.get_running_app()
        layout = BoxLayout(orientation="vertical", spacing=12, padding=12)
        label = Label(text="Введите имя сохранения:", size_hint_y=None, height=dp(32))
        name_input = TextInput(text="", multiline=False, size_hint_y=None, height=dp(40))
        layout.add_widget(label)
        layout.add_widget(name_input)
        btn_save = Button(text="Сохранить", size_hint_y=None, height=dp(40))
        btn_cancel = Button(text="Отмена", size_hint_y=None, height=dp(40))
        btns = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=dp(40))
        btns.add_widget(btn_save)
        btns.add_widget(btn_cancel)
        layout.add_widget(btns)
        popup = Popup(title="Сохранение игры", content=layout, size_hint=(0.5, 0.35))

        def do_save(instance):
            save_name = name_input.text.strip()
            if not save_name:
                label.text = "Имя не может быть пустым!"
                return
            try:
                if getattr(app, "game", None) and getattr(app.game, "player", None):
                    ok = app.game.save_to_file(save_name)
                    if ok:
                        popup.dismiss()
                        Popup(
                            title="Успех",
                            content=Label(text=f'Игра сохранена как "{save_name}"'),
                            size_hint=(0.5, 0.3),
                        ).open()
                    else:
                        label.text = "Ошибка сохранения!"
                else:
                    label.text = "Нет активной игры для сохранения."
            except Exception as e:
                label.text = f"Ошибка: {e}"

        btn_save.bind(on_press=do_save)
        btn_cancel.bind(on_press=lambda x: popup.dismiss())
        popup.open()

    def on_continue_game(self, instance):
        """Загрузить самое свежее сохранение."""
        saves = get_save_list()
        if not saves:
            popup = Popup(
                title="Ошибка",
                content=Label(text="Нет сохранений."),
                size_hint=(0.6, 0.3),
            )
            popup.open()
            return

        most_recent_save = saves[0]
        self.manager.get_screen("load_game").load_save(most_recent_save)

    def on_load_game(self, instance):
        saves = get_save_list()
        if not saves:
            popup = Popup(
                title="Ошибка",
                content=Label(text="Нет сохранений."),
                size_hint=(0.6, 0.3),
            )
            popup.open()
            return

        self.manager.get_screen("load_game").update_saves(saves)
        self.manager.current = "load_game"

    def on_exit(self, instance):
        sys.exit(0)
