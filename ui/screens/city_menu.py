#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Меню города."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui.ui_styles import COLORS
from ui.bindings.keyboard_handler import KeyboardHandler
from ui.widgets.navigation_buttons import add_back_to_map_button

class CityMenuScreen(Screen, KeyboardHandler):
    """Меню города с казино, таверной и магазином."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20),
                           spacing=dp(15))
        
        with layout.canvas.before:
            Color(0.15, 0.2, 0.25, 1)
            self.bg_rect = Rectangle()
            layout.bind(
                size=lambda i, v: setattr(self.bg_rect, 'size', i.size),
                pos=lambda i, v: setattr(self.bg_rect, 'pos', i.pos)
            )
        
        title = Label(
            text='🏛️ ГОРОД',
            font_size=dp(32),
            size_hint_y=None,
            height=dp(80),
            bold=True,
            color=(0.95, 0.95, 0.3, 1)
        )
        layout.add_widget(title)
        
        btn_tavern = Button(
            text='🏰 Таверна',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(22),
            background_color=COLORS['stone_light']
        )
        btn_tavern.bind(on_press=self.on_tavern)
        layout.add_widget(btn_tavern)
        
        btn_shop = Button(
            text='🛒 Магазин',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(22),
            background_color=COLORS['stone_light']
        )
        btn_shop.bind(on_press=self.on_shop)
        layout.add_widget(btn_shop)
        
        # Казино было удалено — игры перенесены в таверну
        
        layout.add_widget(Widget(size_hint_y=1))

        self.add_widget(layout)

        # add edge 'Back to Map' button after layout so it's on top
        self._btn_back_map = add_back_to_map_button(self, self.manager)
        self.bind_keyboard()

    def handle_keyboard_action(self, action: str, pressed: bool = True) -> bool:
        if action in ("exit_location", "open_menu", "open_locations") and pressed:
            try:
                if getattr(self, "_btn_back_map", None):
                    self._btn_back_map.trigger_action(duration=0)
                    return True
            except Exception:
                pass
        return False
    
    def on_tavern(self, instance):
        app = App.get_running_app()
        if app.tavern_screen:
            app.tavern_screen.update_tavern()
        self.manager.current = 'tavern'
    
    def on_shop(self, instance):
        app = App.get_running_app()
        if app.shop_screen:
            app.shop_screen.update_shop()
        self.manager.current = 'shop'
    
