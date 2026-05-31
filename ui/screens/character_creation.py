#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран создания персонажа."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui.ui_styles import COLORS
from core.session import GameSession
from data.items import ItemDatabase


class CharacterCreationScreen(Screen):
    """Экран создания персонажа."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=dp(25), spacing=dp(20))

        with layout.canvas.before:
            Color(0.12, 0.18, 0.28, 1)
            self.bg_rect = Rectangle()
            layout.bind(
                size=lambda i, v: setattr(self.bg_rect, "size", i.size),
                pos=lambda i, v: setattr(self.bg_rect, "pos", i.pos),
            )

        title = Label(
            text="👤 Создание персонажа",
            font_size=dp(42),
            size_hint_y=None,
            height=dp(90),
            color=COLORS["gold"],
        )
        layout.add_widget(title)

        name_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(55))
        name_label = Label(
            text="Имя:",
            size_hint_x=0.3,
            font_size=dp(20),
            color=COLORS["text_light"],
        )
        name_layout.add_widget(name_label)
        self.name_input = TextInput(
            text="Герой",
            multiline=False,
            size_hint_x=0.7,
            font_size=dp(18),
            background_color=COLORS["panel"],
            foreground_color=COLORS["text_light"],
        )
        name_layout.add_widget(self.name_input)
        layout.add_widget(name_layout)

        class_label = Label(
            text="Выберите ваше прошлое(от него зависит стартовый инвентарь):",
            font_size=dp(26),
            size_hint_y=None,
            height=dp(55),
            color=COLORS["text_light"],
        )
        layout.add_widget(class_label)

        class_layout = GridLayout(cols=1, spacing=dp(12), size_hint_y=None)
        class_layout.bind(minimum_height=class_layout.setter("height"))

        self.selected_background = "squire"
        self.background_buttons = {}

        btn_noble = Button(
            text="Обедневший дворянин",
            size_hint_y=None,
            height=dp(70),
            font_size=dp(18),
            background_color=COLORS["stone_light"],
        )
        btn_noble.bind(on_press=lambda x: self.select_background("noble", btn_noble))
        class_layout.add_widget(btn_noble)
        self.background_buttons["noble"] = btn_noble

        btn_squire = Button(
            text="Оруженосец",
            size_hint_y=None,
            height=dp(70),
            font_size=dp(18),
            background_color=COLORS["stone_light"],
        )
        btn_squire.bind(on_press=lambda x: self.select_background("squire", btn_squire))
        class_layout.add_widget(btn_squire)
        self.background_buttons["squire"] = btn_squire

        btn_hunter = Button(
            text="Охотник",
            size_hint_y=None,
            height=dp(70),
            font_size=dp(18),
            background_color=COLORS["stone_light"],
        )
        btn_hunter.bind(on_press=lambda x: self.select_background("hunter", btn_hunter))
        class_layout.add_widget(btn_hunter)
        self.background_buttons["hunter"] = btn_hunter

        btn_test = Button(
            text="ТЕСТ (1000 HP/1000 DMG)",
            size_hint_y=None,
            height=dp(60),
            font_size=dp(22),
            background_color=COLORS["stone_light"],
        )
        btn_test.bind(on_press=lambda x: self.select_background("test", btn_test))
        class_layout.add_widget(btn_test)
        self.background_buttons["test"] = btn_test

        layout.add_widget(class_layout)

        btn_create = Button(
            text="🎮 Создать персонажа",
            size_hint_y=None,
            height=dp(70),
            font_size=dp(24),
            background_color=COLORS["hp_green"],
        )
        btn_create.bind(on_press=self.create_character)
        layout.add_widget(btn_create)

        btn_back = Button(
            text="← Назад",
            size_hint_y=None,
            height=dp(50),
            font_size=dp(20),
            background_color=COLORS["stone_light"],
        )
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def select_background(self, background, button):
        self.selected_background = background
        for btn in self.background_buttons.values():
            r, g, b, a = btn.background_color
            btn.background_color = (r * 0.7, g * 0.7, b * 0.7, a)
        r, g, b, a = button.background_color
        button.background_color = (r * 1.3, g * 1.3, b * 1.3, a)

    def create_character(self, instance):
        name = self.name_input.text.strip() or "Герой"

        ItemDatabase.initialize()

        if not ItemDatabase.get("w_iron_sword"):
            popup = Popup(
                title="Ошибка",
                content=Label(
                    text="Ошибка загрузки базы данных предметов!",
                ),
                size_hint=(0.6, 0.3),
            )
            popup.open()
            return

        session = GameSession()
        if self.selected_background == "test":
            session.start_test_game(name)
        else:
            session.start_new_game(name, self.selected_background)

        app = App.get_running_app()
        app.game = session
        app.bind_session_player(session.player)

        weapon_name = (
            session.player.weapon.name
            if session.player.weapon
            else "Кулаки"
        )
        armor_name = (
            session.player.armor.name
            if session.player.armor
            else "Нет"
        )
        welcome_text = (
            f"Добро пожаловать, {name}!\n\n"
            f"Вы начинаете с:\n"
            f"💰 {session.player.coins} монет\n"
            f"⚔️ {weapon_name}\n"
            f"🛡️ {armor_name}\n\n"
            f"💡 Подсказка: Посетите таверну "
            f"для квестов,\n"
            f"магазин для покупки предметов,\n"
            f"и исследуйте локации на карте!"
        )

        popup = Popup(
            title="🎮 Добро пожаловать!",
            content=Label(
                text=welcome_text,
                text_size=(None, None),
                halign="center",
                font_size=dp(18),
            ),
            size_hint=(0.8, 0.6),
        )
        popup.open()

        app2 = App.get_running_app()
        try:
            if getattr(app2, "location_select_screen", None):
                app2.location_select_screen.update_locations()
        except Exception:
            pass
        self.manager.current = "location_select"

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
