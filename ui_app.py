#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kivy UI для RPG игры.
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
import sys
import random

from game import Game
from creatures import Player
from items import ItemDatabase, Weapon, Armor, Potion
from save_system import save_game, load_game, get_save_list
from battle import Battlefield, EnemyGenerator, EventSystem


class MainMenuScreen(Screen):
    """Главное меню."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        title = Label(
            text='⚔️ MINI RPG ⚔️',
            font_size=dp(48),
            size_hint_y=None,
            height=dp(100)
        )
        layout.add_widget(title)
        
        button_layout = BoxLayout(orientation='vertical', spacing=dp(15), size_hint_y=None)
        button_layout.bind(minimum_height=button_layout.setter('height'))
        
        btn_new = Button(
            text='🆕 Новая игра',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(24)
        )
        btn_new.bind(on_press=self.on_new_game)
        button_layout.add_widget(btn_new)
        
        btn_load = Button(
            text='💾 Загрузить игру',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(24)
        )
        btn_load.bind(on_press=self.on_load_game)
        button_layout.add_widget(btn_load)
        
        btn_exit = Button(
            text='← Выход',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(24)
        )
        btn_exit.bind(on_press=self.on_exit)
        button_layout.add_widget(btn_exit)
        
        layout.add_widget(button_layout)
        self.add_widget(layout)
    
    def on_new_game(self, instance):
        self.manager.current = 'character_creation'
    
    def on_load_game(self, instance):
        saves = get_save_list()
        if not saves:
            popup = Popup(
                title='Ошибка',
                content=Label(text='Нет сохранений.'),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            return
        
        self.manager.get_screen('load_game').update_saves(saves)
        self.manager.current = 'load_game'
    
    def on_exit(self, instance):
        sys.exit(0)


class LoadGameScreen(Screen):
    """Экран загрузки игры."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        
        title = Label(
            text='💾 Загрузка игры',
            font_size=dp(36),
            size_hint_y=None,
            height=dp(80)
        )
        layout.add_widget(title)
        
        scroll = ScrollView()
        self.save_list = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        self.save_list.bind(minimum_height=self.save_list.setter('height'))
        scroll.add_widget(self.save_list)
        layout.add_widget(scroll)
        
        btn_back = Button(
            text='← Назад',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(20)
        )
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
    
    def update_saves(self, saves):
        self.save_list.clear_widgets()
        for save_name in saves:
            btn = Button(
                text=save_name,
                size_hint_y=None,
                height=dp(55),
                font_size=dp(21),
                background_color=(0.3, 0.5, 0.7, 1)
            )
            btn.bind(on_press=lambda x, name=save_name: self.load_save(name))
            self.save_list.add_widget(btn)
    
    def load_save(self, save_name):
        ItemDatabase.initialize()
        player = load_game(save_name)
        if player:
            game = Game()
            game.player = player
            game.day = player.level * 5
            
            app = App.get_running_app()
            app.game = game
            app.game_screen.game = game
            app.game_screen.update_game_state()
            self.manager.current = 'game'
        else:
            popup = Popup(
                title='Ошибка',
                content=Label(text='Ошибка загрузки.'),
                size_hint=(0.6, 0.3)
            )
            popup.open()
    
    def on_back(self, instance):
        self.manager.current = 'main_menu'


