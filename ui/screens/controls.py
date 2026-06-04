#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран настроек управления.

Этот экран позволяет пользователю просматривать текущие привязки
клавиш, переназначать их и сбрасывать к значениям по умолчанию.
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp

from ui.ui_styles import StyledButton, StyledLabel, COLORS
from core.keybindings import key_manager
from ui.bindings.keyboard_handler import KeyboardHandler


class ControlsScreen(Screen, KeyboardHandler):
    """Экран управления клавишами и кнопками мыши."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "controls"
        self.build_ui()
        self.bind_keyboard()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        title = StyledLabel(
            text="Настройки управления",
            font_size=dp(36),
            color=COLORS["gold"],
            bold=True,
        )
        layout.add_widget(title)

        for action, key in key_manager.bindings.items():
            row = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(40),
            )
            row.add_widget(
                Label(
                    text=key_manager.ACTION_NAMES_RU.get(action, action),
                    size_hint_x=0.6,
                )
            )
            btn = StyledButton(text=key, size_hint_x=0.2)
            btn.bind(on_press=lambda inst, act=action: self.start_rebind(act, inst))
            row.add_widget(btn)
            layout.add_widget(row)

        reset_btn = StyledButton(
            text="Сбросить к умолчанию",
            color=COLORS["hp_red"],
            size_hint_y=None,
            height=dp(50),
        )
        reset_btn.bind(on_press=self.reset_bindings)
        layout.add_widget(reset_btn)

        back_btn = StyledButton(
            text="Назад",
            color=COLORS["stone_light"],
            size_hint_y=None,
            height=dp(50),
        )
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def handle_keyboard_action(self, action: str, pressed: bool = True) -> bool:
        if action == "menu_equip":
            self.go_back()
            return True
        return False

    def go_back(self, *args):
        self.manager.current = "main_menu"

    def reset_bindings(self, *args):
        key_manager.reset_to_defaults()
        self.clear_widgets()
        self.build_ui()

    def start_rebind(self, action: str, button: Button):
        def on_key_down(window, key, scancode, codepoint, modifiers):
            key_name = codepoint.lower() if codepoint else str(key)
            key_manager.set_binding(action, key_name)
            button.text = key_name
            window.unbind(on_key_down=on_key_down)
            return True

        from kivy.core.window import Window
        Window.bind(on_key_down=on_key_down)