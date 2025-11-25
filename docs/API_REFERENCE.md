#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Reference - примеры использования модулей
"""

# ============ ITEMS (Предметы) ============

"""
from items import ItemDatabase, Weapon, Armor, Potion, Inventory

# Инициализация базы данных
ItemDatabase.initialize()

# Получить предмет по ID
sword = ItemDatabase.get("w_sword")
print(sword.display_name())  # 🔵 Одноручный меч [w_sword] (Uncommon)

# Найти предметы по редкости
rare_items = ItemDatabase.find_by_rarity("Rare")

# Работа с инвентарём
inv = Inventory(capacity=40)
inv.add(sword, 1)
inv.add(ItemDatabase.get("p_small"), 5)

# Получить предмет из инвентаря
item = inv.get("w_sword")
qty = inv.qty("p_small")  # 5

# Вывести инвентарь
print(inv)

# Удалить предмет
inv.remove("p_small", 2)
"""

# ============ CREATURES (Существа) ============

"""
from creatures import Player, Companion
from items import ItemDatabase

ItemDatabase.initialize()

# Создать игрока
player = Player("Герой", "warrior")

# Получить характеристики
print(player.level)      # 1
print(player.health)     # current HP
print(player.max_health) # max HP
print(player.damage)     # with equipment
print(player.defense)    # with equipment

# Управление здоровьем
player.heal(50)
player.take_damage(30)

# Получить/потратить опыт
msgs = player.add_experience(100)

# Найм спутника
companion = Companion("Thorg", "tank", level=player.level)
player.companions.append(companion)

# Получить статистику
stats = player.get_session_stats()
"""

# ============ BATTLE (Боевая система) ============

"""
from battle import Battlefield, EnemyGenerator, EventSystem
from creatures import Player
from items import ItemDatabase

ItemDatabase.initialize()
player = Player("Герой", "warrior")

# Генерирование врагов
enemies = EnemyGenerator.generate("forest", player.level, num=2)

# Создание боевого поля
bf = Battlefield(player, enemies)

# Атака игрока
damage_msg = bf.player_attack(0)  # атаковать первого врага

# Враги атакуют
logs = bf.enemy_turn()
for log in logs:
    print(log)

# Попытка бегства
success, logs = bf.attempt_escape()

# События
event = EventSystem.roll_forest(player)
"""

# ============ QUESTS (Квесты) ============

"""
from quests import Quest, Tavern
from creatures import Player
from items import ItemDatabase

ItemDatabase.initialize()
player = Player("Герой", "warrior")

# Работа с тавер ной
tavern = Tavern()

# Получить квест
quest = tavern.get_quest("q_kill_wolves")

# Проверить статус
print(quest.progress_display())  # 0/3

# Регистрация убийства
quest.register_kill("Волк")
quest.register_kill("Волк")
quest.register_kill("Волк")

# Получить награду
reward = quest.claim(player)

# Список квестов
print(tavern.list_quests())

# Получить спутника
name, role = tavern.get_random_companion()
"""

# ============ SHOP & CASINO (Магазин и казино) ============

"""
from shop_casino import Shop, Casino
from creatures import Player
from items import ItemDatabase

ItemDatabase.initialize()
player = Player("Герой", "warrior")

# Магазин
stock = {"w_sword": 5, "a_leather": 10, "p_small": 20}
shop = Shop(stock)

# Покупка
msg = player.buy(shop, "w_sword", 1)
# Продажа
msg = player.sell(shop, "p_small", 1)

# Обновление стока
shop.refresh()

# Казино
# Орёл/Решка
ok, payout, msg = Casino.coinflip(100, "h")
player.coins += payout

# Слоты
result, payout = Casino.slots(50)
player.coins += payout

# Колесо
result, payout = Casino.wheel(25)
player.coins += payout
"""

# ============ SAVE SYSTEM (Система сохранений) ============

"""
from save_system import save_game, load_game, get_save_list, delete_save
from creatures import Player

# Создать игрока
player = Player("Герой", "warrior")
# ...игра...

# Сохранить
success = save_game(player, "my_save_1")

# Загрузить
player = load_game("my_save_1")

# Получить список сохранений
saves = get_save_list()  # ['my_save_1', 'my_save_2']

# Удалить
delete_save("my_save_1")
"""

# ============ UTILS (Вспомогательные функции) ============

"""
from utils import (
    clamp, pause, rnd_choice_weighted,
    rarity_weighted_choice, RARITIES,
    print_header, print_section
)

# Математика
x = clamp(50, 0, 100)  # 50
x = clamp(-5, 0, 100)  # 0

# Пауза
pause(0.5)

# Случайный выбор с весами
items = [("Common", 0.5), ("Rare", 0.3), ("Epic", 0.2)]
result = rnd_choice_weighted(items)

# Редкость
rarity = rarity_weighted_choice()

# Вывод
print_header("Заголовок")
print_section("Подзаголовок")
"""

# ============ GAME (Главная игра) ============

"""
from game import Game
from items import ItemDatabase

# Инициализация
ItemDatabase.initialize()
game = Game()

# Создание персонажа
game.create_character()

# Главное меню
game.main_menu()

# Вход в локацию
game.enter_location("forest")

# Посещение таверны
game.visit_tavern()

# Магазин
game.run_shop()

# Казино
game.run_casino()

# Сохранение
game.save_game_prompt()
"""
