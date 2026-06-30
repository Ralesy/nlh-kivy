#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Кнопки навигации «назад на карту» и «в город» для экранов."""

from kivy.app import App
from kivy.uix.button import Button
from kivy.metrics import dp
import os
from ui.ui_styles import BUTTONS_DIR

# Экраны городского контекста (меню и проходимый город/подлокации).
_CITY_INVENTORY_ORIGINS = frozenset({"city_menu", "game_screen"})
_CITY_LOCAL_SCENES = frozenset({"city"})


def prepare_inventory_navigation(origin_screen: str) -> None:
    """Запомнить экран возврата перед открытием инвентаря (вне боя)."""
    app = App.get_running_app()
    app.inventory_return_screen = origin_screen


def _resolve_map_target(app, parent_widget):
    """Куда вести кнопку «на карту» с текущего экрана."""
    if getattr(parent_widget, "name", None) == "inventory":
        explicit = getattr(app, "inventory_return_screen", None)
        if explicit:
            return explicit

    if getattr(app, "return_to_local_location", False):
        return "local_location"

    return "location_select"


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

        target_screen = _resolve_map_target(app2, parent_widget)
        if target_screen == "location_select" and getattr(app2, "location_select_screen", None):
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
    return btn


def add_back_to_city_button(parent_widget, manager):
    """Добавить кнопку возврата в проходимый город."""
    try:
        App.get_running_app()
    except Exception:
        pass

    def _go_city(btn):
        app2 = App.get_running_app()
        from data.local_scenes import enter_local_scene

        enter_local_scene(app2, "city")

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
    return btn


def sync_inventory_city_button(city_btn) -> None:
    """Показать «в город» только если инвентарь открыт из городского контекста."""
    if city_btn is None:
        return
    app = App.get_running_app()
    origin = getattr(app, "inventory_return_screen", None)
    scene = getattr(app, "local_scene_id", None)
    in_city = origin in _CITY_INVENTORY_ORIGINS or (
        origin == "local_location" and scene in _CITY_LOCAL_SCENES
    )
    city_btn.opacity = 1 if in_city else 0
    city_btn.disabled = not in_city
