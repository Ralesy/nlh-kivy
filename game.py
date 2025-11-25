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
from items import ItemDatabase
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
        
        # Инициализация врагов
        from enemies import EnemyDatabase
        EnemyDatabase.initialize()

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

        print(f"\nПерсонаж создан: {self.player.name} "
              f"({self.player.cls})")
        print(f"HP: {self.player.health} | DMG: {self.player.damage} "
              f"| DEF: {self.player.defense}")
        pause(1)

    def main_menu(self) -> None:
        """Главное меню."""
        while self.running:
            print("\n" + "=" * 60)
            print(f"День {self.day} | Уровень {self.player.level} | "
                  f"💰 {self.player.coins}")
            print(f"XP: {self.player.experience}/"
                  f"{self.player.level*100}")
            print(f"HP: {self.player.health}/{self.player.max_health} | "
                  f"DMG: {self.player.damage} | DEF: {self.player.defense}")
            print("=" * 60)

            print("\n📍 ЛОКАЦИИ:")
            for loc in self.location_manager.get_all_locations():
                status = loc.display_status()
                if loc.is_locked:
                    unlock = loc.unlock_description()
                    print(f"  {status} - {unlock}")
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
                    desc = location.unlock_description()
                    print(f"\n❌ Локация закрыта: {desc}")
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
        # Обновляем ассортимент магазина в зависимости от
        # уже разблокированных локаций.
        self.shop.refresh(self.location_manager)

        if victory:
            self.wins_in_row += 1
            result = battlefield.generate_battle_loot()
            self.show_loot_window(result)
            self.location_manager.increment_quest_counter(location_id)
            # Проверяем разблокировку новых локаций
            unlocked = (
                self.location_manager.check_and_unlock_locations()
            )
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
        print_section("БИТВА НАЧАЛАСЬ!")
        print(f"Враги: {', '.join(e.name for e in battlefield.enemies)}\n")
        pause(0.5)

        while not battlefield.is_over():
            print(f"\n[Раунд {battlefield.round + 1}] "
                  f"HP: {self.player.health}/"
                  f"{self.player.max_health}")

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
                for log in logs:
                    print(f"→ {log}")
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
                for log in logs:
                    print(f"→ {log}")

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
        inv_items = battlefield.player.inventory.list_items()
        potions = [
            (iid, qty) for iid, qty in inv_items
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
        print_section("ЛУТ")
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
            print_section("ТАВЕРНА")
            print("\nNPC в таверне:")
            npcs_list = self.npc_manager.get_available_npcs()
            for i, npc in enumerate(npcs_list, 1):
                active = (" [АКТИВНЫЙ КВЕСТ]"
                          if npc.is_quest_active() else "")
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
        intro = npc.get_introduction()
        print_section(intro)

        if npc.is_quest_active():
            quest = npc.current_quest
            print(f"\n📜 Активный квест: {quest.title}")
            print(f"Статус: {quest.progress_display()}")
            if quest.is_complete():
                print("Квест выполнен!")
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
        print_section("ИНВЕНТАРЬ")
        print(self.player.inventory)
        pause(2)

    def show_status(self) -> None:
        """Показать статус персонажа."""
        print_section("СТАТУС ПЕРСОНАЖА")
        print(f"Имя: {self.player.name}")
        print(f"Класс: {self.player.cls}")
        print(f"Уровень: {self.player.level}")
        exp_req = self.player.level * 100
        print(f"Опыт: {self.player.experience}/{exp_req}")
        print(f"HP: {self.player.health}/{self.player.max_health}")
        print(f"Урон: {self.player.damage}")
        print(f"Защита: {self.player.defense}")
        print(f"Золото: {self.player.coins}")

        weapon_name = (self.player.weapon.name
                       if self.player.weapon else "Нет")
        armor_name = (self.player.armor.name
                      if self.player.armor else "Нет")
        print(f"\nОружие: {weapon_name}")
        print(f"Броня: {armor_name}")
        pause(2)

    def run_shop(self) -> None:
        """Магазин."""
        print_section("МАГАЗИН")
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
        print_section("КАЗИНО")
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
                choice_str = input("Орёл (h) или решка (t)? ")
                result, winnings, msg = Casino.coinflip(bet, choice_str)
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
        print_section("ВЫ МЕРТВЫ")
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
