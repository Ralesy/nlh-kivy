#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kivy UI для RPG игры.
"""

from kivy.app import App
from kivy.config import Config

# Set fullscreen mode and window size before importing Window
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'multisampling', '0')

from kivy.core.window import Window

# Disable the window padding/margins that cause black bars
Window.clearcolor = (0, 0, 0, 1)

from kivy.uix.screenmanager import ScreenManager
from kivy.uix.floatlayout import FloatLayout

from ui.local_location_screen import LocalLocationScreen
from ui.widgets.game_hud import GameHUD
from ui.bindings.player_observer import PlayerViewModel
from systems.npcs import NPCManager

from ui.screens import (
    MainMenuScreen,
    CharacterCreationScreen,
    LoadGameScreen,
    GameScreen,
    BattleScreen,
    BattleInventoryScreen,
    TavernScreen,
    ShopScreen,
    CityMenuScreen,
    InventoryScreen,
    StatusScreen,
    LocationSelectScreen,
    AncientCaveBossSelectScreen,
    NPCDialogueScreen,
    LootWindowScreen,
    CompanionManagementScreen,
    ActiveQuestsScreen,
)


class RPGApp(App):
    """Главное Kivy-приложение."""

    def __init__(self, **kwargs):
        """Инициализировать приложение и контейнер сессии."""
        super().__init__(**kwargs)
        self._session = None
        self.player_view = PlayerViewModel()

    @property
    def session(self):
        """Активная игровая сессия."""
        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    @property
    def game(self):
        """Alias для session (обратная совместимость экранов)."""
        return self._session

    @game.setter
    def game(self, value):
        self._session = value

    def bind_session_player(self, player) -> None:
        """Привязать игрока к HUD и PlayerViewModel."""
        try:
            if getattr(self, 'player_view', None):
                self.player_view.bind_player(player)
            if getattr(self, 'hud', None):
                self.hud._bound_player = player
                self.hud.bind_to_view_model(self.player_view)
        except Exception:
            pass

    def unbind_session_player(self) -> None:
        """Отвязать игрока от UI-моделей."""
        try:
            if getattr(self, 'player_view', None):
                self.player_view.unbind_player()
            if getattr(self, 'hud', None):
                self.hud.unbind_player()
        except Exception:
            pass

    def build(self):
        """Собрать дерево экранов и HUD."""
        sm = ScreenManager()
        sm.size_hint = (1, 1)
        sm.pos_hint = {'x': 0, 'y': 0}

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

        city_menu_screen = CityMenuScreen(name='city_menu')
        sm.add_widget(city_menu_screen)
        self.city_menu_screen = city_menu_screen

        inventory_screen = InventoryScreen(name='inventory')
        sm.add_widget(inventory_screen)
        self.inventory_screen = inventory_screen

        status_screen = StatusScreen(name='status')
        sm.add_widget(status_screen)
        self.status_screen = status_screen

        location_select_screen = LocationSelectScreen(name='location_select')
        sm.add_widget(location_select_screen)
        self.location_select_screen = location_select_screen

        ancient_cave_boss_screen = AncientCaveBossSelectScreen(name='ancient_cave_boss')
        sm.add_widget(ancient_cave_boss_screen)
        self.ancient_cave_boss_screen = ancient_cave_boss_screen

        npc_dialogue_screen = NPCDialogueScreen(name='npc_dialogue')
        sm.add_widget(npc_dialogue_screen)
        self.npc_dialogue_screen = npc_dialogue_screen

        loot_window_screen = LootWindowScreen(name='loot_window')
        sm.add_widget(loot_window_screen)
        self.loot_window_screen = loot_window_screen

        companion_management_screen = CompanionManagementScreen(name='companion_management')
        sm.add_widget(companion_management_screen)
        self.companion_management_screen = companion_management_screen

        active_quests_screen = ActiveQuestsScreen(name='active_quests')
        sm.add_widget(active_quests_screen)
        self.active_quests_screen = active_quests_screen

        local_location_screen = LocalLocationScreen(name='local_location')
        sm.add_widget(local_location_screen)
        self.local_location_screen = local_location_screen

        self.npc_manager = NPCManager()
        self.return_to_local_location = False
        self.local_scene_id = None
        # Экран, на который вернуться из инвентаря (задаётся при открытии).
        self.inventory_return_screen = "location_select"

        root = FloatLayout()
        root.size_hint = (1, 1)
        root.pos_hint = {'x': 0, 'y': 0}
        root.add_widget(sm)

        try:
            self.hud = GameHUD()
            root.add_widget(self.hud)
            sm.bind(current=self.on_screen_change)
        except Exception:
            pass

        return root

    def on_screen_change(self, instance, value):
        """Обновить HUD при смене экрана."""
        try:
            if getattr(self, 'hud', None):
                self.hud.update()
        except Exception:
            pass


if __name__ == '__main__':
    RPGApp().run()