class CharacterCreationScreen(Screen):
    """Экран создания персонажа."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(25), spacing=dp(20))
        
        # Фон
        with layout.canvas.before:
            Color(0.12, 0.18, 0.28, 1)  # Темно-синий фон
            self.bg_rect = Rectangle()
            layout.bind(size=lambda instance, value: setattr(self.bg_rect, 'size', instance.size),
                       pos=lambda instance, value: setattr(self.bg_rect, 'pos', instance.pos))
        
        title = Label(
            text='👤 Создание персонажа',
            font_size=dp(42),
            size_hint_y=None,
            height=dp(90),
            color=(0.9, 0.8, 0.3, 1)
        )
        layout.add_widget(title)
        
        name_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(55))
        name_label = Label(text='Имя:', size_hint_x=0.3, font_size=dp(20), color=(0.9, 0.9, 0.9, 1))
        name_layout.add_widget(name_label)
        self.name_input = TextInput(
            text='Герой',
            multiline=False,
            size_hint_x=0.7,
            font_size=dp(18),
            background_color=(0.2, 0.2, 0.3, 1),
            foreground_color=(1, 1, 1, 1)
        )
        name_layout.add_widget(self.name_input)
        layout.add_widget(name_layout)
        
        class_label = Label(
            text='Выберите класс:',
            font_size=dp(26),
            size_hint_y=None,
            height=dp(55),
            color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(class_label)
        
        class_layout = GridLayout(cols=1, spacing=dp(12), size_hint_y=None)
        class_layout.bind(minimum_height=class_layout.setter('height'))
        
        self.selected_class = 'warrior'
        self.class_buttons = {}
        
        btn_warrior = Button(
            text='⚔️ Воин (Макс HP, средний урон)',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(22),
            background_color=(0.3, 0.5, 0.7, 1)
        )
        btn_warrior.bind(on_press=lambda x: self.select_class('warrior', btn_warrior))
        class_layout.add_widget(btn_warrior)
        self.class_buttons['warrior'] = btn_warrior
        
        btn_mage = Button(
            text='🔮 Маг (Макс урон, меньше HP)',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(22),
            background_color=(0.5, 0.3, 0.7, 1)
        )
        btn_mage.bind(on_press=lambda x: self.select_class('mage', btn_mage))
        class_layout.add_widget(btn_mage)
        self.class_buttons['mage'] = btn_mage
        
        btn_archer = Button(
            text='🏹 Лучник (Баланс)',
            size_hint_y=None,
            height=dp(60),
            font_size=dp(22),
            background_color=(0.3, 0.7, 0.5, 1)
        )
        btn_archer.bind(on_press=lambda x: self.select_class('archer', btn_archer))
        class_layout.add_widget(btn_archer)
        self.class_buttons['archer'] = btn_archer
        
        layout.add_widget(class_layout)
        
        btn_create = Button(
            text='✨ Создать персонажа',
            size_hint_y=None,
            height=dp(70),
            font_size=dp(26),
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_create.bind(on_press=self.create_character)
        layout.add_widget(btn_create)
        
        btn_back = Button(
            text='← Назад',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(22),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
    
    def select_class(self, cls, button):
        self.selected_class = cls
        # Визуальная индикация выбора
        for btn in self.class_buttons.values():
            btn.background_color = (btn.background_color[0] * 0.7, btn.background_color[1] * 0.7, btn.background_color[2] * 0.7, 1)
        button.background_color = (button.background_color[0] * 1.3, button.background_color[1] * 1.3, button.background_color[2] * 1.3, 1)
    
    def create_character(self, instance):
        name = self.name_input.text.strip() or "Герой"
        ItemDatabase.initialize()
        game = Game()
        game.player = Player(name, self.selected_class)
        
        # Начальные ресурсы (сбалансировано)
        game.player.coins += 50  # Уменьшено для баланса
        game.player.inventory.add(ItemDatabase.get("w_short"), 1)
        game.player.inventory.add(ItemDatabase.get("a_leather"), 1)  # Более дешевая броня
        game.player.inventory.add(ItemDatabase.get("p_small"), 3)  # Больше зелий, но слабее
        
        app = App.get_running_app()
        app.game = game
        app.game_screen.game = game
        app.game_screen.update_game_state()
        
        # Показываем приветственное сообщение
        welcome_text = (
            f"Добро пожаловать, {name}!\n\n"
            f"Вы начинаете с:\n"
            f"💰 {game.player.coins} монет\n"
            f"⚔️ {game.player.weapon.name if game.player.weapon else 'Кулаки'}\n"
            f"🛡️ {game.player.armor.name if game.player.armor else 'Нет'}\n\n"
            f"💡 Подсказка: Посетите таверну для квестов,\n"
            f"магазин для покупки предметов,\n"
            f"и исследуйте локации на карте!"
        )
        
        popup = Popup(
            title='🎮 Добро пожаловать!',
            content=Label(
                text=welcome_text,
                text_size=(None, None),
                halign='center',
                font_size=dp(18)
            ),
            size_hint=(0.8, 0.6)
        )
        popup.open()
        
        self.manager.current = 'game'
    
    def on_back(self, instance):
        self.manager.current = 'main_menu'


class MapWidget(BoxLayout):
    """Интерактивная карта локаций."""
    
    LOCATION_INFO = {
        'forest': {
            'name': '🌲 Лес',
            'desc': 'Легкие враги\nСобытия',
            'difficulty': 'Легко',
            'color': (0.2, 0.5, 0.2, 1)
        },
        'cave': {
            'name': '⛏️ Пещера',
            'desc': 'Средние враги\nСокровища',
            'difficulty': 'Средне',
            'color': (0.4, 0.3, 0.2, 1)
        },
        'ruins': {
            'name': '🏛️ Руины',
            'desc': 'Сложные враги\nЛегенды',
            'difficulty': 'Сложно',
            'color': (0.5, 0.4, 0.3, 1)
        }
    }
    
    def __init__(self, game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = game_screen
        self.orientation = 'vertical'
        self.spacing = dp(8)
        self.padding = dp(12)
        
        # Фон карты
        with self.canvas.before:
            Color(0.15, 0.2, 0.15, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            self.bind(pos=self.update_bg, size=self.update_bg)
        
        # Заголовок карты
        map_title = Label(
            text='🗺️ КАРТА МИРА',
            font_size=dp(20),
            size_hint_y=None,
            height=dp(35),
            color=(0.9, 0.8, 0.3, 1)
        )
        self.add_widget(map_title)
        
        # Кнопки локаций с улучшенным дизайном
        locations_layout = BoxLayout(orientation='vertical', spacing=dp(8))
        
        for loc_id in ['forest', 'cave', 'ruins']:
            info = self.LOCATION_INFO[loc_id]
            loc_box = BoxLayout(orientation='vertical', spacing=dp(3), size_hint_y=None, height=dp(90))
            
            btn = Button(
                text=f"{info['name']}\n{info['desc']}\nСложность: {info['difficulty']}",
                font_size=dp(18),
                background_color=info['color'],
                size_hint_y=None,
                height=dp(85)
            )
            btn.bind(on_press=lambda x, loc=loc_id: self.game_screen.enter_location(loc))
            loc_box.add_widget(btn)
            locations_layout.add_widget(loc_box)
        
        self.add_widget(locations_layout)
    
    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class GameScreen(Screen):
    """Главный игровой экран."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = None
        self.battlefield = None
        
        main_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        # Фон игрового экрана
        with main_layout.canvas.before:
            Color(0.15, 0.2, 0.25, 1)  # Темно-серый фон
            self.bg_rect = Rectangle()
            main_layout.bind(size=lambda instance, value: setattr(self.bg_rect, 'size', instance.size),
                           pos=lambda instance, value: setattr(self.bg_rect, 'pos', instance.pos))
        
        # Статистика игрока с улучшенным дизайном
        stats_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(110), padding=dp(10))
        stats_box.canvas.before.clear()
        with stats_box.canvas.before:
            Color(0.2, 0.25, 0.3, 1)  # Темная панель
            Rectangle(pos=stats_box.pos, size=stats_box.size)
            stats_box.bind(pos=lambda instance, value: setattr(Rectangle(), 'pos', instance.pos),
                          size=lambda instance, value: setattr(Rectangle(), 'size', instance.size))
        
        self.stats_label = Label(
            text='',
            font_size=dp(19),
            size_hint_y=None,
            height=dp(100),
            text_size=(None, None),
            halign='left',
            valign='top',
            color=(0.95, 0.95, 0.95, 1)
        )
        stats_box.add_widget(self.stats_label)
        main_layout.add_widget(stats_box)
        
        # Карта и меню
        content_layout = BoxLayout(orientation='horizontal', spacing=dp(12))
        
        # Интерактивная карта
        self.map_widget = MapWidget(self, size_hint_x=0.6)
        content_layout.add_widget(self.map_widget)
        
        # Кнопки меню с улучшенным дизайном
        menu_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_x=0.4)
        
        btn_tavern = Button(
            text='🏰 Таверна',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(21),
            background_color=(0.6, 0.4, 0.2, 1)
        )
        btn_tavern.bind(on_press=self.on_tavern)
        menu_layout.add_widget(btn_tavern)
        
        btn_shop = Button(
            text='🛒 Магазин',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(21),
            background_color=(0.2, 0.6, 0.8, 1)
        )
        btn_shop.bind(on_press=self.on_shop)
        menu_layout.add_widget(btn_shop)
        
        btn_casino = Button(
            text='🎰 Казино',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(21),
            background_color=(0.8, 0.6, 0.2, 1)
        )
        btn_casino.bind(on_press=self.on_casino)
        menu_layout.add_widget(btn_casino)
        
        btn_inventory = Button(
            text='🎒 Инвентарь',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(21),
            background_color=(0.3, 0.7, 0.5, 1)
        )
        btn_inventory.bind(on_press=self.on_inventory)
        menu_layout.add_widget(btn_inventory)
        
        btn_status = Button(
            text='📊 Статус',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(21),
            background_color=(0.5, 0.5, 0.7, 1)
        )
        btn_status.bind(on_press=self.on_status)
        menu_layout.add_widget(btn_status)
        
        btn_save = Button(
            text='💾 Сохранить',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(21),
            background_color=(0.4, 0.4, 0.4, 1)
        )
        btn_save.bind(on_press=self.on_save)
        menu_layout.add_widget(btn_save)
        
        content_layout.add_widget(menu_layout)
        main_layout.add_widget(content_layout)
        
        self.add_widget(main_layout)
    
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
    
    def enter_location(self, loc):
        """Вход в локацию."""
        if not self.game or not self.game.player:
            popup = Popup(
                title='Ошибка',
                content=Label(text='Игра не инициализирована!'),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            return
        
        if not self.game.player.is_alive:
            popup = Popup(
                title='Ошибка',
                content=Label(text='Вы не можете идти - вы мертвы!'),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            return
        
        self.game.day += 1
        self.game.player.battles_fought += 1
        
        # Событие
        evt = None
        if loc == "forest":
            evt = EventSystem.roll_forest(self.game.player)
        elif loc == "cave":
            evt = EventSystem.roll_cave(self.game.player)
        
        if evt:
            self.game.history.append(evt)
        
        # Генерация врагов
        if loc == "forest":
            count = random.randint(1, 2)
        elif loc == "cave":
            count = random.randint(1, 3)
        else:  # ruins
            count = random.randint(2, 3)
        
        enemies = EnemyGenerator.generate(loc, self.game.player.level, count)
        self.battlefield = Battlefield(self.game.player, enemies)
        
        # Переход на экран боя
        app = App.get_running_app()
        app.battle_screen.start_battle(self.battlefield, evt)
        self.manager.current = 'battle'
    
    def on_tavern(self, instance):
        if not self.game or not self.game.player:
            return
        app = App.get_running_app()
        app.tavern_screen.update_tavern()
        self.manager.current = 'tavern'
    
    def on_shop(self, instance):
        if not self.game or not self.game.player:
            return
        app = App.get_running_app()
        app.shop_screen.update_shop()
        self.manager.current = 'shop'
    
    def on_casino(self, instance):
        if not self.game or not self.game.player:
            return
        app = App.get_running_app()
        app.casino_screen.update_casino()
        self.manager.current = 'casino'
    
    def on_inventory(self, instance):
        if not self.game or not self.game.player:
            return
        app = App.get_running_app()
        app.inventory_screen.update_inventory()
        self.manager.current = 'inventory'
    
    def on_status(self, instance):
        if not self.game or not self.game.player:
            return
        app = App.get_running_app()
        app.status_screen.update_status()
        self.manager.current = 'status'
    
    def on_save(self, instance):
        if not self.game or not self.game.player:
            return
        
        from datetime import datetime
        
        content = BoxLayout(orientation='vertical', spacing=dp(12), padding=dp(20))
        
        info_label = Label(
            text=f'День: {self.game.day} | Уровень: {self.game.player.level}\nМонеты: {self.game.player.coins}',
            font_size=dp(16),
            text_size=(None, None),
            halign='center',
            color=(0.9, 0.9, 0.9, 1)
        )
        content.add_widget(info_label)
        
        name_input = TextInput(
            text=f'save_{self.game.day}_{datetime.now().strftime("%H%M")}',
            multiline=False,
            font_size=dp(18),
            background_color=(0.2, 0.2, 0.3, 1),
            foreground_color=(1, 1, 1, 1)
        )
        content.add_widget(Label(text='Имя сохранения:', font_size=dp(18), color=(0.9, 0.9, 0.9, 1)))
        content.add_widget(name_input)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(55))
        
        def save_confirm(instance):
            name = name_input.text.strip() or f"save_{self.game.day}"
            if save_game(self.game.player, name):
                popup.dismiss()
                popup2 = Popup(
                    title='✅ Успех',
                    content=Label(
                        text=f'Игра сохранена как "{name}"',
                        font_size=dp(18)
                    ),
                    size_hint=(0.6, 0.3)
                )
                popup2.open()
            else:
                popup.dismiss()
                popup2 = Popup(
                    title='❌ Ошибка',
                    content=Label(
                        text='Ошибка сохранения',
                        font_size=dp(18)
                    ),
                    size_hint=(0.6, 0.3)
                )
                popup2.open()
        
        btn_save = Button(
            text='💾 Сохранить',
            background_color=(0.2, 0.7, 0.3, 1),
            font_size=dp(18)
        )
        btn_save.bind(on_press=save_confirm)
        btn_layout.add_widget(btn_save)
        
        btn_cancel = Button(
            text='Отмена',
            background_color=(0.5, 0.5, 0.5, 1),
            font_size=dp(18)
        )
        btn_cancel.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(btn_cancel)
        
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='💾 Сохранение игры',
            content=content,
            size_hint=(0.7, 0.45)
        )
        popup.open()


