#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Кнопки навигации «назад на карту» и «в город» для экранов."""

from kivy.app import App
from kivy.uix.button import Button
from kivy.metrics import dp
import os
from ui.ui_styles import BUTTONS_DIR


def add_back_to_map_button(parent_widget, manager):
    """Добавить кнопку возврата на глобальную карту.

    parent_widget: экран, на который добавляется кнопка
    manager: ScreenManager (parent_widget.manager может быть None при init)
    """
    try:
        App.get_running_app()
    except Exception:
        pass

    def _go_map(btn):
        app2 = App.get_running_app()
        try:
            if getattr(app2, "game", None) and getattr(app2.game, "player", None):
                try:
                    app2.game.autosave()
                except Exception as e:
                    print(f"[DEBUG] Failed to auto-save: {e}")
        except Exception as e:
            print(f"[DEBUG] Failed to auto-save: {e}")

        if getattr(app2, "return_to_local_location", False):
            target_screen = "local_location"
        else:
            target_screen = "location_select"
            if getattr(app2, "location_select_screen", None):
                try:
                    app2.location_select_screen.update_locations()
                except Exception:
                    pass

        try:
            parent_widget.manager.current = target_screen
        except Exception:
            try:
                if getattr(app2, "sm", None):
                    app2.sm.current = target_screen
            except Exception:
                pass

    btn = Button(
        text="",
        size_hint=(None, None),
        size=(dp(56), dp(56)),
        pos_hint={"right": 0.98, "y": 0.88},
        background_normal=os.path.join(BUTTONS_DIR, "global_map.png"),
        background_down=os.path.join(BUTTONS_DIR, "global_map.png"),
        background_color=(1, 1, 1, 1),
    )
    btn.bind(on_press=_go_map)
    try:
        parent_widget.add_widget(btn)
    except Exception:
        try:
            if hasattr(parent_widget, "content_layout"):
                parent_widget.content_layout.add_widget(btn)
        except Exception:
            pass


def add_back_to_city_button(parent_widget, manager):
    """Добавить кнопку возврата в меню города."""
    try:
        App.get_running_app()
    except Exception:
        pass

    def _go_city(btn):
        app2 = App.get_running_app()
        try:
            parent_widget.manager.current = "city_menu"
        except Exception:
            try:
                if getattr(app2, "sm", None):
                    app2.sm.current = "city_menu"
            except Exception:
                pass

    btn = Button(
        text="",
        size_hint=(None, None),
        size=(dp(56), dp(56)),
        pos_hint={"right": 0.88, "y": 0.88},
        background_normal=os.path.join(BUTTONS_DIR, "city.png"),
        background_down=os.path.join(BUTTONS_DIR, "city.png"),
        background_color=(1, 1, 1, 1),
    )
    btn.bind(on_press=_go_city)
    try:
        parent_widget.add_widget(btn)
    except Exception:
        try:
            if hasattr(parent_widget, "content_layout"):
                parent_widget.content_layout.add_widget(btn)
        except Exception:
            pass
