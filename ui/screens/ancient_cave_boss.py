#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран выбора босса в Пещере Древних."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui.ui_styles import COLORS
from ui.bindings.keyboard_handler import KeyboardHandler
from ui.widgets.navigation_buttons import add_back_to_map_button
from data.locations import LocationManager

class AncientCaveBossSelectScreen(Screen, KeyboardHandler):
    """Экран выбора босса в Пещере Древних."""
    
    # Данные о боссах
    BOSS_DATA = {
        1: {
            'name': 'Безумный мародёр',
            'desc': 'Легенда лесных разбойников',
            'difficulty': 'Легко',
            'color': (0.3, 0.5, 0.3, 1),
            'unlock_text': 'Доступен сразу'
        },
        2: {
            'name': 'Хозяин Болота',
            'desc': 'Властелин топей и трясин',
            'difficulty': 'Средне',
            'color': (0.3, 0.4, 0.6, 1),
            'unlock_text': 'Требуется открытие Болот'
        },
        3: {
            'name': 'Король Шахт',
            'desc': 'Повелитель подземелья',
            'difficulty': 'Сложно',
            'color': (0.4, 0.3, 0.2, 1),
            'unlock_text': 'Требуется открытие Шахт'
        },
        4: {
            'name': 'Повелитель Драконов',
            'desc': 'Властелин небес и огня',
            'difficulty': 'Очень сложно',
            'color': (0.5, 0.4, 0.3, 1),
            'unlock_text': 'Требуется открытие Гор'
        }
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.location_manager = None
        self.game = None
        
        main_layout = BoxLayout(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(12)
        )
        
        # Фон
        with main_layout.canvas.before:
            Color(0.15, 0.2, 0.25, 1)
            self.bg_rect = Rectangle()
            main_layout.bind(
                size=lambda i, v: setattr(
                    self.bg_rect, 'size', i.size
                ),
                pos=lambda i, v: setattr(
                    self.bg_rect, 'pos', i.pos
                )
            )
        
        # Заголовок
        title_label = Label(
            text='[Таверна] ПЕЩЕРА ДРЕВНИХ - ВЫБОР БОССА',
            font_size=dp(22),
            size_hint_y=None,
            height=dp(50),
            color=(0.9, 0.7, 0.1, 1),
            bold=True
        )
        main_layout.add_widget(title_label)
        
        # Список боссов в ScrollView
        scroll = ScrollView(size_hint=(1, 0.7))
        self.bosses_layout = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None,
            padding=dp(10)
        )
        self.bosses_layout.bind(
            minimum_height=self.bosses_layout.setter(
                'height'
            )
        )
        scroll.add_widget(self.bosses_layout)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        # replace old bottom back with edge 'Back to Map' button
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
    
    def update_bosses(self):
        """Обновление списка боссов."""
        app = App.get_running_app()
        self.game = app.game
        # Use shared LocationManager from game when available
        self.location_manager = self.game.location_manager if (self.game and getattr(self.game, 'location_manager', None)) else LocationManager()
        
        self.bosses_layout.clear_widgets()
        
        for boss_id in [1, 2, 3, 4]:
            boss_info = self.BOSS_DATA[boss_id]
            is_unlocked = (
                self.location_manager.is_boss_unlocked(boss_id)
            )
            
            if is_unlocked:
                btn_text = (
                    f"{boss_info['name']}\n"
                    f"{boss_info['desc']}\n"
                    f"Сложность: {boss_info['difficulty']}"
                )
                btn = Button(
                    text=btn_text,
                    size_hint_y=None,
                    height=dp(100),
                    font_size=dp(16),
                    background_color=boss_info['color']
                )
                btn.bind(
                    on_press=lambda x, bid=boss_id: (
                        self.on_boss_select(bid)
                    )
                )
            else:
                btn_text = (
                    f"[Закрыто] {boss_info['name']}\n"
                    f"{boss_info['unlock_text']}"
                )
                btn = Button(
                    text=btn_text,
                    size_hint_y=None,
                    height=dp(100),
                    font_size=dp(16),
                    background_color=COLORS['hp_red']
                )
                btn.bind(on_press=lambda x, bi=boss_info: (
                    self.on_locked_boss(bi)
                ))
            
            self.bosses_layout.add_widget(btn)
    
    def on_boss_select(self, boss_id):
        """Выбрать босса для боя."""
        from systems.battle import EnemyGenerator
        
        if not self.game or not self.game.player:
            return
        
        # Определяем врага по ID босса
        boss_enemy_ids = {
            1: "enemy_ancient_cave_berserker",
            2: "enemy_ancient_cave_bog_master",
            3: "enemy_ancient_cave_mine_king",
            4: "enemy_ancient_cave_dragon_lord"
        }
        
        boss_enemy_id = boss_enemy_ids[boss_id]
        
        # Генерируем босса
        boss = EnemyGenerator.generate_boss(boss_enemy_id)
        
        if not boss:
            popup = Popup(
                title='Ошибка',
                content=Label(text='Не удалось создать босса!'),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return
        
        # Создаём поле боя через сессию
        try:
            battlefield, _service = self.game.create_battle([boss])
        except Exception:
            popup = Popup(
                title='Ошибка',
                content=Label(text='Не удалось начать бой с боссом!'),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        app = App.get_running_app()
        boss_names = {
            1: "Безумный мародёр",
            2: "Хозяин Болота",
            3: "Король Шахт",
            4: "Повелитель Драконов"
        }
        app.battle_screen.start_battle(
            battlefield,
            f"[Таверна] {boss_names[boss_id]}"
        )
        self.manager.current = 'battle'
    
    def on_enter(self):
        """Обновление данных при входе на экран выбора боссов."""
        app = App.get_running_app()
        self.game = getattr(app, 'game', None)
        if self.game and getattr(self.game, 'location_manager', None):
            self.location_manager = self.game.location_manager
        # Refresh the boss list when screen is entered
        try:
            self.update_bosses()
        except Exception:
            pass
    
    def on_locked_boss(self, boss_info):
        """Показать требования для разблокировки босса."""
        popup = Popup(
            title=f'[Закрыто] {boss_info["name"]}',
            content=Label(
                text=boss_info['unlock_text'],
                text_size=(None, None),
                halign='center',
                valign='middle',
                font_size=dp(18)
            ),
            size_hint=(0.7, 0.4),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()
    
