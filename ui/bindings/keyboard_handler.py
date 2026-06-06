#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mixin для обработки клавиатурных нажатий на экранах игры.
Подключает KeyBindingManager и предоставляет единый интерфейс.

Включает:
- Глобальную привязку on_key_down/on_key_up к Window
- Словарь нажатых клавиш (_kb_pressed_global)
- Преобразование scancode/keycode -> имя
"""

from kivy.core.window import Window
from core.keybindings import key_manager


_kb_pressed_global = {}
_keyboard_bound = False


def _keycode_to_char(keycode) -> str:
    """Преобразовать Kivy keycode int в символ."""
    mapping = {
        97: "a", 98: "b", 99: "c", 100: "d", 101: "e", 102: "f",
        103: "g", 104: "h", 105: "i", 106: "j", 107: "k", 108: "l",
        109: "m", 110: "n", 111: "o", 112: "p", 113: "q", 114: "r",
        115: "s", 116: "t", 117: "u", 118: "v", 119: "w", 120: "x",
        121: "y", 122: "z",
    }
    return mapping.get(keycode, "")


def _keycode_to_name(keycode) -> str:
    if not keycode:
        return ""
    if isinstance(keycode, (tuple, list)) and len(keycode) >= 2:
        return str(keycode[1]).lower()
    if isinstance(keycode, str):
        return keycode.lower()
    if isinstance(keycode, int):
        return _keycode_to_char(keycode)
    return str(keycode).lower()


def _resolve_action_from_event(keycode, scancode, codepoint):
    key_str = None
    action = None

    if codepoint and isinstance(codepoint, str):
        cp = codepoint.lower()
        action = key_manager.get_action_for_key(cp)
        key_str = cp

    if not action:
        kc = _keycode_to_name(keycode)
        if kc:
            action = key_manager.get_action_for_key(kc)
            key_str = kc

    if not action and scancode:
        sc = _scancode_to_keyname(scancode)
        if sc:
            action = key_manager.get_action_for_key(sc)
            key_str = sc

    return action, key_str



def _scancode_to_keyname(scancode) -> str:
    """Преобразовать Kivy scancode в строковое имя клавиши."""
    mapping = {
        27: "escape",
        13: "enter",
        271: "enter",
        8: "backspace",
        9: "tab",
        32: "space",
        273: "up",
        274: "down",
        275: "right",
        276: "left",
        285: "f5",
        289: "f9",
    }
    return mapping.get(scancode, "")


def _get_screen_manager(app):
    """Получить ScreenManager из приложения (root может быть FloatLayout или ScreenManager)."""
    if app is None:
        return None
    root = getattr(app, 'root', None)
    if root is None:
        return None
    # Если root сам является ScreenManager
    if hasattr(root, 'current') and hasattr(root, 'get_screen'):
        return root
    # Иначе ищем ScreenManager среди дочерних виджетов (root — FloatLayout)
    for child in getattr(root, 'children', []):
        if hasattr(child, 'current') and hasattr(child, 'get_screen'):
            return child
    return None


def _global_key_down(window, keycode, scancode, codepoint, modifiers):
    """Глобальный обработчик key_down - вызывает handle_keyboard_action текущего экрана."""
    global _kb_pressed_global, _keyboard_bound

    action, key_str = _resolve_action_from_event(keycode, scancode, codepoint)

    if key_str:
        _kb_pressed_global[key_str] = True

    if action:
        try:
            from kivy.app import App
            app = App.get_running_app()
            sm = _get_screen_manager(app)
            if sm:
                screen = sm.get_screen(sm.current)
                if screen and hasattr(screen, 'handle_keyboard_action'):
                    return screen.handle_keyboard_action(action, pressed=True)
        except Exception:
            pass
    return False


def _global_key_up(window, keycode, *args):
    """Глобальный обработчик key_up - сбрасывает состояние клавиши."""
    global _kb_pressed_global

    scancode = args[0] if len(args) >= 1 else None
    action, key_str = _resolve_action_from_event(keycode, scancode, None)

    if key_str:
        _kb_pressed_global[key_str] = False

    handled = False
    if action:
        try:
            from kivy.app import App
            app = App.get_running_app()
            sm = _get_screen_manager(app)
            if sm:
                screen = sm.get_screen(sm.current)
                if screen and hasattr(screen, "handle_keyboard_action"):
                    handled = bool(screen.handle_keyboard_action(action, pressed=False))
        except Exception:
            pass
    return handled


class KeyboardHandler:
    """Mixin-класс для экранов Kivy."""

    def bind_keyboard(self) -> None:
        """Привязать обработчики клавиш (глобально)."""
        global _keyboard_bound
        if not _keyboard_bound:
            Window.bind(on_key_down=_global_key_down)
            Window.bind(on_key_up=_global_key_up)
            _keyboard_bound = True

    def unbind_keyboard(self) -> None:
        """Отвязать обработчики клавиш (не используется - глобальные работают всегда)."""
        pass

    def is_key_pressed(self, key_name: str) -> bool:
        """Проверить, зажата ли клавиша с данным именем."""
        return _kb_pressed_global.get(key_name, False)

    def handle_keyboard_action(self, action: str, pressed: bool = True) -> bool:
        """
        Обработать действие.
        Должен быть переопределён в конкретном экране.
        Возвращает True если действие обработано.
        """
        return False
