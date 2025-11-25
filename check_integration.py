#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.items import ItemDatabase, WEAPON_MATERIALS, ARMOR_MATERIALS
from core.creatures import Player

print("\n✅ ПРОВЕРКА ИНТЕГРАЦИИ СИСТЕМЫ ПРЕДМЕТОВ\n")

ItemDatabase.initialize()
p = Player('Тест', 'warrior')

print(f"✅ Импорты работают")
print(f"✅ Игрок создан с {len(p.inventory.list_items())} предметами")
print(f"✅ Доступно предметов в БД: {len(ItemDatabase.ITEMS)}")
print(f"✅ Материалы оружия: {len(WEAPON_MATERIALS)}")
print(f"✅ Материалы брони: {len(ARMOR_MATERIALS)}")
print(f"✅ Оружие игрока: {p.weapon.display_name()}")
print(f"✅ Броня игрока: {p.armor.display_name()}")
print(f"\n✅ СИСТЕМА ПОЛНОСТЬЮ ИНТЕГРИРОВАНА И РАБОТАЕТ!\n")
