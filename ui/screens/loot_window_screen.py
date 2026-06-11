#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран добычи после боя."""

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from ui.ui_styles import COLORS

class LootWindowScreen(Screen):
    """Окно добычи после боя."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.battle_result = None
        
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
        title_layout = BoxLayout(size_hint_y=None, spacing=dp(20))
        title_layout.height = dp(60)
        
        title = Label(
            text='⚔️ ПОБЕДА! 🏆',
            font_size=dp(28),
            color=(0.9, 0.7, 0.1, 1),
            bold=True
        )
        title_layout.add_widget(title)
        main_layout.add_widget(title_layout)
        
        # Статистика боя
        stats_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(10)
        )
        stats_layout.height = dp(80)
        
        self.stats_label = Label(
            text='',
            size_hint_y=None,
            height=dp(70),
            text_size=(None, None),
            halign='center',
            valign='center',
            font_size=dp(16)
        )
        stats_layout.add_widget(self.stats_label)
        main_layout.add_widget(stats_layout)
        
        # Предметы добычи
        loot_title = Label(
            text='📦 ДОБЫЧА:',
            size_hint_y=None,
            height=dp(40),
            font_size=dp(20),
            color=(0.7, 0.9, 0.7, 1),
            bold=True
        )
        main_layout.add_widget(loot_title)
        
        scroll = ScrollView(size_hint=(1, 0.4))
        self.loot_layout = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(10)
        )
        self.loot_layout.bind(
            minimum_height=self.loot_layout.setter('height')
        )
        scroll.add_widget(self.loot_layout)
        main_layout.add_widget(scroll)
        
        # Кнопка продолжения
        btn_layout = BoxLayout(
            spacing=dp(10),
            size_hint_y=None
        )
        btn_layout.height = dp(50)
        
        btn_continue = Button(
            text='➜ Продолжить',
            background_color=COLORS['hp_green']
        )
        btn_continue.bind(on_press=self.on_continue)
        btn_layout.add_widget(btn_continue)
        
        main_layout.add_widget(btn_layout)
        self.add_widget(main_layout)
    
    def show_loot(self, battle_result):
        """Показать окно выбора лута (Mount & Blade style:))."""
        from ui.loot_window import LootWindow
        app = App.get_running_app()
        print(f"[DEBUG] Setting app.battle_result = {battle_result}")
        app.battle_result = battle_result
        self.clear_widgets()
        app = App.get_running_app()
        player_inventory = (
            app.game.player.inventory
            if app and app.game and app.game.player
            else None
        )
        loot_items = (
            battle_result.loot
            if battle_result.loot
            else []
        )

        def on_done(selected):
            # Предметы уже добавлены при нажатии на
            # каждую кнопку "Взять"
            # Добавляем золото и опыт
            app.game.player.coins += (
                battle_result.gold_earned
            )
            app.game.player.add_experience(
                battle_result.xp_earned
            )
            # Обновляем карту/списки перед переходом
            try:
                if hasattr(app, 'location_select_screen'):
                    app.location_select_screen.update_locations()
            except Exception:
                pass
            # If this battle originated from a local location, return to that local map
            try:
                if getattr(app, '_battle_from_local_location', False) and getattr(app, 'local_location_screen', None):
                    # notify local screen about return so it can mark defeated enemy and resume
                    try:
                        app.local_location_screen.on_return_from_battle()
                    except Exception:
                        pass
                    app._battle_from_local_location = False
                    self.manager.current = 'local_location'
                    return
            except Exception:
                pass
            # Переходим на глобальную карту
            self.manager.current = 'location_select'

        loot_window = LootWindow(
            loot_items,
            player_inventory,
            on_done,
            gold=battle_result.gold_earned,
            xp=battle_result.xp_earned
        )
        self.add_widget(loot_window)

    
    def _format_loot_item(self, loot_drop):
        """Форматировать предмет добычи."""
        item = loot_drop.item
        if not item:
            return "— Никакого предмета"
        
        text = f"📦 {item.name}"
        if hasattr(item, 'material'):
            text += f" ({item.material})"
        if hasattr(item, 'condition'):
            text += f" [{item.condition}]"
        
        return text
    
    def on_continue(self, instance):
        """Продолжить игру."""
        app = App.get_running_app()
        
        # Добавить добычу в инвентарь
        if self.battle_result:
            player = app.game.player
            for loot in self.battle_result.loot:
                if loot.item:
                    player.inventory.add(loot.item, 1)
            
            player.coins += self.battle_result.gold_earned
            # Add experience and trigger level-ups
            player.add_experience(self.battle_result.xp_earned)

            # Обновляем магазин по новым разблокировкам
            try:
                app.game.refresh_shop()
                # Обновляем экран магазина, чтобы данные были готовы
                if getattr(app, 'shop_screen', None):
                    app.shop_screen.update_shop()
            except Exception:
                pass
        
        # If this battle originated from a local location, return to that local map
        try:
            if getattr(app, '_battle_from_local_location', False) and getattr(app, 'local_location_screen', None):
                # notify local screen about return so it can mark defeated enemy and resume
                try:
                    app.local_location_screen.on_return_from_battle()
                except Exception:
                    pass
                app._battle_from_local_location = False
                self.manager.current = 'local_location'
                return
        except Exception:
            pass

        self.manager.current = 'location_select'
