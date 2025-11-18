#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Game: главный модуль игры с интерфейсом и менеджментом.
"""

import random
import sys
from typing import Optional
from creatures import Player
from items import ItemDatabase, Inventory, Weapon, Armor
from battle import Battlefield, EnemyGenerator, EventSystem
from quests import Tavern
from shop_casino import Shop, Casino
from save_system import save_game, load_game, get_save_list, delete_save
from utils import print_header, print_section, pause


class Game:
    """Главный класс игры."""

    def __init__(self):
        """Инициализация игры."""
        self.player: Optional[Player] = None
        self.tavern = Tavern()

        # Инициализация магазина
        base_stock = {
            "w_short": 6, "w_sword": 3, "w_staff": 2,
            "w_great_sword": 1, "a_leather": 6,
            "a_chain": 3, "a_plate": 1, "a_epic": 1,
            "p_small": 12, "p_med": 6, "p_large": 2, "p_mega": 1
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
        self.player.coins += 100
        self.player.inventory.add(
            ItemDatabase.get("w_short"), 1
        )
        self.player.inventory.add(
            ItemDatabase.get("a_chain"), 1
        )
        self.player.inventory.add(
            ItemDatabase.get("p_med"), 2
        )

        print(f"\nПерсонаж создан: {self.player.name} ({self.player.cls})")
        print(f"HP: {self.player.health} | DMG: {self.player.damage} "
              f"| DEF: {self.player.defense}")
        pause(1)

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