class BattleScreen(Screen):
    """Экран боя."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.battlefield = None
        self.event_message = None
        self.is_processing_turn = False  # Флаг блокировки действий во время обработки хода
        
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        # Устанавливаем темный фон для боевого экрана
        with layout.canvas.before:
            Color(0.15, 0.15, 0.2, 1)  # Темно-синий фон
            self.bg_rect = Rectangle()
            layout.bind(size=lambda instance, value: setattr(self.bg_rect, 'size', instance.size),
                       pos=lambda instance, value: setattr(self.bg_rect, 'pos', instance.pos))
        
        # Сообщение о событии
        self.event_label = Label(
            text='',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(50),
            text_size=(None, None),
            color=(0.9, 0.9, 0.3, 1)  # Желтый цвет для событий
        )
        layout.add_widget(self.event_label)
        
        # Информация о бое с улучшенным дизайном
        self.battle_info = Label(
            text='',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(120),
            text_size=(None, None),
            halign='left',
            valign='top',
            color=(0.9, 0.9, 0.9, 1)  # Светлый цвет текста
        )
        layout.add_widget(self.battle_info)
        
        # Список врагов
        scroll = ScrollView()
        self.enemies_layout = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None)
        self.enemies_layout.bind(minimum_height=self.enemies_layout.setter('height'))
        scroll.add_widget(self.enemies_layout)
        layout.add_widget(scroll)
        
        # Лог боя с улучшенным дизайном
        log_header = Label(
            text="📜 ЛОГ БОЯ:",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30),
            color=(0.8, 0.8, 0.8, 1)
        )
        layout.add_widget(log_header)
        
        scroll_log = ScrollView()
        self.log_label = Label(
            text='',
            font_size=dp(15),
            size_hint_y=None,
            text_size=(None, None),
            halign='left',
            valign='top',
            color=(0.9, 0.9, 0.9, 1)
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        scroll_log.add_widget(self.log_label)
        layout.add_widget(scroll_log)
        
        # Кнопки действий
        actions_layout = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(120))
        
        self.btn_inventory = Button(
            text='🎒 Инвентарь',
            font_size=dp(18),
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.btn_inventory.bind(on_press=self.on_open_inventory)
        actions_layout.add_widget(self.btn_inventory)
        
        self.btn_escape = Button(
            text='🏃 Убежать',
            font_size=dp(18),
            background_color=(0.8, 0.6, 0.2, 1)
        )
        self.btn_escape.bind(on_press=self.on_escape)
        actions_layout.add_widget(self.btn_escape)
        
        self.btn_surrender = Button(
            text='🏳️ Сдаться',
            font_size=dp(18),
            background_color=(0.7, 0.3, 0.3, 1)
        )
        self.btn_surrender.bind(on_press=self.on_surrender)
        actions_layout.add_widget(self.btn_surrender)
        
        layout.add_widget(actions_layout)
        
        self.add_widget(layout)
    
    def start_battle(self, battlefield, event_message=None):
        """Начало боя."""
        self.battlefield = battlefield
        self.event_message = event_message
        self.log_label.text = ''
        self.is_processing_turn = False
        self.update_battle_display()
        
        if event_message:
            self.event_label.text = f"⚡ {event_message}"
        else:
            self.event_label.text = ''
        
        self.add_log(f"Битва началась! Враги: {', '.join(e.name for e in battlefield.enemies)}")
        Clock.schedule_once(lambda dt: self.enemy_turn(), 0.5)
    
    def update_battle_display(self):
        """Обновление отображения боя."""
        if not self.battlefield:
            return
        
        p = self.battlefield.player
        
        # Улучшенное отображение информации о бое
        companions_info = ""
        if p.companions:
            alive_companions = [c for c in p.companions if c.is_alive]
            if alive_companions:
                comp_text = ", ".join([f"{c.name}({c.health}/{c.max_health})" for c in alive_companions])
                companions_info = f"\n🤝 Спутники: {comp_text}"
            else:
                companions_info = "\n🤝 Спутники: Все выбыли"
        
        self.battle_info.text = (
            f"⚔️ Раунд {self.battlefield.round + 1}\n"
            f"💚 Ваш HP: {p.health}/{p.max_health} | ⚔️ DMG: {p.damage} | 🛡️ DEF: {p.defense}"
            f"{companions_info}"
        )
        
        # Обновление списка врагов с улучшенным дизайном
        self.enemies_layout.clear_widgets()
        enemies = self.battlefield.alive_enemies()
        
        # Заголовок
        header = Label(
            text="👹 ВРАГИ (нажмите для атаки):",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(30),
            bold=True
        )
        self.enemies_layout.add_widget(header)
        
        for i, enemy in enumerate(enemies):
            # Цвет кнопки зависит от здоровья врага
            hp_percent = enemy.health / enemy.max_health if enemy.max_health > 0 else 0
            if hp_percent > 0.6:
                bg_color = (0.7, 0.3, 0.3, 1)  # Красный для здоровых
            elif hp_percent > 0.3:
                bg_color = (0.8, 0.6, 0.2, 1)  # Оранжевый для раненых
            else:
                bg_color = (0.5, 0.5, 0.5, 1)  # Серый для почти мертвых
            
            btn = Button(
                text=f"⚔️ {enemy.name}\n💚 HP: {enemy.health}/{enemy.max_health} | ⚔️ DMG: {enemy.damage}",
                size_hint_y=None,
                height=dp(60),
                font_size=dp(16),
                disabled=self.is_processing_turn,
                background_color=bg_color
            )
            btn.bind(on_press=lambda x, idx=i: self.attack_enemy(idx))
            self.enemies_layout.add_widget(btn)
        
        # Отключаем/включаем кнопки действий
        self.btn_inventory.disabled = self.is_processing_turn
        self.btn_escape.disabled = self.is_processing_turn
        self.btn_surrender.disabled = self.is_processing_turn
    
    def add_log(self, message):
        """Добавление сообщения в лог."""
        self.log_label.text += message + '\n'
        self.log_label.texture_update()
    
    def attack_enemy(self, enemy_index):
        """Атака врага."""
        # Блокируем повторные клики
        if self.is_processing_turn:
            return
        
        if not self.battlefield or self.battlefield.is_over():
            return
        
        # Устанавливаем флаг обработки
        self.is_processing_turn = True
        self.update_battle_display()
        
        result = self.battlefield.player_attack(enemy_index)
        self.add_log(result)
        self.update_battle_display()
        
        if self.battlefield.is_over():
            self.is_processing_turn = False
            self.end_battle()
        else:
            Clock.schedule_once(lambda dt: self.enemy_turn(), 1.0)
    
    def on_open_inventory(self, instance):
        """Открытие инвентаря в бою."""
        if self.is_processing_turn:
            return
        
        if not self.battlefield:
            return
        
        app = App.get_running_app()
        app.battle_inventory_screen.update_inventory(self.battlefield)
        self.manager.current = 'battle_inventory'
    
    def on_escape(self, instance):
        """Попытка побега."""
        if self.is_processing_turn:
            return
        
        if not self.battlefield:
            return
        
        # Устанавливаем флаг обработки
        self.is_processing_turn = True
        self.update_battle_display()
        
        success, logs = self.battlefield.attempt_escape()
        for log in logs:
            self.add_log(f"→ {log}")
        
        if success:
            self.add_log("\nВы успешно сбежали!")
            self.is_processing_turn = False
            Clock.schedule_once(lambda dt: self.return_to_game(), 1.5)
        else:
            if not self.battlefield.is_over():
                Clock.schedule_once(lambda dt: self.enemy_turn(), 1.0)
            else:
                self.is_processing_turn = False
    
    def on_surrender(self, instance):
        """Сдача."""
        if self.is_processing_turn:
            return
        
        self.is_processing_turn = True
        self.update_battle_display()
        self.add_log("\nВы сдались...")
        Clock.schedule_once(lambda dt: self.return_to_game(False), 1.5)
    
    def enemy_turn(self):
        """Ход врагов."""
        if not self.battlefield or self.battlefield.is_over():
            self.is_processing_turn = False
            self.update_battle_display()
            return
        
        # Спутники атакуют
        if self.battlefield.player.companions:
            for c in self.battlefield.player.companions:
                if c.is_alive and self.battlefield.alive_enemies():
                    import random
                    target = random.choice(self.battlefield.alive_enemies())
                    dmg = c.damage
                    dealt = target.take_damage(dmg)
                    self.add_log(f"→ {c.name} наносит {dealt} урона по {target.name}.")
                    if not target.is_alive:
                        self.add_log(f"  💥 {target.name} повержен!")
                        self.battlefield.player.coins += target.base_coins
        
        if self.battlefield.is_over():
            self.is_processing_turn = False
            self.end_battle()
            return
        
        # Ход врагов
        logs = self.battlefield.enemy_turn()
        for log in logs:
            self.add_log(f"→ {log}")
        
        self.update_battle_display()
        
        if not self.battlefield.player.is_alive:
            self.add_log("\n💀 Вы были повержены!")
            self.is_processing_turn = False
            Clock.schedule_once(lambda dt: self.return_to_game(False), 2.0)
        elif self.battlefield.is_over():
            self.is_processing_turn = False
            self.end_battle()
        else:
            # Сбрасываем флаг после завершения хода врагов, чтобы игрок мог действовать
            self.is_processing_turn = False
            self.update_battle_display()
    
    def end_battle(self):
        """Завершение боя."""
        # Сбрасываем флаг обработки
        self.is_processing_turn = False
        self.update_battle_display()
        
        app = App.get_running_app()
        if self.battlefield.player.is_alive:
            self.add_log("\n🎉 Вы победили!")
            
            # Восстанавливаем здоровье компаньонов после боя
            for companion in self.battlefield.player.companions:
                companion.health = companion.max_health
                if not companion.is_alive:
                    self.add_log(f"💚 {companion.name} восстановлен после боя!")
            
            # Регистрация убийств
            if app.game:
                for e in self.battlefield.enemies:
                    if not e.is_alive:
                        for q in app.game.tavern.available_quests.values():
                            q.register_kill(e.name)
                
                app.game.wins_in_row += 1
                app.game.shop.refresh()
                for q in app.game.tavern.available_quests.values():
                    if not q.complete:
                        q.register_win()
            
            Clock.schedule_once(lambda dt: self.return_to_game(True), 2.0)
        else:
            self.add_log("\n💀 Вы были повержены...")
            if app.game:
                app.game.wins_in_row = 0
                # Показываем экран смерти
                Clock.schedule_once(lambda dt: self.show_death_screen(), 2.0)
    
    def show_death_screen(self):
        """Показ экрана смерти."""
        app = App.get_running_app()
        if not app.game:
            return
        
        stats = app.game.player.get_session_stats()
        text = (
            "ИГРА ОКОНЧЕНА - ВЫ БЫЛИ ПОВЕРЖЕНЫ!\n\n"
            "📊 СТАТИСТИКА СЕССИИ:\n"
            f"  Персонаж: {stats['name']} ({stats['class']})\n"
            f"  Финальный уровень: {stats['level']}\n"
            f"  Финальные монеты: {stats['coins']} 💰\n"
            f"  Выданный урон: {stats['total_damage_dealt']}\n"
            f"  Полученный урон: {stats['total_damage_taken']}\n"
            f"  Врагов повержено: {stats['enemies_defeated']}\n"
            f"  Битв проведено: {stats['battles_fought']}\n"
            f"  Предметов в инвентаре: {stats['inventory_items']}\n"
        )
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text=text, text_size=(None, None), halign='left', valign='top'))
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        
        def restart(instance):
            popup.dismiss()
            app.game = None
            self.manager.current = 'main_menu'
        
        def exit(instance):
            popup.dismiss()
            sys.exit(0)
        
        btn_restart = Button(text='Начать заново')
        btn_restart.bind(on_press=restart)
        btn_layout.add_widget(btn_restart)
        
        btn_exit = Button(text='Выйти')
        btn_exit.bind(on_press=exit)
        btn_layout.add_widget(btn_exit)
        
        content.add_widget(btn_layout)
        
        popup = Popup(
            title='💀 Смерть',
            content=content,
            size_hint=(0.8, 0.7),
            auto_dismiss=False
        )
        popup.open()
    
    def return_to_game(self, victory=True):
        """Возврат на главный экран."""
        app = App.get_running_app()
        if app.game:
            app.game_screen.game = app.game
            app.game_screen.update_game_state()
        self.manager.current = 'game'


class TavernScreen(Screen):
    """Экран таверны."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        # Фон таверны
        with layout.canvas.before:
            Color(0.25, 0.2, 0.15, 1)  # Коричневый фон (как в таверне)
            self.bg_rect = Rectangle()
            layout.bind(size=lambda instance, value: setattr(self.bg_rect, 'size', instance.size),
                       pos=lambda instance, value: setattr(self.bg_rect, 'pos', instance.pos))
        
        title = Label(
            text='🏰 ТАВЕРНА',
            font_size=dp(40),
            size_hint_y=None,
            height=dp(70),
            color=(0.9, 0.8, 0.3, 1)
        )
        layout.add_widget(title)
        
        # Вкладки с улучшенным дизайном
        tab_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(55), spacing=dp(5))
        btn_quests = Button(
            text='📜 Квесты',
            size_hint_x=0.5,
            background_color=(0.4, 0.6, 0.3, 1),
            font_size=dp(20)
        )
        btn_quests.bind(on_press=lambda x: self.show_quests())
        tab_layout.add_widget(btn_quests)
        
        btn_companions = Button(
            text='🤝 Спутники',
            size_hint_x=0.5,
            background_color=(0.3, 0.5, 0.7, 1),
            font_size=dp(20)
        )
        btn_companions.bind(on_press=lambda x: self.show_companions())
        tab_layout.add_widget(btn_companions)
        layout.add_widget(tab_layout)
        
        scroll = ScrollView()
        self.content_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        self.content_layout.bind(minimum_height=self.content_layout.setter('height'))
        scroll.add_widget(self.content_layout)
        layout.add_widget(scroll)
        
        btn_back = Button(
            text='← Назад',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(22),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
        self.current_tab = 'quests'
    
    def update_tavern(self):
        self.show_quests()
    
    def show_quests(self):
        self.current_tab = 'quests'
        self.content_layout.clear_widgets()
        
        app = App.get_running_app()
        if not app.game:
            return
        
        for q in app.game.tavern.available_quests.values():
            status = q.progress_display()
            claimed = " ✅ [ПОЛУЧЕНО]" if q.claimed else ""
            complete = " ✅ ЗАВЕРШЕН" if q.complete and not q.claimed else ""
            
            quest_box = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, height=dp(130), padding=dp(8))
            
            # Фон квеста
            with quest_box.canvas.before:
                Color(0.3, 0.3, 0.35, 1)
                quest_bg = Rectangle()
                quest_box.bind(pos=lambda instance, value: setattr(quest_bg, 'pos', instance.pos),
                              size=lambda instance, value: setattr(quest_bg, 'size', instance.size))
            
            # Заголовок квеста
            quest_title = Label(
                text=f"📜 {q.desc}",
                font_size=dp(18),
                size_hint_y=None,
                height=dp(35),
                text_size=(None, None),
                halign='left',
                valign='top',
                color=(0.9, 0.9, 0.3, 1),
                bold=True
            )
            quest_box.add_widget(quest_title)
            
            # Прогресс
            total_goal = sum(q.goal.values())
            total_progress = sum(q.progress.values())
            progress_percent = (total_progress / total_goal * 100) if total_goal > 0 else 0
            
            progress_label = Label(
                text=f"Прогресс: {total_progress}/{total_goal} ({int(progress_percent)}%){complete}{claimed}",
                font_size=dp(16),
                size_hint_y=None,
                height=dp(30),
                text_size=(None, None),
                halign='left',
                valign='top',
                color=(0.8, 0.8, 0.8, 1)
            )
            quest_box.add_widget(progress_label)
            
            # Прогресс-бар (визуальный)
            progress_bar_bg = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(20))
            progress_bar_bg.canvas.before.clear()
            with progress_bar_bg.canvas.before:
                Color(0.2, 0.2, 0.2, 1)
                bar_bg = Rectangle()
                progress_bar_bg.bind(pos=lambda instance, value: setattr(bar_bg, 'pos', instance.pos),
                                    size=lambda instance, value: setattr(bar_bg, 'size', instance.size))
            
            progress_bar = BoxLayout(size_hint_x=progress_percent/100 if progress_percent > 0 else 0.01)
            progress_bar.canvas.before.clear()
            with progress_bar.canvas.before:
                Color(0.2, 0.7, 0.3, 1)
                bar_fill = Rectangle()
                progress_bar.bind(pos=lambda instance, value: setattr(bar_fill, 'pos', instance.pos),
                                 size=lambda instance, value: setattr(bar_fill, 'size', instance.size))
            progress_bar_bg.add_widget(progress_bar)
            quest_box.add_widget(progress_bar_bg)
            
            # Кнопка получения награды
            if q.complete and not q.claimed:
                btn_claim = Button(
                    text='🎁 Получить награду',
                    size_hint_y=None,
                    height=dp(45),
                    background_color=(0.2, 0.7, 0.3, 1),
                    font_size=dp(18)
                )
                btn_claim.bind(on_press=lambda x, quest=q: self.claim_quest(quest))
                quest_box.add_widget(btn_claim)
            
            self.content_layout.add_widget(quest_box)
    
    def show_companions(self):
        self.current_tab = 'companions'
        self.content_layout.clear_widgets()
        
        app = App.get_running_app()
        if not app.game:
            return
        
        companions = app.game.tavern.COMPANIONS
        for i, (name, role) in enumerate(companions, 1):
            roles_desc = {
                "tank": "Танк (высокая защита)",
                "archer": "Лучник (высокий урон)",
                "healer": "Целитель (восстанавливает HP)"
            }
            
            # Получаем цену из ROLES
            from creatures import Companion
            role_data = Companion.ROLES.get(role, {"coins": 30})
            price = role_data["coins"]
            
            comp_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
            comp_label = Label(
                text=f"{i}) {name} — {roles_desc.get(role, role)} (цена: {price} монет)",
                font_size=dp(18),
                size_hint_x=0.7
            )
            comp_layout.add_widget(comp_label)
            
            btn_hire = Button(
                text='Нанять',
                size_hint_x=0.3,
                background_color=(0.2, 0.7, 0.3, 1)
            )
            btn_hire.bind(on_press=lambda x, n=name, r=role: self.hire_companion(n, r))
            comp_layout.add_widget(btn_hire)
            
            self.content_layout.add_widget(comp_layout)
    
    def claim_quest(self, quest):
        app = App.get_running_app()
        if not app.game:
            return
        
        result = quest.claim(app.game.player)
        popup = Popup(
            title='🎁 Награда получена!',
            content=Label(
                text=result,
                text_size=(None, None),
                halign='center',
                font_size=dp(18)
            ),
            size_hint=(0.7, 0.4)
        )
        popup.open()
        self.show_quests()
        # Обновляем игровой экран
        app.game_screen.update_game_state()
    
    def hire_companion(self, name, role):
        app = App.get_running_app()
        if not app.game:
            return
        
        from creatures import Companion
        role_data = Companion.ROLES.get(role, {"coins": 30})
        price = role_data["coins"]
        
        if app.game.player.coins < price:
            popup = Popup(
                title='Ошибка',
                content=Label(text=f'Недостаточно монет (нужно {price}).'),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            return
        
        app.game.player.coins -= price
        from creatures import Companion
        comp = Companion(name, role, level=max(1, app.game.player.level - 1))
        app.game.player.companions.append(comp)
        
        popup = Popup(
            title='✅ Успех',
            content=Label(
                text=f'{name} присоединился к вашей партии!\n\n'
                     f'Роль: {comp.role}\n'
                     f'HP: {comp.health}/{comp.max_health}\n'
                     f'Урон: {comp.damage}',
                text_size=(None, None),
                halign='center',
                font_size=dp(18)
            ),
            size_hint=(0.7, 0.4)
        )
        popup.open()
        self.show_companions()
        # Обновляем игровой экран
        app.game_screen.update_game_state()
    
    def on_back(self, instance):
        app = App.get_running_app()
        if app.game:
            app.game_screen.update_game_state()
        self.manager.current = 'game'


class ShopScreen(Screen):
    """Экран магазина."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        title = Label(text='🛒 МАГАЗИН', font_size=dp(36), size_hint_y=None, height=dp(60))
        layout.add_widget(title)
        
        coins_label = Label(text='', font_size=dp(20), size_hint_y=None, height=dp(40))
        layout.add_widget(coins_label)
        self.coins_label = coins_label
        
        # Вкладки
        tab_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        btn_buy = Button(text='📦 Купить', size_hint_x=0.5)
        btn_buy.bind(on_press=lambda x: self.show_buy())
        tab_layout.add_widget(btn_buy)
        
        btn_sell = Button(text='💵 Продать', size_hint_x=0.5)
        btn_sell.bind(on_press=lambda x: self.show_sell())
        tab_layout.add_widget(btn_sell)
        layout.add_widget(tab_layout)
        
        scroll = ScrollView()
        self.content_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
        self.content_layout.bind(minimum_height=self.content_layout.setter('height'))
        scroll.add_widget(self.content_layout)
        layout.add_widget(scroll)
        
        btn_back = Button(text='← Назад', size_hint_y=None, height=dp(50), font_size=dp(20))
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
        self.current_tab = 'buy'
    
    def update_shop(self):
        self.show_buy()
    
    def show_buy(self):
        self.current_tab = 'buy'
        self.content_layout.clear_widgets()
        
        app = App.get_running_app()
        if not app.game:
            return
        
        self.coins_label.text = f"Ваши монеты: {app.game.player.coins} 💰"
        
        for iid, qty in app.game.shop.stock.items():
            item = ItemDatabase.get(iid)
            if not item:
                continue
            
            q = "∞" if qty is None else str(qty)
            
            item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
            item_label = Label(
                text=f"{item.display_name()} — {item.price} монет (в наличии: {q})",
                font_size=dp(16),
                size_hint_x=0.7
            )
            item_layout.add_widget(item_label)
            
            btn_buy = Button(text='Купить', size_hint_x=0.3)
            btn_buy.bind(on_press=lambda x, item_id=iid: self.buy_item(item_id))
            item_layout.add_widget(btn_buy)
            
            self.content_layout.add_widget(item_layout)
    
    def show_sell(self):
        self.current_tab = 'sell'
        self.content_layout.clear_widgets()
        
        app = App.get_running_app()
        if not app.game:
            return
        
        self.coins_label.text = f"Ваши монеты: {app.game.player.coins} 💰"
        
        items = app.game.player.inventory.list_items()
        for item, qty in items:
            item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
            price = (item.price * qty) // 2
            item_label = Label(
                text=f"{item.display_name()} x{qty} — продать за {price} монет",
                font_size=dp(16),
                size_hint_x=0.7
            )
            item_layout.add_widget(item_label)
            
            btn_sell = Button(text='Продать', size_hint_x=0.3)
            btn_sell.bind(on_press=lambda x, item_id=item.id: self.sell_item(item_id))
            item_layout.add_widget(btn_sell)
            
            self.content_layout.add_widget(item_layout)
    
    def buy_item(self, item_id):
        app = App.get_running_app()
        if not app.game:
            return
        
        result = app.game.player.buy(app.game.shop, item_id, 1)
        popup = Popup(
            title='Результат',
            content=Label(text=result),
            size_hint=(0.6, 0.3)
        )
        popup.open()
        self.show_buy()
    
    def sell_item(self, item_id):
        app = App.get_running_app()
        if not app.game:
            return
        
        result = app.game.player.sell(app.game.shop, item_id, 1)
        popup = Popup(
            title='Результат',
            content=Label(text=result),
            size_hint=(0.6, 0.3)
        )
        popup.open()
        self.show_sell()
    
    def on_back(self, instance):
        app = App.get_running_app()
        if app.game:
            app.game_screen.update_game_state()
        self.manager.current = 'game'


class CasinoScreen(Screen):
    """Экран казино."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        # Фон казино
        with layout.canvas.before:
            Color(0.2, 0.15, 0.25, 1)  # Темно-фиолетовый фон
            self.bg_rect = Rectangle()
            layout.bind(size=lambda instance, value: setattr(self.bg_rect, 'size', instance.size),
                       pos=lambda instance, value: setattr(self.bg_rect, 'pos', instance.pos))
        
        title = Label(
            text='🎰 КАЗИНО',
            font_size=dp(40),
            size_hint_y=None,
            height=dp(70),
            color=(0.9, 0.8, 0.3, 1)
        )
        layout.add_widget(title)
        
        self.coins_label = Label(
            text='',
            font_size=dp(22),
            size_hint_y=None,
            height=dp(45),
            color=(0.9, 0.9, 0.3, 1)
        )
        layout.add_widget(self.coins_label)
        
        self.result_label = Label(
            text='',
            font_size=dp(19),
            size_hint_y=None,
            height=dp(110),
            text_size=(None, None),
            halign='center',
            valign='middle',
            color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(self.result_label)
        
        games_layout = GridLayout(cols=1, spacing=dp(12), size_hint_y=None)
        games_layout.bind(minimum_height=games_layout.setter('height'))
        
        btn_coinflip = Button(
            text='🪙 Орёл/Решка (1:1)',
            size_hint_y=None,
            height=dp(65),
            font_size=dp(22),
            background_color=(0.6, 0.4, 0.2, 1)
        )
        btn_coinflip.bind(on_press=self.on_coinflip)
        games_layout.add_widget(btn_coinflip)
        
        btn_slots = Button(
            text='🎲 Слоты',
            size_hint_y=None,
            height=dp(65),
            font_size=dp(22),
            background_color=(0.7, 0.3, 0.5, 1)
        )
        btn_slots.bind(on_press=self.on_slots)
        games_layout.add_widget(btn_slots)
        
        btn_wheel = Button(
            text='🎡 Колесо Фортуны',
            size_hint_y=None,
            height=dp(65),
            font_size=dp(22),
            background_color=(0.5, 0.3, 0.7, 1)
        )
        btn_wheel.bind(on_press=self.on_wheel)
        games_layout.add_widget(btn_wheel)
        
        layout.add_widget(games_layout)
        
        btn_back = Button(
            text='← Назад',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(22),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
    
    def update_casino(self):
        app = App.get_running_app()
        if app.game:
            self.coins_label.text = f"Ваши монеты: {app.game.player.coins} 💰"
        self.result_label.text = ''
    
    def on_coinflip(self, instance):
        self.show_bet_dialog('coinflip')
    
    def on_slots(self, instance):
        self.show_bet_dialog('slots')
    
    def on_wheel(self, instance):
        self.show_bet_dialog('wheel')
    
    def show_bet_dialog(self, game_type):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        
        bet_input = TextInput(text='10', multiline=False, input_filter='int')
        content.add_widget(Label(text='Ставка:'))
        content.add_widget(bet_input)
        
        choice_layout = None
        if game_type == 'coinflip':
            choice_layout = BoxLayout(orientation='horizontal', spacing=dp(10))
            btn_h = Button(text='Орёл (h)')
            btn_t = Button(text='Решка (t)')
            choice_layout.add_widget(btn_h)
            choice_layout.add_widget(btn_t)
            content.add_widget(choice_layout)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        
        def play(choice=None):
            try:
                bet = int(bet_input.text)
                app = App.get_running_app()
                if not app.game:
                    return
                
                from shop_casino import Casino
                
                if game_type == 'coinflip':
                    if choice is None:
                        popup.dismiss()
                        return
                    ok, payout, msg = Casino.coinflip(bet, choice)
                    app.game.player.coins += payout
                    self.result_label.text = msg
                elif game_type == 'slots':
                    res, payout = Casino.slots(bet)
                    app.game.player.coins += payout
                    self.result_label.text = res
                elif game_type == 'wheel':
                    lab, payout = Casino.wheel(bet)
                    app.game.player.coins += payout
                    self.result_label.text = lab
                
                self.update_casino()
                popup.dismiss()
            except ValueError:
                pass
        
        if game_type == 'coinflip':
            btn_h.bind(on_press=lambda x: play('h'))
            btn_t.bind(on_press=lambda x: play('t'))
        else:
            btn_play = Button(text='Играть')
            btn_play.bind(on_press=lambda x: play())
            btn_layout.add_widget(btn_play)
        
        btn_cancel = Button(text='Отмена')
        btn_cancel.bind(on_press=lambda x: popup.dismiss())
        btn_layout.add_widget(btn_cancel)
        
        if game_type != 'coinflip':
            content.add_widget(btn_layout)
        
        popup = Popup(
            title=f'🎰 {game_type}',
            content=content,
            size_hint=(0.7, 0.5)
        )
        popup.open()
    
    def on_back(self, instance):
        app = App.get_running_app()
        if app.game:
            app.game_screen.update_game_state()
        self.manager.current = 'game'


class InventoryScreen(Screen):
    """Экран инвентаря."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        # Фон инвентаря
        with layout.canvas.before:
            Color(0.18, 0.22, 0.28, 1)
            self.bg_rect = Rectangle()
            layout.bind(size=lambda instance, value: setattr(self.bg_rect, 'size', instance.size),
                       pos=lambda instance, value: setattr(self.bg_rect, 'pos', instance.pos))
        
        title = Label(
            text='🎒 ИНВЕНТАРЬ',
            font_size=dp(40),
            size_hint_y=None,
            height=dp(70),
            color=(0.9, 0.8, 0.3, 1)
        )
        layout.add_widget(title)
        
        self.equipment_label = Label(
            text='',
            font_size=dp(19),
            size_hint_y=None,
            height=dp(85),
            text_size=(None, None),
            halign='left',
            valign='top',
            color=(0.9, 0.9, 0.9, 1)
        )
        layout.add_widget(self.equipment_label)
        
        scroll = ScrollView()
        self.items_layout = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None)
        self.items_layout.bind(minimum_height=self.items_layout.setter('height'))
        scroll.add_widget(self.items_layout)
        layout.add_widget(scroll)
        
        btn_back = Button(
            text='← Назад',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(22),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
    
    def update_inventory(self):
        app = App.get_running_app()
        if not app.game:
            return
        
        p = app.game.player
        
        # Экипировка
        weapon_name = p.weapon.name if p.weapon else 'Нет'
        armor_name = p.armor.name if p.armor else 'Нет'
        self.equipment_label.text = (
            f"⚔️ Оружие: {weapon_name}\n"
            f"🛡️ Броня: {armor_name}"
        )
        
        # Предметы
        self.items_layout.clear_widgets()
        items = p.inventory.list_items()
        for item, qty in items:
            item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(60))
            item_label = Label(
                text=f"{item.display_name()} x{qty}",
                font_size=dp(16),
                size_hint_x=0.7
            )
            item_layout.add_widget(item_label)
            
            btn_layout = BoxLayout(orientation='horizontal', size_hint_x=0.3, spacing=dp(5))
            
            if isinstance(item, Weapon) or isinstance(item, Armor):
                btn_equip = Button(text='Экипировать', size_hint_x=0.5)
                btn_equip.bind(on_press=lambda x, it=item: self.equip_item(it))
                btn_layout.add_widget(btn_equip)
            
            if (p.weapon and p.weapon.id == item.id) or (p.armor and p.armor.id == item.id):
                btn_unequip = Button(text='Снять', size_hint_x=0.5)
                btn_unequip.bind(on_press=lambda x, it=item: self.unequip_item(it))
                btn_layout.add_widget(btn_unequip)
            
            item_layout.add_widget(btn_layout)
            self.items_layout.add_widget(item_layout)
    
    def equip_item(self, item):
        app = App.get_running_app()
        if not app.game:
            return
        
        if isinstance(item, Weapon):
            if app.game.player.equip_weapon(item):
                popup = Popup(
                    title='Успех',
                    content=Label(text=f'✅ Экипировано {item.display_name()}'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
            else:
                popup = Popup(
                    title='Ошибка',
                    content=Label(text='Не удалось экипировать. Проверьте инвентарь.'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
        elif isinstance(item, Armor):
            if app.game.player.equip_armor(item):
                popup = Popup(
                    title='Успех',
                    content=Label(text=f'✅ Экипировано {item.display_name()}'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
            else:
                popup = Popup(
                    title='Ошибка',
                    content=Label(text='Не удалось экипировать. Проверьте инвентарь.'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
        
        self.update_inventory()
    
    def unequip_item(self, item):
        app = App.get_running_app()
        if not app.game:
            return
        
        if isinstance(item, Weapon):
            if app.game.player.unequip_weapon():
                popup = Popup(
                    title='Успех',
                    content=Label(text='✅ Оружие снято.'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
        elif isinstance(item, Armor):
            if app.game.player.unequip_armor():
                popup = Popup(
                    title='Успех',
                    content=Label(text='✅ Броня снята.'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
        
        self.update_inventory()
    
    def on_back(self, instance):
        app = App.get_running_app()
        if app.game:
            app.game_screen.update_game_state()
        self.manager.current = 'game'


class BattleInventoryScreen(Screen):
    """Экран инвентаря в бою."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.battlefield = None
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        title = Label(text='🎒 ИНВЕНТАРЬ В БОЮ', font_size=dp(32), size_hint_y=None, height=dp(60))
        layout.add_widget(title)
        
        # Информация о персонаже
        self.player_info = Label(
            text='',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(80),
            text_size=(None, None),
            halign='left',
            valign='top'
        )
        layout.add_widget(self.player_info)
        
        # Экипировка
        self.equipment_label = Label(text='', font_size=dp(18), size_hint_y=None, height=dp(60))
        layout.add_widget(self.equipment_label)
        
        scroll = ScrollView()
        self.items_layout = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None)
        self.items_layout.bind(minimum_height=self.items_layout.setter('height'))
        scroll.add_widget(self.items_layout)
        layout.add_widget(scroll)
        
        btn_back = Button(text='← Назад в бой', size_hint_y=None, height=dp(50), font_size=dp(20))
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
    
    def update_inventory(self, battlefield):
        """Обновление инвентаря для боя."""
        self.battlefield = battlefield
        if not battlefield:
            return
        
        p = battlefield.player
        
        # Информация о персонаже
        self.player_info.text = (
            f"HP: {p.health}/{p.max_health} | "
            f"DMG: {p.damage} | DEF: {p.defense}"
        )
        
        # Экипировка
        weapon_name = p.weapon.name if p.weapon else 'Нет'
        armor_name = p.armor.name if p.armor else 'Нет'
        self.equipment_label.text = (
            f"Оружие: {weapon_name} | Броня: {armor_name}"
        )
        
        # Предметы
        self.items_layout.clear_widgets()
        items = p.inventory.list_items()
        
        for item, qty in items:
            item_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(70))
            
            # Информация о предмете
            item_info = BoxLayout(orientation='vertical', size_hint_x=0.6, spacing=dp(2))
            item_name = Label(
                text=f"{item.display_name()} x{qty}",
                font_size=dp(16),
                text_size=(None, None),
                halign='left',
                valign='top'
            )
            item_info.add_widget(item_name)
            
            # Описание для зелий
            if isinstance(item, Potion):
                desc = Label(
                    text=f"Восстанавливает {item.heal_amount} HP",
                    font_size=dp(12),
                    text_size=(None, None),
                    halign='left',
                    valign='top',
                    color=(0.7, 0.9, 0.7, 1)
                )
                item_info.add_widget(desc)
            
            item_layout.add_widget(item_info)
            
            # Кнопки действий
            btn_layout = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=dp(5))
            
            # Для зелий - кнопка "Использовать"
            if isinstance(item, Potion):
                btn_use = Button(
                    text='Использовать',
                    size_hint_y=None,
                    height=dp(30),
                    font_size=dp(14)
                )
                btn_use.bind(on_press=lambda x, it=item: self.use_item(it))
                btn_layout.add_widget(btn_use)
            
            # Для оружия и брони - кнопки экипировки
            if isinstance(item, Weapon) or isinstance(item, Armor):
                btn_equip = Button(
                    text='Экипировать',
                    size_hint_y=None,
                    height=dp(30),
                    font_size=dp(14)
                )
                btn_equip.bind(on_press=lambda x, it=item: self.equip_item(it))
                btn_layout.add_widget(btn_equip)
            
            # Кнопка снятия экипировки
            if (p.weapon and p.weapon.id == item.id) or (p.armor and p.armor.id == item.id):
                btn_unequip = Button(
                    text='Снять',
                    size_hint_y=None,
                    height=dp(30),
                    font_size=dp(14)
                )
                btn_unequip.bind(on_press=lambda x, it=item: self.unequip_item(it))
                btn_layout.add_widget(btn_unequip)
            
            item_layout.add_widget(btn_layout)
            self.items_layout.add_widget(item_layout)
    
    def use_item(self, item):
        """Использование предмета в бою."""
        if not self.battlefield:
            return
        
        if not isinstance(item, Potion):
            popup = Popup(
                title='Ошибка',
                content=Label(text='Этот предмет нельзя использовать в бою.'),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            return
        
        # Используем зелье
        result = self.battlefield.use_item(item.id)
        
        # Обновляем инвентарь
        self.update_inventory(self.battlefield)
        
        # Показываем результат
        popup = Popup(
            title='Результат',
            content=Label(text=result),
            size_hint=(0.6, 0.3)
        )
        popup.open()
        
        # Возвращаемся в бой
        Clock.schedule_once(lambda dt: self.return_to_battle(), 1.0)
    
    def equip_item(self, item):
        """Экипировка предмета в бою."""
        if not self.battlefield:
            return
        
        p = self.battlefield.player
        
        if isinstance(item, Weapon):
            if p.equip_weapon(item):
                popup = Popup(
                    title='Успех',
                    content=Label(text=f'✅ Экипировано {item.display_name()}'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
                self.update_inventory(self.battlefield)
            else:
                popup = Popup(
                    title='Ошибка',
                    content=Label(text='Не удалось экипировать. Проверьте инвентарь.'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
        elif isinstance(item, Armor):
            if p.equip_armor(item):
                popup = Popup(
                    title='Успех',
                    content=Label(text=f'✅ Экипировано {item.display_name()}'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
                self.update_inventory(self.battlefield)
            else:
                popup = Popup(
                    title='Ошибка',
                    content=Label(text='Не удалось экипировать. Проверьте инвентарь.'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
    
    def unequip_item(self, item):
        """Снятие экипировки в бою."""
        if not self.battlefield:
            return
        
        p = self.battlefield.player
        
        if isinstance(item, Weapon):
            if p.unequip_weapon():
                popup = Popup(
                    title='Успех',
                    content=Label(text='✅ Оружие снято.'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
                self.update_inventory(self.battlefield)
        elif isinstance(item, Armor):
            if p.unequip_armor():
                popup = Popup(
                    title='Успех',
                    content=Label(text='✅ Броня снята.'),
                    size_hint=(0.6, 0.3)
                )
                popup.open()
                self.update_inventory(self.battlefield)
    
    def return_to_battle(self):
        """Возврат в бой после использования предмета."""
        app = App.get_running_app()
        battle_screen = app.battle_screen
        
        # Обновляем отображение боя
        battle_screen.update_battle_display()
        
        # Если бой не закончен, продолжаем ход врагов
        if not battle_screen.battlefield.is_over():
            battle_screen.is_processing_turn = True
            battle_screen.update_battle_display()
            Clock.schedule_once(lambda dt: battle_screen.enemy_turn(), 1.0)
        else:
            battle_screen.is_processing_turn = False
            battle_screen.end_battle()
        
        self.manager.current = 'battle'
    
    def on_back(self, instance):
        """Возврат в бой без действий."""
        self.manager.current = 'battle'


class StatusScreen(Screen):
    """Экран статуса."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        # Фон статуса
        with layout.canvas.before:
            Color(0.15, 0.2, 0.25, 1)
            self.bg_rect = Rectangle()
            layout.bind(size=lambda instance, value: setattr(self.bg_rect, 'size', instance.size),
                       pos=lambda instance, value: setattr(self.bg_rect, 'pos', instance.pos))
        
        title = Label(
            text='📊 СТАТУС',
            font_size=dp(40),
            size_hint_y=None,
            height=dp(70),
            color=(0.9, 0.8, 0.3, 1)
        )
        layout.add_widget(title)
        
        scroll = ScrollView()
        self.status_label = Label(
            text='',
            font_size=dp(19),
            size_hint_y=None,
            text_size=(None, None),
            halign='left',
            valign='top',
            color=(0.9, 0.9, 0.9, 1)
        )
        self.status_label.bind(texture_size=self.status_label.setter('size'))
        scroll.add_widget(self.status_label)
        layout.add_widget(scroll)
        
        btn_back = Button(
            text='← Назад',
            size_hint_y=None,
            height=dp(55),
            font_size=dp(22),
            background_color=(0.5, 0.5, 0.5, 1)
        )
        btn_back.bind(on_press=self.on_back)
        layout.add_widget(btn_back)
        
        self.add_widget(layout)
    
    def update_status(self):
        app = App.get_running_app()
        if not app.game:
            return
        
        p = app.game.player
        stats = p.get_session_stats()
        
        # Прогресс до следующего уровня
        xp_progress = (p.experience / (p.level * 100)) * 100 if p.level > 0 else 0
        
        text = (
            f"═══════════════════════════════════\n"
            f"👤 ПЕРСОНАЖ\n"
            f"═══════════════════════════════════\n"
            f"Имя: {p.name}\n"
            f"Класс: {p.CLASS_STATS[p.cls]['name']}\n"
            f"Уровень: {p.level} ⭐\n"
            f"День: {app.game.day} 📅\n\n"
            f"═══════════════════════════════════\n"
            f"💚 ХАРАКТЕРИСТИКИ\n"
            f"═══════════════════════════════════\n"
            f"HP: {p.health}/{p.max_health}\n"
            f"Урон: {p.damage} ⚔️\n"
            f"Защита: {p.defense} 🛡️\n\n"
            f"═══════════════════════════════════\n"
            f"💰 РЕСУРСЫ\n"
            f"═══════════════════════════════════\n"
            f"Монеты: {p.coins} 💰\n"
            f"Опыт: {p.experience}/{p.level*100} ({int(xp_progress)}%) ✨\n\n"
        )
        
        # Экипировка
        weapon_name = p.weapon.name if p.weapon else "Нет"
        armor_name = p.armor.name if p.armor else "Нет"
        text += (
            f"═══════════════════════════════════\n"
            f"⚔️ ЭКИПИРОВКА\n"
            f"═══════════════════════════════════\n"
            f"Оружие: {weapon_name}\n"
            f"Броня: {armor_name}\n\n"
        )
        
        # Спутники
        text += (
            f"═══════════════════════════════════\n"
            f"🤝 СПУТНИКИ\n"
            f"═══════════════════════════════════\n"
        )
        if not p.companions:
            text += "  (Нет спутников)\n\n"
        else:
            for c in p.companions:
                status = "✅ Жив" if c.is_alive else "💀 Мертв"
                text += f"  • {c.name} ({c.role})\n"
                text += f"    HP: {c.health}/{c.max_health} | DMG: {c.damage} | {status}\n"
            text += "\n"
        
        # Статистика сессии
        text += (
            f"═══════════════════════════════════\n"
            f"📊 СТАТИСТИКА СЕССИИ\n"
            f"═══════════════════════════════════\n"
            f"Врагов повержено: {stats['enemies_defeated']} 💀\n"
            f"Битв проведено: {stats['battles_fought']} ⚔️\n"
            f"Выданный урон: {stats['total_damage_dealt']} 🔥\n"
            f"Полученный урон: {stats['total_damage_taken']} 🛡️\n"
            f"Предметов в инвентаре: {stats['inventory_items']} 🎒\n\n"
        )
        
        # История
        text += (
            f"═══════════════════════════════════\n"
            f"📜 ПОСЛЕДНИЕ СОБЫТИЯ\n"
            f"═══════════════════════════════════\n"
        )
        if not app.game.history:
            text += "  (Нет событий)\n"
        else:
            for h in app.game.history[-8:]:
                text += f"  • {h}\n"
        
        self.status_label.text = text
    
    def on_back(self, instance):
        self.manager.current = 'game'


class RPGApp(App):
    """Главное приложение."""
    
    def build(self):
        sm = ScreenManager()
        
        # Создаём экраны
        main_menu = MainMenuScreen(name='main_menu')
        sm.add_widget(main_menu)
        
        character_creation = CharacterCreationScreen(name='character_creation')
        sm.add_widget(character_creation)
        
        load_game_screen = LoadGameScreen(name='load_game')
        sm.add_widget(load_game_screen)
        
        game_screen = GameScreen(name='game')
        sm.add_widget(game_screen)
        self.game_screen = game_screen
        
        battle_screen = BattleScreen(name='battle')
        sm.add_widget(battle_screen)
        self.battle_screen = battle_screen
        
        battle_inventory_screen = BattleInventoryScreen(name='battle_inventory')
        sm.add_widget(battle_inventory_screen)
        self.battle_inventory_screen = battle_inventory_screen
        
        tavern_screen = TavernScreen(name='tavern')
        sm.add_widget(tavern_screen)
        self.tavern_screen = tavern_screen
        
        shop_screen = ShopScreen(name='shop')
        sm.add_widget(shop_screen)
        self.shop_screen = shop_screen
        
        casino_screen = CasinoScreen(name='casino')
        sm.add_widget(casino_screen)
        self.casino_screen = casino_screen
        
        inventory_screen = InventoryScreen(name='inventory')
        sm.add_widget(inventory_screen)
        self.inventory_screen = inventory_screen
        
        status_screen = StatusScreen(name='status')
        sm.add_widget(status_screen)
        self.status_screen = status_screen
        
        self.game = None
        
        return sm


if __name__ == '__main__':
    RPGApp().run()

