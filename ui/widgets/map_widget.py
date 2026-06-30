#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Виджет карты локаций на игровом экране."""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui.ui_styles import COLORS

class MapWidget(BoxLayout):
    """Интерактивная карта локаций."""
    
    LOCATION_INFO = {
        'forest': {
            'name': 'Лес Криволесье',
            'desc': 'Легкие враги\nСобытия',
            'difficulty': 'Легко',
            'color': (0.45, 0.33, 0.20, 1),
            'pos': (-100, 100)
        },
        'swamp': {
            'name': '[Болото] Болота Гниющие Топи',
            'desc': 'Средние враги\nТопи',
            'difficulty': 'Средне',
            'color': (0.40, 0.30, 0.20, 1),
            'pos': (-100, 0)
        },
        'mines': {
            'name': '[Шахты] Шахты Подскальные Гроты',
            'desc': 'Сложные враги\nСокровища',
            'difficulty': 'Сложно',
            'color': (0.38, 0.28, 0.18, 1),
            'pos': (100, 0)
        },
        'mountains': {
            'name': '[Горы] Горы Хребет Драконов',
            'desc': 'Очень сложные враги\nДраконы',
            'difficulty': 'Очень сложно',
            'color': (0.47, 0.34, 0.22, 1),
            'pos': (100, 100)
        },
    }
    
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.orientation = 'vertical'
        self.spacing = dp(8)
        self.padding = dp(12)
        self._buttons = {}
        self._base_colors = {}
        self._selected_loc_id = None
        
        with self.canvas.before:
            Color(0.15, 0.2, 0.15, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self.update_bg, size=self.update_bg)
        
        map_title = Label(
            text='КАРТА МИРА',
            font_size=dp(20),
            size_hint_y=None,
            height=dp(35),
            color=COLORS['gold']
        )
        self.add_widget(map_title)
        
        locations_layout = BoxLayout(orientation='vertical', spacing=dp(8))
        
        for loc_id in ['forest', 'swamp', 'mines', 'mountains']:
            info = self.LOCATION_INFO[loc_id]
            loc_box = BoxLayout(orientation='vertical', spacing=dp(3), size_hint_y=None, height=dp(90))
            
            btn = Button(
                text=f"{info['name']}\n{info['desc']}\n"
                     f"Сложность: {info['difficulty']}",
                font_size=dp(18),
                background_color=info['color'],
                size_hint_y=None,
                height=dp(85)
            )
            btn.bind(on_press=lambda x, loc=loc_id: self.game_screen.enter_location(loc))
            loc_box.add_widget(btn)
            locations_layout.add_widget(loc_box)
            self._buttons[loc_id] = btn
            self._base_colors[loc_id] = info['color']
        
        self.add_widget(locations_layout)

    def get_location_ids(self):
        return list(self._buttons.keys())

    def set_selected_location(self, loc_id):
        self._selected_loc_id = loc_id
        for lid, btn in self._buttons.items():
            base = self._base_colors.get(lid, (1, 1, 1, 1))
            if lid == loc_id:
                btn.background_color = (
                    min(base[0] * 1.25, 1),
                    min(base[1] * 1.25, 1),
                    min(base[2] * 1.25, 1),
                    base[3],
                )
            else:
                btn.background_color = base
    
    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def screen_to_game_pos(self, pos):
        """Конвертировать экранные координаты в игровые (для клика мыши)."""
        x, y = pos
        cx = (x - self.center_x) / self.width * 400
        cy = (self.center_y - y) / self.height * 400
        return (cx, cy)
