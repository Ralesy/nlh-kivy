#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экраны Kivy-приложения."""

from ui.screens.battle import BattleScreen
from ui.screens.main_menu import MainMenuScreen
from ui.screens.character_creation import CharacterCreationScreen
from ui.screens.load_game import LoadGameScreen
from ui.screens.shop import ShopScreen
from ui.screens.inventory import InventoryScreen, BattleInventoryScreen
from ui.screens.game_screen import GameScreen
from ui.screens.tavern import TavernScreen
from ui.screens.status import StatusScreen
from ui.screens.location_select import LocationSelectScreen
from ui.screens.ancient_cave_boss import AncientCaveBossSelectScreen
from ui.screens.npc_dialogue import NPCDialogueScreen
from ui.screens.loot_window_screen import LootWindowScreen
from ui.screens.companion_management import CompanionManagementScreen
from ui.screens.active_quests import ActiveQuestsScreen
from ui.screens.city_menu import CityMenuScreen

__all__ = [
    "BattleScreen",
    "MainMenuScreen",
    "CharacterCreationScreen",
    "LoadGameScreen",
    "ShopScreen",
    "InventoryScreen",
    "BattleInventoryScreen",
    "GameScreen",
    "TavernScreen",
    "StatusScreen",
    "LocationSelectScreen",
    "AncientCaveBossSelectScreen",
    "NPCDialogueScreen",
    "LootWindowScreen",
    "CompanionManagementScreen",
    "ActiveQuestsScreen",
    "CityMenuScreen",
]
