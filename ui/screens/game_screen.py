#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Главный игровой экран."""

import random

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.core.window import Window
from core.hybrid_controls import HybridControlManager
from ui.bindings.keyboard_handler import KeyboardHandler, _keycode_to_char
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, Line
from kivy.metrics import dp

from ui.ui_styles import StyledButton, COLORS
from ui.widgets.map_widget import MapWidget
from systems.battle import EnemyGenerator

class GameScreen(Screen, KeyboardHandler):
    """Главный игровой экран."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = None
        self.battlefield = None
        self.controls = HybridControlManager()
        self.bind_keyboard()
        self._kb_location_ids = []
        self._kb_location_index = 0
        self._kb_selected_location = None
        
        main_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        # Фон игрового экрана - тёмный с коричневым оттенком
        with main_layout.canvas.before:
            Color(*COLORS['dark_bg'])
            self.bg_rect = Rectangle()
            main_layout.bind(
                size=lambda i, v: setattr(self.bg_rect, 'size', i.size),
                pos=lambda i, v: setattr(self.bg_rect, 'pos', i.pos)
            )
        
        # Статистика игрока с улучшенным дизайном
        stats_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(110), padding=dp(10))
        stats_box.canvas.before.clear()
        with stats_box.canvas.before:
            Color(*COLORS['panel'])
            rect = Rectangle(pos=stats_box.pos, size=stats_box.size)
            # Граница
            Color(*COLORS['border_gold'])
            Line(rectangle=(stats_box.x, stats_box.y, stats_box.width, stats_box.height), width=dp(1.5))
            stats_box.bind(
                pos=lambda i, v: setattr(rect, 'pos', i.pos),
                size=lambda i, v: setattr(rect, 'size', i.size)
            )
        
        self.stats_label = Label(
            text='',
            font_size=dp(19),
            size_hint_y=None,
            height=dp(100),
            text_size=(None, None),
            halign='left',
            valign='top',
            color=COLORS['text_light']
        )
        stats_box.add_widget(self.stats_label)
        main_layout.add_widget(stats_box)
        
        # Карта и меню
        content_layout = BoxLayout(orientation='horizontal', spacing=dp(12))
        
        # Интерактивная карта
        self.map_widget = MapWidget(self, size_hint_x=0.6)
        content_layout.add_widget(self.map_widget)
        try:
            self._kb_location_ids = self.map_widget.get_location_ids()
            if self._kb_location_ids:
                self._kb_location_index = 0
                self._kb_selected_location = self._kb_location_ids[0]
                self.map_widget.set_selected_location(self._kb_selected_location)
        except Exception:
            pass
        
        # Кнопки меню с улучшенным дизайном
        menu_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_x=0.4)
        
        btn_city = StyledButton(
            text='🏛️ ГОРОД',
            color=COLORS['stone_light'],
            size_hint_y=None,
            height=dp(55),
            font_size=dp(18)
        )
        btn_city.bind(on_press=self.on_city)
        menu_layout.add_widget(btn_city)
        
        btn_inventory = StyledButton(
            text='🎒 ИНВЕНТАРЬ',
            color=COLORS['stone_light'],
            size_hint_y=None,
            height=dp(55),
            font_size=dp(18)
        )
        btn_inventory.bind(on_press=self.on_inventory)
        menu_layout.add_widget(btn_inventory)

        btn_locations = StyledButton(
            text='🗺️ ЛОКАЦИИ',
            color=COLORS['gold'],
            size_hint_y=None,
            height=dp(55),
            font_size=dp(18)
        )
        btn_locations.bind(on_press=self.on_locations)
        menu_layout.add_widget(btn_locations)
        
        btn_status = StyledButton(
            text='📊 СТАТУС',
            color=COLORS['stone_light'],
            size_hint_y=None,
            height=dp(55),
            font_size=dp(18)
        )
        btn_status.bind(on_press=self.on_status)
        menu_layout.add_widget(btn_status)

        btn_companions = StyledButton(
            text='🤝 СПУТНИКИ',
            color=COLORS['stone_light'],
            size_hint_y=None,
            height=dp(55),
            font_size=dp(18)
        )
        btn_companions.bind(on_press=self.on_companions)
        menu_layout.add_widget(btn_companions)

        btn_quests = StyledButton(
            text='📋 КВЕСТЫ',
            color=COLORS['stone_light'],
            size_hint_y=None,
            height=dp(55),
            font_size=dp(18)
        )
        btn_quests.bind(on_press=self.on_active_quests)
        menu_layout.add_widget(btn_quests)

        btn_save = StyledButton(
            text='💾 СОХРАНИТЬ',
            color=COLORS['hp_green'],
            size_hint_y=None,
            height=dp(55),
            font_size=dp(18)
        )
        btn_save.bind(on_press=self.on_save)
        menu_layout.add_widget(btn_save)
        
        content_layout.add_widget(menu_layout)
        main_layout.add_widget(content_layout)
        
        self.add_widget(main_layout)

    def _kb_select_location_delta(self, delta: int) -> bool:
        if not self._kb_location_ids:
            return False
        self._kb_location_index = (self._kb_location_index + delta) % len(self._kb_location_ids)
        self._kb_selected_location = self._kb_location_ids[self._kb_location_index]
        try:
            self.map_widget.set_selected_location(self._kb_selected_location)
        except Exception:
            pass
        return True
    
    def update_game_state(self):
        """Обновление отображения состояния игры."""
        if not self.game or not self.game.player:
            return
        
        p = self.game.player
        self.stats_label.text = (
            f"День {self.game.day} | Уровень {p.level} | "
            f"💰 {p.coins} | XP: {p.experience}/{p.level*100}\n"
            f"HP: {p.health}/{p.max_health} | DMG: {p.damage} | DEF: {p.defense}"
        )
    
    def handle_keyboard_action(self, action: str, pressed: bool = True) -> bool:
        """Обработка клавиатурных действий."""
        if action == "move_up" and pressed:
            return self._kb_select_location_delta(-1)
        elif action == "move_down" and pressed:
            return self._kb_select_location_delta(1)
        elif action == "move_left" and pressed:
            return self._kb_select_location_delta(-1)
        elif action == "move_right" and pressed:
            return self._kb_select_location_delta(1)
        elif action == "enter_location" and pressed:
            if self._kb_selected_location:
                self.enter_location(self._kb_selected_location)
            return True
        elif action == "open_inventory" and pressed:
            self.on_inventory(None)
            return True
        elif action == "open_status" and pressed:
            self.on_status(None)
            return True
        elif action == "open_companions" and pressed:
            self.on_companions(None)
            return True
        elif action == "open_quests" and pressed:
            self.on_active_quests(None)
            return True
        elif action == "open_locations" and pressed:
            self.on_locations(None)
            return True
        elif action == "open_save" and pressed:
            self.on_save(None)
            return True
        elif action in ("open_menu", "exit_location") and pressed:
            try:
                app = App.get_running_app()
                if getattr(app, "game", None) and getattr(app.game, "player", None):
                    app.game.autosave()
            except Exception:
                pass
            try:
                self.manager.current = "main_menu"
            except Exception:
                pass
            return True
        return False
    
    def on_touch_down(self, touch):
        """Обработка касания/клика мыши - движение по карте."""
        if not self.game or not self.game.player:
            return super().on_touch_down(touch)
        
        if self.map_widget.collide_point(*touch.pos):
            widget_pos = self.map_widget.to_local(*touch.pos, relative=False)
            game_pos = self.map_widget.screen_to_game_pos(widget_pos)
            self.controls.handle_mouse_click(game_pos)
        
        return super().on_touch_down(touch)
    
    def enter_location(self, loc_id):
        """Вход в локацию."""
        if not self.game or not self.game.player:
            return  # Early return if game or player is not initialized

        if not self.game.player.is_alive:
            popup = Popup(
                title='Ошибка',
                content=Label(text='Вы не можете идти - вы мертвы!'),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        # Получить локацию из менеджера
        location_manager = getattr(self.game, 'location_manager', None)
        location = None
        if location_manager:
            try:
                location = location_manager.get_location(loc_id)
            except Exception:
                location = None

        if location:
            location.visited = True

        if not location:
            popup = Popup(
                title='Ошибка',
                content=Label(text='Локация не найдена!'),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        if getattr(location, 'is_locked', False):
            condition_text = getattr(location, 'unlock_condition', None) or 'Эта локация пока недоступна.'
            popup = Popup(
                title=f'🔒 {location.name}',
                content=Label(text=f"Требования для разблокировки:\n{condition_text}", font_size=dp(18)),
                size_hint=(0.7, 0.4),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        # Special case: ancient cave — боссы перенесены в локации
        if loc_id == 'ancient_cave':
            popup = Popup(
                title='Пещера Древних',
                content=Label(
                    text='Боссы теперь обитают в своих локациях.',
                    font_size=dp(18),
                ),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        # Проходимые локальные карты (только город)
        from data.local_scenes import enter_local_scene
        if loc_id == 'city':
            app = App.get_running_app()
            enter_local_scene(app, loc_id)
            return

        # Normal locations -> start a battle (legacy fallback)
        app = App.get_running_app()
        cnt = random.randint(1, 3)
        try:
            enemies = EnemyGenerator.generate_for_location(
                loc_id, self.game.player.level, count=cnt
            )
        except Exception:
            enemies = []

        if not enemies:
            popup = Popup(
                title='Ошибка',
                content=Label(text='Нет врагов для этой локации.'),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        try:
            battlefield, _service = self.game.create_battle(enemies)
        except Exception:
            popup = Popup(
                title='Ошибка',
                content=Label(text='Не удалось начать бой.'),
                size_hint=(0.6, 0.3),
                background='',
                background_color=(0, 0, 0, 0),
                separator_color=(0, 0, 0, 0),
            )
            popup.open()
            return

        self.battlefield = battlefield
        self.current_location = location

        try:
            if app and getattr(app, 'battle_screen', None):
                app.battle_screen.start_battle(battlefield, location.name)
            self.manager.current = 'battle'
        except Exception:
            popup = Popup(title='Ошибка', content=Label(text='Не удалось начать бой.'), size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),)
            popup.open()
    
    def on_city(self, instance):
        if not self.game or not self.game.player:
            return
        from data.local_scenes import enter_local_scene

        app = App.get_running_app()
        enter_local_scene(app, "city")
    
    def on_inventory(self, instance):
        if not self.game or not self.game.player:
            return
        from ui.widgets.navigation_buttons import prepare_inventory_navigation

        prepare_inventory_navigation('game_screen')
        app = App.get_running_app()
        app.inventory_screen.update_inventory()
        self.manager.current = 'inventory'
    
    def on_status(self, instance):
        if not self.game or not self.game.player:
            return
        app = App.get_running_app()
        app.status_screen.update_status()
        self.manager.current = 'status'
    
    def on_locations(self, instance):
        """Открыть экран выбора локаций."""
        if not self.game or not self.game.player:
            return
        app = App.get_running_app()
        if app.location_select_screen:
            app.location_select_screen.update_locations()
            self.manager.current = 'location_select'
    
    def on_companions(self, instance):
        """Открыть экран управления спутниками."""
        if not self.game or not self.game.player:
            return
        app = App.get_running_app()
        if app.companion_management_screen:
            app.companion_management_screen.update_companion()
            self.manager.current = 'companion_management'

    def on_active_quests(self, instance):
        """Открыть экран активных квестов."""
        if not self.game or not self.game.player:
            return
        app = App.get_running_app()
        if app.active_quests_screen:
            app.active_quests_screen.update_quests()
            self.manager.current = 'active_quests'
    
    def on_save(self, instance):
        if not self.game or not self.game.player:
            return
        
        from datetime import datetime
        
        content = BoxLayout(orientation='vertical', spacing=dp(12),
                            padding=dp(20))
        
        info_label = Label(
            text=f'День: {self.game.day} | '
                 f'Уровень: {self.game.player.level}\n'
                 f'Монеты: {self.game.player.coins}',
            font_size=dp(16),
            text_size=(None, None),
            halign='center',
            color=COLORS['text_light']
        )
        content.add_widget(info_label)
        
        name_input = TextInput(
            text=f'save_{self.game.day}_{datetime.now().strftime("%H%M")}',
            multiline=False,
            font_size=dp(18),
            background_color=(0.2, 0.2, 0.3, 1),
            foreground_color=(1, 1, 1, 1)
        )
        content.add_widget(Label(text='Имя сохранения:', font_size=dp(18),
                                 color=(0.9, 0.9, 0.9, 1)))
        content.add_widget(name_input)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(55))
        
        def save_confirm(instance):
            name = name_input.text.strip() or f"save_{self.game.day}"
            if self.game.save_to_file(name):
                popup.dismiss()
                popup2 = Popup(
                    title='✅ Успех',
                    content=Label(
                        text=f'Игра сохранена как "{name}"',
                        font_size=dp(18),
                    ),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup2.open()
            else:
                popup.dismiss()
                popup2 = Popup(
                    title='❌ Ошибка',
                    content=Label(
                        text='Ошибка сохранения.',
                        font_size=dp(18),
                    ),
                    size_hint=(0.6, 0.3),
                    background='',
                    background_color=(0, 0, 0, 0),
                    separator_color=(0, 0, 0, 0),
                )
                popup2.open()
        
        btn_save = Button(
            text='💾 Сохранить',
            background_color=COLORS['hp_green'],
            font_size=dp(18)
        )
        btn_save.bind(on_press=save_confirm)
        btn_layout.add_widget(btn_save)
        
        btn_cancel = Button(
            text='Отмена',
            background_color=COLORS['stone'],
            font_size=dp(18)
        )
        btn_cancel.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(btn_cancel)
        
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='💾 Сохранение игры',
            content=content,
            size_hint=(0.7, 0.45),
            background='',
            background_color=(0, 0, 0, 0),
            separator_color=(0, 0, 0, 0),
        )
        popup.open()

