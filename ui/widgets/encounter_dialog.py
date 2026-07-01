#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import random
from typing import Callable, Optional

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from ui.ui_styles import COLORS


class EncounterDialog(Popup):
    def __init__(self, encounter_data: dict, **kwargs):
        super().__init__(**kwargs)
        self.encounter_data = encounter_data
        self._result_handler: Optional[Callable] = None

        self.title = f"{encounter_data.get('name', 'Столкновение')}"
        self.size_hint = (0.75, 0.55)
        self.auto_dismiss = False
        self.background = ''
        self.background_color = (0, 0, 0, 0)
        self.separator_color = (0, 0, 0, 0)

        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))

        desc = encounter_data.get("dialogue", "")
        desc_label = Label(
            text=desc,
            font_size=dp(15),
            size_hint_y=None,
            height=dp(90),
            text_size=(None, None),
            halign="center",
            valign="middle",
            color=COLORS['text_light'],
        )
        content.add_widget(desc_label)

        zone_name = encounter_data.get("zone_name", "wild")
        zone_label = Label(
            text=f"📍 {zone_name}",
            font_size=dp(12),
            size_hint_y=None,
            height=dp(24),
            color=COLORS['stone'],
        )
        content.add_widget(zone_label)

        actions_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
        )
        actions_layout.bind(minimum_height=actions_layout.setter("height"))

        actions = encounter_data.get("actions", [])
        for action in actions:
            btn = Button(
                text=action.get("label", "?"),
                size_hint_y=None,
                height=dp(48),
                font_size=dp(15),
                background_color=COLORS['stone_dark'],
                color=COLORS['gold_light'],
            )
            btn._action_data = action
            btn.bind(on_press=self._on_action)
            actions_layout.add_widget(btn)

        content.add_widget(actions_layout)
        self.content = content

    def set_result_handler(self, handler: Callable) -> None:
        self._result_handler = handler

    def _resolve(self, action_id: str):
        self.dismiss()
        if self._result_handler:
            self._result_handler(action_id, self.encounter_data)

    def _on_action(self, instance: Button):
        action = getattr(instance, "_action_data", {})
        action_type = action.get("type", "")

        if action_type == "fight":
            self._resolve("fight")
        elif action_type == "flee":
            self._try_flee(action)
        elif action_type == "bribe":
            self._try_bribe(action)
        else:
            self._resolve(action.get("id", ""))

    def _try_flee(self, action: dict):
        chance = action.get("chance", 0.5)
        app = App.get_running_app()
        if app and app.game and app.game.player and hasattr(app.game.player, "skill_points_allocated"):
            speed_level = app.game.player.skill_points_allocated.get("agility", 0)
            chance += speed_level * 0.05

        if random.random() < chance:
            self._show_result("flee", "🏃 Вы успешно сбежали!", COLORS['hp_green'])
        else:
            self._show_result("fight", "Сбежать не удалось! Приготовьтесь к бою.", COLORS['hp_red'])

    def _try_bribe(self, action: dict):
        cost = action.get("cost", 50)
        app = App.get_running_app()
        if app and app.game and app.game.player and app.game.player.coins >= cost:
            app.game.player.coins -= cost
            self._show_result("bribe_success", f"Вы откупились {cost} монетами. Проход свободен.", COLORS['hp_green'])
        else:
            self._show_result("insufficient_coins", "Недостаточно монет! Попробуйте другой вариант.", COLORS['gold_dark'])

    def _show_result(self, action_id: str, text: str, color: tuple):
        if action_id == "insufficient_coins":
            self.title = "Результат"
            new_content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(20))
            label = Label(
                text=text,
                font_size=dp(16),
                text_size=(None, None),
                halign="center",
                valign="middle",
                color=color,
            )
            new_content.add_widget(label)

            btn_ok = Button(
                text="Продолжить",
                size_hint_y=None,
                height=dp(48),
                font_size=dp(16),
                background_color=COLORS['stone_dark'],
                color=COLORS['gold_light'],
            )
            btn_ok.bind(on_press=lambda x: self._restore_actions())
            new_content.add_widget(btn_ok)

            self.content = new_content
            self.size_hint = (0.6, 0.35)
            return

        self.title = "Результат"
        new_content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(20))
        label = Label(
            text=text,
            font_size=dp(16),
            text_size=(None, None),
            halign="center",
            valign="middle",
            color=color,
        )
        new_content.add_widget(label)

        btn_ok = Button(
            text="Продолжить",
            size_hint_y=None,
            height=dp(48),
            font_size=dp(16),
            background_color=COLORS['stone_dark'],
            color=COLORS['gold_light'],
        )
        btn_ok.bind(on_press=lambda x: self._resolve(action_id))
        new_content.add_widget(btn_ok)

        self.content = new_content
        self.size_hint = (0.6, 0.35)

    def _restore_actions(self):
        self.title = f"{self.encounter_data.get('name', 'Столкновение')}"
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))

        desc = self.encounter_data.get("dialogue", "")
        desc_label = Label(
            text=desc,
            font_size=dp(15),
            size_hint_y=None,
            height=dp(90),
            text_size=(None, None),
            halign="center",
            valign="middle",
            color=COLORS['text_light'],
        )
        content.add_widget(desc_label)

        zone_name = self.encounter_data.get("zone_name", "wild")
        zone_label = Label(
            text=f"📍 {zone_name}",
            font_size=dp(12),
            size_hint_y=None,
            height=dp(24),
            color=COLORS['stone'],
        )
        content.add_widget(zone_label)

        actions_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
        )
        actions_layout.bind(minimum_height=actions_layout.setter("height"))

        actions = self.encounter_data.get("actions", [])
        for action in actions:
            btn = Button(
                text=action.get("label", "?"),
                size_hint_y=None,
                height=dp(48),
                font_size=dp(15),
                background_color=COLORS['stone_dark'],
                color=COLORS['gold_light'],
            )
            btn._action_data = action
            btn.bind(on_press=self._on_action)
            actions_layout.add_widget(btn)

        content.add_widget(actions_layout)
        self.content = content
        self.size_hint = (0.75, 0.55)