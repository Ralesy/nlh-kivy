#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Game: главный модуль игры с интерфейсом и менеджментом.
Переработан для новой системы локаций, NPC и дропа.
"""

import random
import sys
from typing import Optional
from creatures import Player
from items import ItemDatabase, Weapon, Armor
from battle import (
    Battlefield, EnemyGenerator, EventSystem, BattleResult
)
from quests import Tavern
from shop_casino import Shop, Casino
from save_system import save_game, load_game, get_save_list
from locations import LocationManager
from npcs import NPCManager, GeneratedQuest
from enemies import EnemyDatabase
from utils import print_header, print_section, pause


class Game:
    """Главный класс игры."""

    def __init__(self):
        """Инициализация игры."""
        self.player: Optional[Player] = None
        self.tavern = Tavern()
        self.location_manager = LocationManager()
        self.npc_manager = NPCManager()

        # Инициализация магазина (обновленный сток)
        base_stock = {
            "w_iron_sword": 5, "w_steel_sword": 2,
            "a_leather_armor": 5, "a_iron_plate": 2,
            "a_steel_plate": 1,
            "p_small": 15, "p_med": 8, "p_large": 3
        }
        self.shop = Shop(base_stock)

        self.day = 1
        self.running = True
        self.history: list = []
        self.wins_in_row = 0

    def create_character(self) -> None:
        """Создание персонажа."""
        print_header("Создание персонажа")
        name = input("Введите имя персонажа: ").strip() or "Герой"
        print("\nВыберите класс:")
        print("1) Воин (Макс HP, средний урон)")
        print("2) Маг (Макс урон, меньше HP)")
        print("3) Лучник (Баланс)")
        c = input("\n> ").strip()
        cls = {"1": "warrior", "2": "mage", "3": "archer"}.get(
            c, "warrior"
        )
        self.player = Player(name, cls)

        # Начальные ресурсы
        self.player.coins += 200
        sword = ItemDatabase.get("w_iron_sword")
        armor = ItemDatabase.get("a_leather_armor")
        potion = ItemDatabase.get("p_small")
        
        if sword:
            self.player.inventory.add(sword, 1)
            self.player.equip_weapon(sword)
        if armor:
            self.player.inventory.add(armor, 1)
            self.player.equip_armor(armor)
        if potion:
            self.player.inventory.add(potion, 3)

        print(f"\nПерсонаж создан: {self.player.name} ({self.player.cls})")
        print(f"HP: {self.player.health} | DMG: {self.player.damage} "
              f"| DEF: {self.player.defense}")
        pause(1)

    def main_menu(self) -> None:
        """Главное меню."""
        while self.running:
            print("\n" + "=" * 60)
            print(f"День {self.day} | Уровень {self.player.level} | "
                  f"💰 {self.player.coins}")
            print(f"XP: {self.player.experience}/{self.player.level*100}")
            print(f"HP: {self.player.health}/{self.player.max_health} | "
                  f"DMG: {self.player.damage} | DEF: {self.player.defense}")
            print("=" * 60)

            print("\n📍 ЛОКАЦИИ:")
            for loc in self.location_manager.get_all_locations():
                status = loc.display_status()
                if loc.is_locked:
                    print(f"  {status} - {loc.unlock_description()}")
                else:
                    print(f"  {status}")

            print("\n🎮 МЕНЮ:")
            print("1) Вход в локацию")
            print("2) 🏛️ Таверна (квесты/NPC)")
            print("3) 🛒 Магазин")
            print("4) 🎰 Казино")
            print("5) 🎒 Инвентарь")
            print("6) 📊 Статус")
            print("7) 💾 Сохранить игру")
            print("8) 🚪 Выйти")

            ch = input("\nВыбор: ").strip()

            if ch == "1":
                self.choose_location()
            elif ch == "2":
                self.visit_tavern()
            elif ch == "3":
                self.run_shop()
            elif ch == "4":
                self.run_casino()
            elif ch == "5":
                self.manage_inventory()
            elif ch == "6":
                self.show_status()
            elif ch == "7":
                self.save_game_prompt()
            elif ch == "8":
                self.quit_game()
            else:
                print("Неверный выбор.")

    def choose_location(self) -> None:
        """Выбор локации."""
        if not self.player.is_alive:
            print("Вы не можете идти - вы мертвы!")
            return

        print("\n📍 Выберите локацию:")
        locations = self.location_manager.get_all_locations()
        for i, loc in enumerate(locations, 1):
            status = "🔒" if loc.is_locked else "📍"
            print(f"{i}) {status} {loc.name}")
        print("0) Отмена")

        ch = input("\n> ").strip()
        try:
            idx = int(ch)
            if idx == 0:
                return
            if 1 <= idx <= len(locations):
                location = locations[idx - 1]
                if location.is_locked:
                    print(f"\n❌ Локация закрыта: "
                          f"{location.unlock_description()}")
                    pause(1)
                else:
                    self.enter_location(location.id)
        except ValueError:
            pass

    def enter_location(self, location_id: str) -> None:
        """Вход в локацию."""
        if not self.player.is_alive:
            print("Вы не можете идти - вы мертвы!")
            return

        self.day += 1
        location = self.location_manager.get_location(location_id)
        location.visited = True

        print_section(f"Вы входите в {location.name}")
        print(f"\n{location.description}\n")
        pause(1)

        # Событие
        evt = EventSystem.roll_event(location_id, self.player)
        if evt:
            print(f"⚡ {evt}\n")
            self.history.append(evt)
            pause(1)

        # Враги
        count = random.randint(1, 3)
        enemies = EnemyGenerator.generate_for_location(
            location_id, self.player.level, count
        )

        if not enemies:
            print("❌ Нет врагов в этой локации.")
            return

        battlefield = Battlefield(self.player, enemies)

        victory = self.battle_loop(battlefield)

        # Обновления после боя
        self.shop.refresh()

        if victory:
            self.wins_in_row += 1
            result = battlefield.generate_battle_loot()
            self.show_loot_window(result)
            self.location_manager.increment_quest_counter(location_id)
            # Проверяем разблокировку новых локаций
            unlocked = self.location_manager.check_and_unlock_locations()
            if unlocked:
                print("\n🔓 НОВЫЕ ЛОКАЦИИ РАЗБЛОКИРОВАНЫ!")
                for loc_id in unlocked:
                    loc = self.location_manager.get_location(loc_id)
                    print(f"  ✅ {loc.name}")
                pause(2)
        else:
            self.wins_in_row = 0
            self.on_death()

    def battle_loop(self, battlefield: Battlefield) -> bool:
        """Боевая петля."""
        print_section(
            f"⚔️ БИТВА НАЧАЛАСЬ!"
        )
        print(f"Враги: {', '.join(e.name for e in battlefield.enemies)}\n")
        pause(0.5)

        while not battlefield.is_over():
            print(f"\n[Раунд {battlefield.round + 1}] "
                  f"HP: {self.player.health}/{self.player.max_health}")

            # Враги на поле
            enemies = battlefield.alive_enemies()
            print("\nВраги:")
            for i, e in enumerate(enemies, 1):
                print(f"  {i}) {e.name} | HP:{e.health}/{e.max_health}")

            # Ход игрока
            print("\nДействия:")
            print("1) Атаковать")
            print("2) Использовать зелье")
            print("3) Попытаться убежать (30%)")
            print("4) Сдаться")

            act = input("\n> ").strip()

            if act == "1":
                log, _ = battlefield.player_attack()
                print(f"→ {log}\n")
            elif act == "2":
                self.battle_use_potion(battlefield)
            elif act == "3":
                success, logs = battlefield.attempt_escape()
                for l in logs:
                    print(f"→ {l}")
                if success:
                    print("\n✅ Вы сбежали!")
                    return False
            elif act == "4":
                print("\n😢 Вы сдались...")
                return False
            else:
                print("Неверное действие.")
                continue

            # Ход врагов
            if not battlefield.is_over():
                logs = battlefield.enemy_turn()
                for l in logs:
                    print(f"→ {l}")

                if not self.player.is_alive:
                    print("\n💀 Вы были повержены!")
                    return False

            battlefield.round += 1
            pause(0.5)

        # Конец боя
        if self.player.is_alive:
            print("\n✅ ПОБЕДА!\n")
            return True

        return False

    def battle_use_potion(self, battlefield: Battlefield) -> None:
        """Использование зелья в бою."""
        potions = [
            (iid, qty) for iid, qty in battlefield.player.inventory.list_items()
            if battlefield.player.inventory.get(iid).is_consumable()
        ]

        if not potions:
            print("❌ У вас нет зелий.")
            return

        print("\nЗелья:")
        for i, (iid, qty) in enumerate(potions, 1):
            item = battlefield.player.inventory.get(iid)
            print(f"{i}) {item.name} x{qty}")

        try:
            idx = int(input("\n> ")) - 1
            if 0 <= idx < len(potions):
                iid, _ = potions[idx]
                item = battlefield.player.inventory.get(iid)
                msg = item.use(battlefield.player, battlefield)
                print(f"→ {msg}")
                battlefield.player.inventory.remove(iid, 1)
        except (ValueError, IndexError):
            print("Неверный выбор.")

    def show_loot_window(self, result: BattleResult) -> None:
        """Показать окно лута."""
        print_section("🎁 ЛУТ")
        print(f"💰 Получено: {result.gold_earned} золота")
        print(f"⭐ Получено: {result.xp_earned} опыта\n")

        if result.loot:
            print("Предметы:")
            for i, loot in enumerate(result.loot, 1):
                print(f"  {i}) {loot.display()}")
                # Автоматически берём лут если есть место
                if self.player.inventory.has_space_for(loot.quantity):
                    item = ItemDatabase.get(loot.item_id)
                    if item:
                        self.player.inventory.add(item, loot.quantity)

        self.player.coins += result.gold_earned
        xp_msgs = self.player.add_experience(result.xp_earned)
        for msg in xp_msgs:
            print(f"  📈 {msg}")

        pause(2)

    def visit_tavern(self) -> None:
        """Посещение таверны."""
        while True:
            print_section("🏛️ ТАВЕРНА")
            print("\nНЛ в таверне:")
            npcs_list = self.npc_manager.get_available_npcs()
            for i, npc in enumerate(npcs_list, 1):
                active = " [АКТИВНЫЙ КВЕСТ]" if npc.is_quest_active() else ""
                print(f"{i}) {npc.name}{active}")
            print("0) Выход")

            ch = input("\n> ").strip()
            try:
                idx = int(ch)
                if idx == 0:
                    break
                if 1 <= idx <= len(npcs_list):
                    npc = npcs_list[idx - 1]
                    self.talk_to_npc(npc)
            except ValueError:
                pass

    def talk_to_npc(self, npc) -> None:
        """Диалог с NPC."""
        print_section(f"💬 {npc.get_introduction()}")

        if npc.is_quest_active():
            quest = npc.current_quest
            print(f"\n📜 Активный квест: {quest.title}")
            print(f"Статус: {quest.progress_display()}")
            if quest.is_complete():
                print(f"\n✅ Квест выполнен!")
                print(f"Награда: {quest.reward_gold} золота, "
                      f"{quest.reward_xp} опыта")
                self.player.coins += quest.reward_gold
                xp_msgs = self.player.add_experience(quest.reward_xp)
                for msg in xp_msgs:
                    print(f"  📈 {msg}")
                npc.completed_quests_count += 1
                new_quest = npc.generate_quest()
                self.talk_to_npc_offer(npc, new_quest)
            else:
                print("\nПродолжайте выполнять квест...")
        else:
            # Генерируем новый квест
            new_quest = npc.generate_quest()
            self.talk_to_npc_offer(npc, new_quest)

        pause(2)

    def talk_to_npc_offer(self, npc, quest: GeneratedQuest) -> None:
        """Предложение нового квеста."""
        print(f"\n📋 {quest.description}\n")
        print(f"Цель: {quest.progress_display()}")
        print(f"Награда: {quest.reward_gold} монет, "
              f"{quest.reward_xp} опыта\n")

        print("Принять квест?")
        print("1) Да")
        print("2) Нет")

        ch = input("\n> ").strip()
        if ch == "1":
            if npc.accept_quest():
                print("\n✅ Вы приняли квест!")
        else:
            npc.reject_quest()
            print("\n❌ Вы отказались.")

    def manage_inventory(self) -> None:
        """Управление инвентарём."""
        print_section("🎒 ИНВЕНТАРЬ")
        print(self.player.inventory)
        pause(2)

    def show_status(self) -> None:
        """Показать статус персонажа."""
        print_section("📊 СТАТУС ПЕРСОНАЖА")
        print(f"Имя: {self.player.name}")
        print(f"Класс: {self.player.cls}")
        print(f"Уровень: {self.player.level}")
        print(f"Опыт: {self.player.experience}/{self.player.level * 100}")
        print(f"HP: {self.player.health}/{self.player.max_health}")
        print(f"Урон: {self.player.damage}")
        print(f"Защита: {self.player.defense}")
        print(f"Золото: {self.player.coins}")
        print(f"\nОружие: {self.player.weapon.name if self.player.weapon else 'Нет'}")
        print(f"Броня: {self.player.armor.name if self.player.armor else 'Нет'}")
        pause(2)

    def run_shop(self) -> None:
        """Магазин."""
        print_section("🛒 МАГАЗИН")
        print(self.shop.list_for_sale())
        print("\n1) Купить")
        print("2) Продать")
        print("0) Выход")

        ch = input("\n> ").strip()
        if ch == "1":
            item_id = input("ID предмета: ").strip()
            qty = int(input("Количество: ") or "1")
            msg = self.shop.buy(self.player, item_id, qty)
            print(f"\n{msg}")
        elif ch == "2":
            item_id = input("ID предмета: ").strip()
            qty = int(input("Количество: ") or "1")
            msg = self.shop.sell(self.player, item_id, qty)
            print(f"\n{msg}")

        pause(1)

    def run_casino(self) -> None:
        """Казино."""
        print_section("🎰 КАЗИНО")
        print("1) Орёл-решка")
        print("2) Слоты")
        print("0) Выход")

        ch = input("\n> ").strip()
        if ch in ("1", "2"):
            bet = int(input("Ставка (монет): ") or "0")
            if bet <= 0 or bet > self.player.coins:
                print("❌ Неверная ставка.")
                return

            if ch == "1":
                result, winnings, msg = Casino.coinflip(bet, input("Орёл (h) или решка (t)? "))
                if result:
                    self.player.coins += winnings
                    print(f"✅ {msg}")
                else:
                    self.player.coins -= bet
                    print(f"❌ {msg}")
            elif ch == "2":
                result, winnings, msg = Casino.slots(bet)
                if result:
                    self.player.coins += winnings
                    print(f"✅ {msg}")
                else:
                    self.player.coins -= bet
                    print(f"❌ {msg}")

        pause(1)

    def save_game_prompt(self) -> None:
        """Сохранение игры."""
        filename = input("Введите имя сохранения: ").strip()
        if filename:
            save_game(self.player, filename)
            print(f"✅ Игра сохранена как '{filename}'")
            pause(1)

    def on_death(self) -> None:
        """При смерти персонажа."""
        print_section("💀 ВЫ МЕРТВЫ")
        print("\nЧто дальше?")
        print("1) Загрузить игру")
        print("2) Начать заново")
        print("3) Выход")

        ch = input("\n> ").strip()
        if ch == "1":
            self.load_game_menu()
        elif ch == "2":
            self.create_character()
        elif ch == "3":
            self.quit_game()

    def load_game_menu(self) -> None:
        """Меню загрузки."""
        saves = get_save_list()
        if not saves:
            print("❌ Сохранений не найдено.")
            return

        print("Сохранения:")
        for i, save_file in enumerate(saves, 1):
            print(f"{i}) {save_file}")

        try:
            idx = int(input("\n> ")) - 1
            if 0 <= idx < len(saves):
                self.player = load_game(saves[idx])
        except (ValueError, IndexError):
            print("Неверный выбор.")

    def quit_game(self) -> None:
        """Выход из игры."""
        print("\n👋 До свидания!")
        self.running = False
        sys.exit(0)


def main() -> None:
    """Главная функция."""
    # Инициализация базы данных
    ItemDatabase.initialize()
    EnemyDatabase.initialize()

    game = Game()
    game.create_character()
    game.main_menu()


if __name__ == "__main__":
    main()


    def main_menu(self) -> None:
        """Главное меню."""
        while self.running:
            print("\n" + "=" * 50)
            print(f"День {self.day} | "
                  f"Уровень {self.player.level} | "
                  f"💰 {self.player.coins} | "
                  f"XP: {self.player.experience}/{self.player.level*100}")
            print(f"HP: {self.player.health}/{self.player.max_health} | "
                  f"DMG: {self.player.damage} | DEF: {self.player.defense}")
            print("=" * 50)
            print("\nДоступные локации:")
            print("1) 🌲 Лес")
            print("2) ⛏️ Пещера")
            print("3) 🏛️ Руины")
            print("\nМеню:")
            print("4) 🏰 Таверна (квесты/спутники)")
            print("5) 🛒 Магазин")
            print("6) 🎰 Казино")
            print("7) 🎒 Инвентарь")
            print("8) 📊 Статус")
            print("9) 💾 Сохранить игру")
            print("10) Выйти")

            ch = input("\nВыбор: ").strip()

            if ch == "1":
                self.enter_location("forest")
            elif ch == "2":
                self.enter_location("cave")
            elif ch == "3":
                self.enter_location("ruins")
            elif ch == "4":
                self.visit_tavern()
            elif ch == "5":
                self.run_shop()
            elif ch == "6":
                self.run_casino()
            elif ch == "7":
                self.manage_inventory()
            elif ch == "8":
                self.show_status()
            elif ch == "9":
                self.save_game_prompt()
            elif ch == "10":
                self.quit_game()
            else:
                print("Неверный выбор.")

    def enter_location(self, loc: str) -> None:
        """Вход в локацию."""
        if not self.player.is_alive:
            print("Вы не можете идти - вы мертвы!")
            return

        self.day += 1
        self.player.battles_fought += 1

        print_section(f"Вы идёте в {'ЛЕСНЫЕ ЧАЩИ' if loc == 'forest'
                                    else 'ТЁМНЫЕ ПЕЩЕРЫ'
                                    if loc == 'cave'
                                    else 'ДРЕВНИЕ РУИНЫ'}")

        # Событие
        evt = None
        if loc == "forest":
            evt = EventSystem.roll_forest(self.player)
        elif loc == "cave":
            evt = EventSystem.roll_cave(self.player)

        if evt:
            print(f"\n⚡ {evt}")
            self.history.append(evt)
            pause(1)

        # Враги
        if loc == "forest":
            count = random.randint(1, 2)
        elif loc == "cave":
            count = random.randint(1, 3)
        else:  # ruins
            count = random.randint(2, 3)

        enemies = EnemyGenerator.generate(loc, self.player.level, count)
        battlefield = Battlefield(self.player, enemies)

        victory = self.battle_loop(battlefield)

        # Обновления после боя
        self.shop.refresh()

        if victory:
            self.wins_in_row += 1
            for q in self.tavern.available_quests.values():
                if not q.complete:
                    q.register_win()
        else:
            self.wins_in_row = 0
            self.on_death()

    def battle_loop(self, battlefield: Battlefield) -> bool:
        """Боевая петля."""
        print_section(
            f"Битва началась! Враги: "
            f"{', '.join(e.name for e in battlefield.enemies)}"
        )
        pause(0.5)

        while not battlefield.is_over():
            print(f"\n[Раунд {battlefield.round + 1}] "
                  f"HP: {self.player.health}/"
                  f"{self.player.max_health}")

            # Спутники атакуют
            if self.player.companions:
                for c in self.player.companions:
                    if (c.is_alive and
                            battlefield.alive_enemies()):
                        target = random.choice(
                            battlefield.alive_enemies()
                        )
                        dmg = c.damage
                        dealt = target.take_damage(dmg)
                        print(f"→ {c.name} наносит {dealt} урона "
                              f"по {target.name}.")
                        if not target.is_alive:
                            print(f"  💥 {target.name} повержен!")
                            self.player.coins += target.base_coins

            # Враги на поле
            enemies = battlefield.alive_enemies()
            print("\nВраги на поле:")
            for i, e in enumerate(enemies, 1):
                print(f"  {i}) {e.name} | HP:{e.health}/{e.max_health} "
                      f"DMG:{e.damage}")

            # Ход игрока
            print("\nДействия:")
            print("1) Атаковать")
            print("2) Использовать зелье")
            print("3) Убежать (30%)")
            print("4) Сдаться")

            act = input("\n> ").strip()

            if act == "1":
                self.battle_attack(battlefield)
            elif act == "2":
                self.battle_use_item(battlefield)
            elif act == "3":
                success, logs = battlefield.attempt_escape()
                for l in logs:
                    print(f"→ {l}")
                if success:
                    print("\nВы успешно сбежали!")
                    return False
            elif act == "4":
                print("\nВы сдались...")
                return False
            else:
                print("Неверное действие.")
                continue

            # Ход врагов
            if not battlefield.is_over():
                logs = battlefield.enemy_turn()
                for l in logs:
                    print(f"→ {l}")

                if not self.player.is_alive:
                    print("\n💀 Вы были повержены!")
                    return False

            battlefield.round += 1
            pause(0.5)

        # Конец боя
        if self.player.is_alive:
            print_section("🎉 Вы победили!")

            # Регистрация убийств
            for e in battlefield.enemies:
                if not e.is_alive:
                    for q in self.tavern.available_quests.values():
                        q.register_kill(e.name)
            return True
        else:
            print_section("💀 Вы были повержены...")
            return False

    def battle_attack(self, battlefield: Battlefield) -> None:
        """Атака в бою."""
        enemies = battlefield.alive_enemies()
        print("\nВыберите цель:")
        for i, e in enumerate(enemies, 1):
            print(f"  {i}) {e.name} (HP:{e.health})")

        try:
            t = int(input("> ").strip()) - 1
            print(f"\n{battlefield.player_attack(t)}")
        except (ValueError, IndexError):
            print("Неверный выбор.")

    def battle_use_item(self, battlefield: Battlefield) -> None:
        """Использование предмета в бою."""
        items = self.player.inventory.list_items()
        if not items:
            print("Инвентарь пуст!")
            return

        print("\nВыберите предмет:")
        for i, (it, qty) in enumerate(items, 1):
            print(f"  {i}) {it.name} x{qty}")

        try:
            sel = int(input("> ").strip()) - 1
            if 0 <= sel < len(items):
                item, _ = items[sel]
                print(f"\n{battlefield.use_item(item.id)}")
            else:
                print("Неверный выбор.")
        except ValueError:
            print("Ошибка ввода.")

    def on_death(self) -> None:
        """Обработка смерти игрока."""
        print_header("ИГРА ОКОНЧЕНА - ВЫ БЫЛИ ПОВЕРЖЕНЫ!")

        # Статистика сессии
        stats = self.player.get_session_stats()
        print("\n📊 СТАТИСТИКА СЕССИИ:")
        print(f"  Персонаж: {stats['name']} ({stats['class']})")
        print(f"  Финальный уровень: {stats['level']}")
        print(f"  Финальные монеты: {stats['coins']} 💰")
        print(f"  Выданный урон: {stats['total_damage_dealt']}")
        print(f"  Полученный урон: {stats['total_damage_taken']}")
        print(f"  Врагов повержено: {stats['enemies_defeated']}")
        print(f"  Битв проведено: {stats['battles_fought']}")
        print(f"  Предметов в инвентаре: {stats['inventory_items']}")

        print("\n\nЧто дальше?")
        print("1) Начать заново")
        print("2) Выйти из игры")

        ch = input("\n> ").strip()
        if ch == "1":
            self.running = False  # Сигнал на рестарт
        else:
            sys.exit(0)

    def visit_tavern(self) -> None:
        """Посещение таверны."""
        print_header("🏰 ТАВЕРНА")

        while True:
            print("\n1) 📜 Квесты")
            print("2) 🤝 Нанять спутника")
            print("3) ← Выйти")

            ch = input("\n> ").strip()

            if ch == "1":
                self.manage_quests()
            elif ch == "2":
                self.hire_companion()
            elif ch == "3":
                break
            else:
                print("Неверный выбор.")

    def manage_quests(self) -> None:
        """Управление квестами."""
        print_section("Доступные квесты")
        print(self.tavern.list_quests())

        qid = input("\nВведите ID квеста (или 'назад'): ").strip()
        if qid.lower() == "назад":
            return

        q = self.tavern.get_quest(qid)
        if not q:
            print("Нет такого квеста.")
            return

        print(f"\n{q.id}: {q.desc}")
        print(f"Прогресс: {q.progress_display()}")

        if q.complete and not q.claimed:
            print("\n✅ Квест завершён! Получить награду? (y/n)")
            if input("> ").lower() == "y":
                print(q.claim(self.player))
        else:
            print("(Квест продолжается или уже выполнен)")

    def hire_companion(self) -> None:
        """Найм спутника."""
        print_section("Найм спутников")
        print(self.tavern.list_companions())

        try:
            sel = int(input("\nВыбор: ").strip())
            companions = self.tavern.COMPANIONS
            if 1 <= sel <= len(companions):
                name, role = companions[sel - 1]
                price = 50

                if self.player.coins < price:
                    print(f"Недостаточно монет (нужно {price}).")
                    return

                self.player.coins -= price
                from creatures import Companion
                comp = Companion(
                    name, role,
                    level=max(1, self.player.level - 1)
                )
                self.player.companions.append(comp)
                print(f"\n✅ {name} присоединился к вашей партии!")
            else:
                print("Неверный выбор.")
        except ValueError:
            print("Ошибка ввода.")

    def run_shop(self) -> None:
        """Магазин."""
        print_header("🛒 МАГАЗИН")

        while True:
            print("\n" + self.shop.list_for_sale())
            print("\n1) 📦 Купить")
            print("2) 💵 Продать")
            print("3) ← Выйти")

            ch = input("\n> ").strip()

            if ch == "1":
                iid = input("ID товара: ").strip()
                try:
                    qty = int(input("Количество (по умолчанию 1): "
                                    ).strip() or "1")
                except ValueError:
                    qty = 1
                print(self.player.buy(self.shop, iid, qty))
            elif ch == "2":
                print("\nВаш инвентарь:")
                for it, qty in self.player.inventory.list_items():
                    print(f"  {it.display_name()} x{qty}")
                iid = input("\nID предмета: ").strip()
                try:
                    qty = int(input("Количество (по умолчанию 1): "
                                    ).strip() or "1")
                except ValueError:
                    qty = 1
                print(self.player.sell(self.shop, iid, qty))
            elif ch == "3":
                break
            else:
                print("Неверный выбор.")

    def run_casino(self) -> None:
        """Казино."""
        print_header("🎰 КАЗИНО")

        while True:
            print(f"\nВаши монеты: {self.player.coins} 💰")
            print("\n1) 🪙 Орёл/Решка (1:1)")
            print("2) 🎲 Слоты")
            print("3) 🎡 Колесо Фортуны")
            print("4) ← Выйти")

            ch = input("\n> ").strip()

            if ch == "1":
                try:
                    bet = int(input("Ставка: ").strip() or "0")
                    choice = input("Выбор (h/t): ").strip().lower()
                    ok, payout, msg = Casino.coinflip(bet, choice)
                    self.player.coins += payout
                    print(f"\n{msg}")
                except ValueError:
                    print("Ошибка ввода.")
            elif ch == "2":
                try:
                    bet = int(input("Ставка: ").strip() or "0")
                    res, payout = Casino.slots(bet)
                    self.player.coins += payout
                    print(f"\n{res}")
                except ValueError:
                    print("Ошибка ввода.")
            elif ch == "3":
                try:
                    bet = int(input("Ставка: ").strip() or "0")
                    lab, payout = Casino.wheel(bet)
                    self.player.coins += payout
                    print(f"\n{lab}")
                except ValueError:
                    print("Ошибка ввода.")
            elif ch == "4":
                break
            else:
                print("Неверный выбор.")

    def manage_inventory(self) -> None:
        """Управление инвентарём."""
        print_header("🎒 ИНВЕНТАРЬ")

        while True:
            print("\nПредметы:")
            print(self.player.inventory)

            print("\nЭкипировка:")
            print(f"  Оружие: {self.player.weapon.name
                             if self.player.weapon else 'Нет'}")
            print(f"  Броня: {self.player.armor.name
                            if self.player.armor else 'Нет'}")

            print("\n1) 📍 Экипировать")
            print("2) ❌ Снять")
            print("3) ← Выйти")

            ch = input("\n> ").strip()

            if ch == "1":
                iid = input("ID предмета: ").strip()
                item = self.player.inventory.get(iid)
                if not item:
                    print("Нет такого предмета.")
                    continue

                if isinstance(item, Weapon):
                    self.player.equip_weapon(item)
                    print(f"✅ Экипировано {item.display_name()}")
                elif isinstance(item, Armor):
                    self.player.equip_armor(item)
                    print(f"✅ Экипировано {item.display_name()}")
                else:
                    print("Этот предмет нельзя экипировать.")

            elif ch == "2":
                print("1) Оружие  2) Броня")
                sub = input("> ").strip()
                if sub == "1":
                    self.player.unequip_weapon()
                    print("✅ Оружие снято.")
                elif sub == "2":
                    self.player.unequip_armor()
                    print("✅ Броня снята.")

            elif ch == "3":
                break
            else:
                print("Неверный выбор.")

    def show_status(self) -> None:
        """Статус персонажа."""
        print_header("📊 СТАТУС")

        print(f"\n👤 Имя: {self.player.name}")
        print(f"🎓 Класс: {self.player.CLASS_STATS[self.player.cls]['name']}")
        print(f"📈 Уровень: {self.player.level}")
        print(f"💚 HP: {self.player.health}/{self.player.max_health}")
        print(f"⚔️ Урон: {self.player.damage}")
        print(f"🛡️ Защита: {self.player.defense}")
        print(f"💰 Монеты: {self.player.coins}")
        print(f"✨ Опыт: {self.player.experience}/{self.player.level*100}")

        print("\n🤝 Спутники:")
        if not self.player.companions:
            print("  (Нет)")
        else:
            for c in self.player.companions:
                print(f"  - {c.name} ({c.role}) | "
                      f"HP:{c.health}/{c.max_health} | "
                      f"DMG:{c.damage}")

        print("\n📜 История:")
        if not self.history:
            print("  (Нет событий)")
        else:
            for h in self.history[-5:]:
                print(f"  • {h}")

        input("\nНажмите Enter для продолжения...")

    def save_game_prompt(self) -> None:
        """Сохранение игры."""
        print_header("💾 СОХРАНЕНИЕ")

        name = input("Имя сохранения (или Enter): ").strip()
        if not name:
            name = f"save_{self.day}"

        if save_game(self.player, name):
            print(f"✅ Игра сохранена как '{name}'")
        else:
            print("❌ Ошибка сохранения")
        pause(1)

    def quit_game(self) -> None:
        """Выход из игры."""
        print("\nВы уверены? (y/n)")
        if input("> ").lower() == "y":
            print("До свидания! 👋")
            sys.exit(0)


def main() -> None:
    """Главная функция."""
    print_header("⚔️ MINI RPG ⚔️")
    print("\n1) 🆕 Новая игра")
    print("2) 💾 Загрузить игру")
    print("3) ← Выход")

    ch = input("\n> ").strip()

    if ch == "1":
        ItemDatabase.initialize()
        game = Game()
        game.create_character()

        while game.running:
            try:
                game.main_menu()
            except KeyboardInterrupt:
                print("\n\nПрограмма прервана.")
                sys.exit(0)

        # После смерти - рестарт
        main()

    elif ch == "2":
        saves = get_save_list()
        if not saves:
            print("Нет сохранений.")
            return

        print("\nДоступные сохранения:")
        for i, save in enumerate(saves, 1):
            print(f"  {i}) {save}")

        try:
            sel = int(input("\nВыбор: ").strip())
            if 1 <= sel <= len(saves):
                ItemDatabase.initialize()
                player = load_game(saves[sel - 1])
                if player:
                    game = Game()
                    game.player = player
                    game.day = player.level * 5  # Примерный день

                    while game.running:
                        try:
                            game.main_menu()
                        except KeyboardInterrupt:
                            print("\n\nПрограмма прервана.")
                            sys.exit(0)

                    main()
                else:
                    print("Ошибка загрузки.")
        except ValueError:
            print("Ошибка ввода.")

    elif ch == "3":
        print("До свидания! 👋")
        sys.exit(0)


if __name__ == "__main__":
    main()
