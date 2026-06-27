# AI_PROJECT_CONTEXT.md — Технический паспорт проекта NLH Remake(Этот контекст вероятно устарел, но в общих чертах архитектура не изменилась)

> **Проект:** Nameless Hero: Fears of Emberfall — однопользовательская RPG
> **Язык:** Python 3.13+
> **GUI-фреймворк:** Kivy 2.3.1
> **Тестирование:** pytest
> **Лицензия:** MIT
> **Текущая версия:** 1.1 (Service Layer)
> **Строк кода:** ~7100


---

## 1. Архитектурный обзор

**NLH Remake** — это пошаговая RPG-игра с элементами стелс-механики, свободного перемещения по глобальной карте, локальными проходимыми сценами (лес, болота, шахты, горы, город) и системой прогрессии через убийство врагов, выполнение квестов и победу над боссами. Приложение построено на фреймворке **Kivy** с использованием `ScreenManager` для навигации между экранами. Графика — фоновая (изображения PNG/JPG) с наложением Canvas-примитивов для маркеров, токенов врагов, зон перехода и HUD-панели.

**Архитектура разделена на три слоя:**
- **Data Layer** (`data/`): статические базы данных предметов, врагов, локаций, оружия и сцен. Содержит классы `ItemDatabase`, `EnemyDatabase`, `LocationManager` и конфигурации `LocalSceneConfig`.
- **Core Layer** (`core/`): доменная логика — модели существ (`Creature`, `Player`, `Companion`), инвентарь (`Inventory`), боевая система (`Battlefield`, `BattleService`, `Damage`), сессия (`GameSession`), генерация врагов (`EnemyGenerator`) и система событий (`EventSystem`).
- **UI Layer** (`ui/`): Kivy-экраны (`screens/`), переиспользуемые виджеты (`widgets/`), стилизованные компоненты (`ui_styles.py`) и система привязки клавиатуры/наблюдателя (`bindings/`).

**Системные сервисы** (`systems/`) работают как прослойка между Core и UI: управление опасностью (`DangerManager`), квестами (`quests.py`, `npcs.py`), сохранением (`save_system.py`), магазином/казино (`shop_casino.py`), стелс-контроллером (`stealth_controller.py`) и роумингом врагов на глобальной карте (`roaming_entity_manager.py`).

**Паттерн взаимодействия:** Приложение запускается через `main.py` → `RPGApp` (Kivy App) собирает дерево экранов и HUD. Каждый экран получает ссылку на `GameSession` через `App.get_running_app().game`. Пользователь взаимодействует с UI-экранами, те вызывают методы `GameSession` или сервисов, а результат отображают обратно через обновление виджетов. `PlayerViewModel` (паттерн Observer) транслирует изменения игрока (HP, монеты, уровень) в HUD. Навигация: главное меню → создание персонажа → глобальная карта → локальные сцены/бой.

---

## 2. Дерево проекта

```
NLH_remake/
├── main.py                          # Точка входа: запускает RPGApp (Kivy)
│
├── core/                            # Доменная логика и модели
│   ├── __init__.py                  # Re-export моделей из core.models
│   ├── config.py                    # Константы: размеры, цвета, пороги локаций/боссов, ItemRarity и CharacterClass
│   ├── creatures.py                 # Re-export: Player, Creature, Companion, Inventory
│   ├── game.py                      # Re-export: Game = GameSession
│   ├── hybrid_controls.py           # Гибридное управление (клавиатура + мышь) — заготовка
│   ├── keybindings.py               # Сопоставление клавиш → действия
│   ├── session.py                   # GameSession: оркестратор сессии (игрок, бой, квесты, сохранение, штраф смерти)
│   ├── utils.py                     # Утилиты: clamp, rarity_weighted_choice, weighted_random, print_header
│   │
│   ├── models/                      # Модели данных
│   │   ├── __init__.py              # Пустой
│   │   ├── companion.py             # Companion: спутник (роль: танк/лучник/целитель), наследует Creature
│   │   ├── creature.py              # Creature: базовая боевая единица (HP, урон, защита, take_damage, heal)
│   │   ├── inventory.py             # Inventory: контейнер предметов (add/remove/qty/list, сериализация)
│   │   ├── player.py                # Player: персонаж с навыками, экипировкой, опытом, слушателями UI
│   │   ├── roam_zone.py             # RoamZone: зона на глобальной карте (тип, радиус, типы врагов)
│   │   └── roaming_token.py         # RoamingToken: токен врага на глобальной карте (патруль, преследование, конус зрения)
│   │
│   └── combat/                      # Боевая система
│       ├── __init__.py              # Пустой
│       ├── battle_service.py        # BattleService: фасад боя для UI (get_status, атака, побег, лут)
│       ├── battlefield.py           # Battlefield: состояние боя (раунды, атака игрока/врагов, способности, побег, лут)
│       ├── damage.py                # Формулы: roll_raw_damage, apply_critical, armor_ignore_bonus, resolve_hit
│       ├── enemy_spawner.py         # EnemyGenerator: создание врагов из шаблонов EnemyDatabase
│       ├── events.py                # EventSystem: случайные события в локациях (находка, яд, обвал)
│       └── loot.py                  # LootDrop и BattleResult: результаты боя (лут, золото, XP)
│
├── data/                            # Статические данные и конфигурации
│   ├── __init__.py                  # Пустой
│   ├── enemies.py                   # Enemy + EnemyDatabase: 40+ врагов и 4 босса с таблицами лута
│   ├── items.py                     # Item / Weapon / Armor / Potion + ItemDatabase: 40+ предметов всех типов
│   ├── local_scenes.py              # LocalSceneConfig / ZoneConfig / BossSceneConfig: конфигурация проходимых сцен
│   ├── locations.py                 # Location + LocationManager: 5 локаций с блокировками и боссами
│   └── weapon_abilities.py          # WeaponAbility и подклассы: способности оружия (двойной удар, игнор брони и т.д.)
│
├── systems/                         # Сервисный слой (бизнес-логика)
│   ├── __init__.py                  # Пустой
│   ├── active_quests.py             # Экран/логика активных квестов
│   ├── battle.py                    # BattleResult/LootDrop (дубли из loot.py для обратной совместимости)
│   ├── battle_logic_service.py      # Альтернативный сервис боя (заготовка)
│   ├── battle_service.py            # BattleService (реэкспорт из core.combat)
│   ├── danger_manager.py            # DangerManager: шкала глобальной опасности (0–100%), рост/спад, засады
│   ├── inventory_service.py         # InventoryService: операции с инвентарём
│   ├── location_service.py          # LocationService: запуск боя для локации (генерация врагов)
│   ├── npcs.py                      # NPC / CaptainGuard / SwampTracker / NPCManager: NPC с генерируемыми квестами
│   ├── quests.py                    # Quest + Tavern: квесты на убийство и победы (награда: монеты/опыт/предметы)
│   ├── roaming_entity_manager.py    # RoamingEntityManager: спавн, перемещение и столкновения токенов на глобальной карте
│   ├── save_system.py               # save_session / load_session_into / get_save_list: JSON-сохранение/загрузка
│   ├── shop_casino.py               # Shop (покупка/продажа) + Casino (coinflip, slots, wheel)
│   ├── stealth_controller.py        # StealthController: режимы (норм/стелс/бег), шум, обнаружение токенами
│   └── ui_services.py               # UI-сервисы общего назначения
│
├── ui/                              # Пользовательский интерфейс (Kivy)
│   ├── __init__.py                  # Пустой
│   ├── ui_app.py                    # RPGApp: сборка ScreenManager, HUD, ссылки на экраны
│   ├── ui_styles.py                 # COLORS, StyledButton, StyledPanel, CustomProgressBar, PopupTitle
│   ├── local_location_screen.py     # Re-export LocalLocationScreen из screens/
│   ├── loot_window.py               # Компонент окна добычи
│   ├── refactored_battle_screen_example.py  # Пример рефакторинга экрана боя
│   │
│   ├── bindings/                    # Связь UI с Core
│   │   ├── __init__.py              # Пустой
│   │   ├── keyboard_handler.py      # KeyboardHandler: привязка клавиш к экранам
│   │   └── player_observer.py       # PlayerViewModel: Observable для HUD (HP, монеты, уровень)
│   │
│   ├── screens/                     # Kivy-экраны (18 экранов)
│   │   ├── __init__.py              # Импорт всех экранов для RPGApp
│   │   ├── active_quests.py         # Активные квесты с прогрессом и сдачей
│   │   ├── ancient_cave_boss.py     # Выбор босса в древней пещере
│   │   ├── battle.py                # BattleScreen: полный экран боя (атака, способности, побег, лут)
│   │   ├── character_creation.py    # Создание персонажа (имя, фон: дворянин/оруженосец/охотник)
│   │   ├── city_menu.py             # Меню города (таверна, магазин, казино)
│   │   ├── companion_management.py  # Управление спутниками (найм, просмотр)
│   │   ├── controls.py              # Справка по управлению
│   │   ├── game_screen.py           # Заглушка основного экрана игры
│   │   ├── inventory.py             # Инвентарь (использование, экипировка, продажа)
│   │   ├── load_game.py             # Загрузка сохранений
│   │   ├── local_location_base.py   # LocalLocationScreen: проходимая карта с камерой, врагами, NPC, зонами
│   │   ├── location_select.py       # LocationSelectScreen: глобальная карта с камерой, токенами, стелсом
│   │   ├── loot_window_screen.py    # Окно добычи после боя
│   │   ├── main_menu.py             # Главное меню (продолжить, новая игра, загрузить, выход)
│   │   ├── npc_dialogue.py          # Диалоги с NPC (принять/отказаться от квеста, сдать)
│   │   ├── shop.py                  # Магазин (покупка/продажа)
│   │   ├── status.py                # Статус персонажа (характеристики, навыки, статистика)
│   │   └── tavern.py                # Таверна (спутники, квесты)
│   │
│   └── widgets/                     # Переиспользуемые виджеты
│       ├── __init__.py              # Пустой
│       ├── cover_background.py      # cover_background_image: подгонка картинки под размер экрана
│       ├── danger_bar.py            # DangerBar: визуализация шкалы опасности
│       ├── encounter_dialog.py      # EncounterDialog: всплывающее окно встречи с токеном (бой/обход)
│       ├── game_hud.py              # GameHUD: HUD-панель (HP, DMG, DEF, уровень, XP, монеты)
│       ├── level_up_popup.py        # LevelUpPopup: анимация повышения уровня
│       ├── map_widget.py            # MapWidget: компонент карты
│       └── navigation_buttons.py    # Кнопки навигации (инвентарь, статус, меню)
│
├── assets/                          # Ресурсы
│   ├── backgrounds/                 # Фоновые изображения локаций, глобальной карты, квестов
│   └── ui/buttons/                  # Иконки кнопок (inventory, battle, menu и т.д.)
│
├── docs/                            # Документация
│   ├── ARCHITECTURE.md, GAME_MECHANICS.md, ADDING_CONTENT.md, OOP_PRINCIPLES.md и др.
│   └── requirements.txt             # Зависимости (kivy, pytest)
│
├── scripts/                         # Вспомогательные скрипты
│   ├── autosave_test.py             # Тест автосохранения
│   └── check_axe_ignore.py          # Проверка механики топора
│
└── tests/                           # Тесты (pytest, ~25 тестов)
    ├── test_full_playthrough.py     # Полное прохождение
    ├── test_battle_combat.py        # Боевая система
    ├── test_save_load_system.py     # Сохранение/загрузка
    ├── test_roaming.py              # Роуминг врагов
    ├── test_danger_manager.py       # Система опасности
    └── ...                          # + другие тесты
```

---

## 3. Стабильные модули (Кратко)

Данный раздел описывает классы и модули, логика которых завершена и маловероятно потребует изменений. Полный код не приводится — только сигнатуры и краткое описание.

### 3.1. `core/config.py`
Конфигурационные константы и перечисления. Стабильна, изменения только при добавлении новых локаций/боссов.
- **Классы:** `ItemRarity` (COMMON/RARE/LEGENDARY/UNIQUE), `ItemType` (WEAPON/ARMOR/POTION/MISC), `LocationDifficulty` (EASY–LEGENDARY), `CharacterClass` (WARRIOR/ROGUE/MAGE/PALADIN).
- **Константы:** `WINDOW_WIDTH=1280`, `WINDOW_HEIGHT=720`, цвета RGBA, размеры шрифтов, `STAT_SCALE_FACTOR=0.12`, `BASE_EXPERIENCE_PER_LEVEL=100`, `DODGE_CHANCE_BASE=0.05`, `LOCATION_UNLOCK_CONDITIONS`, `BOSS_UNLOCK_CONDITIONS`.
- **Вход:** импорт констант из любых модулей проекта.
- **Выход:** значения констант, объекты Enum.

### 3.2. `core/utils.py`
Вспомогательные функции общего назначения. Стабильна.
- `clamp(v, a, b) → float` — зажимает значение в диапазон.
- `pause(seconds=0.4)` — пауза (time.sleep).
- `rnd_choice_weighted(items_with_weight) → Any` — взвешенный случайный выбор.
- `rarity_weighted_choice() → str` — выбор редкости (Common > Legendary).
- `clear_screen()`, `print_header(text)`, `print_section(text)` — консольные утилиты.
- **Вход:** разнородные параметры.
- **Выход:** значение/побочный эффект (печать, пауза).

### 3.3. `core/models/creature.py`
Базовый класс всех существ. Стабилен.
- **Класс `Creature`:** конструктор `__init__(name, base_health, base_damage, base_coins, level=1)`, свойства `damage`, `defense`, `is_alive`, `health`, `coins`, `base_xp`.
- **Методы:** `_scale_stat(base) → int`, `take_damage(dmg) → int`, `heal(amount) → int`, `die(cause)`, `equip_weapon/armor`, `unequip_weapon/armor`, `description() → str`, `to_dict() → dict`, `from_dict(data) → Creature`.
- **Вход:** числовые характеристики, объекты Weapon/Armor.
- **Выход:** изменённое состояние, строка описания, словарь для сохранения.

### 3.4. `core/models/inventory.py`
Система инвентаря. Стабильна.
- **Класс `Inventory`:** конструктор `__init__(capacity=20)`. Свойства `used_slots`, `free_slots`.
- **Методы:** `add(item, qty=1) → bool`, `remove(item_id, qty=1) → bool`, `get(item_id) → Optional[Item]`, `qty(item_id) → int`, `list_items() → List[Tuple[Item, int]]`, `has_space_for(qty) → bool`, `to_dict() → dict`, `from_dict(data) → Inventory`.
- **Вход:** объекты Item, ID предметов.
- **Выход:** bool успеха, количество, список пар (Item, qty).

### 3.5. `core/models/companion.py`
Спутник игрока. Стабилен.
- **Класс `Companion(Creature)`:** роли `tank` (50 HP/3 DMG), `archer` (37/4), `healer` (33/2).
- **Методы:** `to_dict() → dict`, `from_dict(data) → Companion`.
- **Вход:** имя, роль, уровень.
- **Выход:** сериализованный/десериализованный объект.

### 3.6. `data/items.py`
База данных предметов (оружие, броня, зелья). Стабильна, пополняется добавлением новых предметов.
- **Классы:** `Item` (базовый), `Weapon(Item)` (материал, base_damage, condition, ability), `Armor(Item)` (материал, base_defense, condition), `Potion(Item)` (heal_amount), `ItemDatabase` (ITEMS: dict, register, get, initialize).
- **Материалы:** iron/steel/goblin/orc/elf/dwarf/dragon (оружие); rags/leather/iron/steel/orc/elf/dwarf (броня).
- **Состояния:** sharp/blunt/rusted/masterwork (оружие); torn/reinforced/enhanced/legendary (броня).
- **Вход:** ID предмета (строка).
- **Выход:** объект Item или None.

### 3.7. `data/enemies.py`
База данных врагов. Стабильна, пополняется новыми врагами.
- **Классы:** `Enemy` (id, name, enemy_type, base_health/damage/coins, xp_reward, loot_table, is_boss), `EnemyDatabase` (ENEMIES: dict, register, get, get_by_location, initialize).
- **Враги:** лес (волк, мародёр, бандит, разведчик), болота (гоблин, жаба, болотник, шаман), шахты (орк, драугр, голем, скелет, гремлин), горы (снеговик, волк, приведение, дракон, тролль, великан), боссы (4 шт).
- **Вход:** ID врага/локации.
- **Выход:** объект Enemy или список Enemy.

### 3.8. `data/locations.py`
Система локаций с блокировками. Стабильна.
- **Классы:** `LocationStatus` (LOCKED/AVAILABLE/DISCOVERED), `Location` (id, name, description, difficulty, is_locked, unlock_condition, enemy_types), `LocationManager`.
- **Логика:** `unlock_location`, `is_location_available`, `check_and_unlock_locations` (по цепочке боссов), `mark_boss_defeated`, `is_boss_unlocked`, `to_dict/from_dict`.
- **Вход:** ID локации/босса.
- **Выход:** bool, список разблокированных локаций, Location.

### 3.9. `systems/save_system.py`
JSON-сохранение/загрузка. Стабильна.
- **Функции:** `ensure_saves_dir()`, `get_save_path(filename) → Path`, `read_save_data(filename) → dict`, `save_session(session, filename) → bool`, `load_session_into(session, filename) → bool`, `save_game(player, filename) → bool`, `load_game(filename) → Player`, `get_save_list() → List[str]`, `delete_save(filename) → bool`.
- **Вход:** сессия/игрок + имя файла.
- **Выход:** bool успеха, словарь данных, список сохранений.

### 3.10. `systems/shop_casino.py`
Магазин и казино. Стабильны.
- **Класс `Shop`:** `__init__(stock)`, `list_for_sale()`, `buy(player, item_id, qty, price_modifier) → str`, `sell(player, item_id, qty) → str`, `refresh(location_manager)`.
- **Класс `Casino`:** `coinflip(bet, choice) → Tuple[bool, int, str]`, `slots(bet) → Tuple[str, int]`, `wheel(bet) → Tuple[str, int]`.
- **Вход:** Player, ID предмета, ставка.
- **Выход:** строка-сообщение, кортеж (результат, выплата).

### 3.11. `systems/quests.py`
Система квестов таверны. Стабильна.
- **Класс `Quest`:** конструктор (id, desc, goal, reward), методы `register_kill/enemy_name`, `register_win()`, `check_complete()`, `claim(player) → str`, `progress_display()`.
- **Класс `Tavern`:** `_initialize_quests()`, `list_quests()`, `get_quest(quest_id)`, `get_random_companion()`, `list_companions()`.
- **Вход:** Player, ID квеста, имя врага.
- **Выход:** строка, bool, обновлённый прогресс.

### 3.12. `data/weapon_abilities.py`
Способности оружия. Стабильна.
- **Классы:** `WeaponAbility` (name, ability_type), `ArmorIgnoreAbility` (armor_ignore=0.30), `CriticalBoostAbility` (crit_multiplier=2.0), `DamageScalingAbility` (damage_per_hit=2), `DoubleStrikeAbility`, `DoubleArrowAbility`, `StaffAoEAbility`.
- **Функция:** `get_weapon_ability(weapon_type, is_unique, unique_id) → Optional[WeaponAbility]`.
- **Вход:** тип оружия, флаг уникальности, ID.
- **Выход:** объект способности или None.

### 3.13. `core/combat/damage.py`
Формулы расчёта урона. Стабильны.
- **Функции:** `roll_raw_damage(base_damage, variance, minimum) → int`, `apply_critical(damage, crit_chance, multiplier) → Tuple[int, bool]`, `apply_forced_critical(damage, multiplier) → int`, `armor_ignore_bonus(target_defense, ignore_ratio) → int`, `resolve_hit(damage, target) → int`, `player_crit_chance(player) → float`.
- **Константы:** `DEFAULT_VARIANCE=(-3,5)`, `ENEMY_VARIANCE=(-2,3)`, `MIN_DAMAGE=1`, `DEFAULT_CRIT_MULTIPLIER=2.0`, `DEFAULT_ENEMY_CRIT_CHANCE=0.04`.
- **Вход:** числовые характеристики, объект Creature.
- **Выход:** число урона, bool (крит).

---

## 4. Ядро проекта (Полный код)

В данном разделе приведено полное содержимое ключевых файлов, которые будут активно развиваться и рефакториться.

### 4.1. `main.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mini RPG — точка входа приложения (Kivy UI).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.ui_app import RPGApp

if __name__ == "__main__":
    RPGApp().run()
```

### 4.2. `ui/ui_app.py`

```python
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
```

### 4.3. `core/session.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GameSession — единый оркестратор игровой сессии.

UI-слой обращается к сессии, а не к разрозненным системам напрямую.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from core.combat.battle_service import BattleService
from core.combat.battlefield import Battlefield
from core.combat.loot import BattleResult
from core.creatures import Player, TestPlayer
from data.enemies import EnemyDatabase
from data.items import ItemDatabase
from data.locations import LocationManager
from systems.npcs import GeneratedQuest, NPCManager
from systems.quests import Tavern
from systems.danger_manager import DangerManager
from systems.save_system import load_session_into, save_session
from systems.shop_casino import Shop


@dataclass
class DeathPenaltyResult:
    """Результат поражения игрока для отображения в UI."""

    gold_lost: int = 0
    items_lost: List[str] = field(default_factory=list)
    health_restored: int = 0
    message: str = ""


class GameSession:
    """
    Игровая сессия: игрок, мир, экономика, квесты и боевые операции.

    Kivy-экраны получают ссылку на сессию через ``app.game`` / ``app.session``.
    """

    DEFAULT_SHOP_STOCK = {
        "w_iron_sword": 5,
        "w_steel_sword": 2,
        "a_leather_armor": 5,
        "a_iron_plate": 2,
        "a_steel_plate": 1,
        "p_small": 15,
        "p_med": 8,
        "p_large": 3,
    }

    def __init__(self):
        """Инициализировать пустую сессию с базовыми подсистемами."""
        self.player: Optional[Player] = None
        self.tavern = Tavern()
        self.location_manager = LocationManager()
        self.npc_manager = NPCManager()

        ItemDatabase.initialize()
        EnemyDatabase.initialize()

        self.shop = Shop(self.DEFAULT_SHOP_STOCK.copy())
        self.danger_manager = DangerManager()
        self.day = 1
        self.history: List[str] = []
        self.wins_in_row = 0

    @property
    def has_player(self) -> bool:
        """True, если в сессии есть активный игрок."""
        return self.player is not None

    def start_new_game(self, name: str, background: str = "squire") -> Player:
        """
        Создать нового игрока и привязать к сессии.

        Args:
            name: имя персонажа.
            background: ключ фона (noble / squire / hunter).

        Returns:
            Созданный Player.
        """
        self.player = Player(name, background)
        self.day = 1
        self.history = []
        self.wins_in_row = 0
        self.danger_manager.reset()
        return self.player

    def start_test_game(self, name: str) -> Player:
        """Создать тестового игрока с усиленными характеристиками."""
        self.player = TestPlayer(name)
        self.day = 1
        self.history = []
        self.wins_in_row = 0
        self.danger_manager.reset()
        return self.player

    def load_from_file(self, filename: str) -> bool:
        """
        Загрузить сессию из файла сохранения.

        Returns:
            True при успешной загрузке.
        """
        return load_session_into(self, filename)

    def save_to_file(self, filename: str) -> bool:
        """
        Сохранить сессию в файл.

        Returns:
            True при успешном сохранении.
        """
        if not self.player:
            return False
        return save_session(self, filename)

    def autosave(self) -> bool:
        """Быстрое автосохранение в ``autosave``."""
        return self.save_to_file("autosave")

    def advance_day(self) -> None:
        """Перевести игровой день на следующий."""
        self.day += 1

    def register_battle_encounter(self) -> None:
        """Зафиксировать начало боя: день и счётчик боёв."""
        self.advance_day()
        if self.player:
            self.player.battles_fought += 1

    def create_battle(
        self,
        enemies: List,
        register_encounter: bool = True,
    ) -> Tuple[Battlefield, BattleService]:
        """
        Создать бой с врагами.

        Args:
            enemies: список Creature.
            register_encounter: учитывать день/статистику боя.

        Returns:
            (Battlefield, BattleService).
        """
        if not self.player:
            raise RuntimeError("Нельзя начать бой без игрока.")
        if register_encounter:
            self.register_battle_encounter()
        battlefield = Battlefield(self.player, enemies)
        return battlefield, BattleService(battlefield)

    def refresh_shop(self) -> None:
        """Обновить ассортимент магазина по разблокированным локациям."""
        self.shop.refresh(self.location_manager)

    def mark_boss_defeated(self, boss_id: int) -> None:
        """Отметить босса как поверженного и проверить разблокировки."""
        if self.player:
            self.player.defeated_bosses.add(boss_id)
        self.location_manager.mark_boss_defeated(boss_id)

    def check_location_unlocks(self) -> List[str]:
        """
        Проверить новые локации после победы.

        Returns:
            ID разблокированных локаций.
        """
        return self.location_manager.check_and_unlock_locations()

    def add_history(self, message: str) -> None:
        """Добавить запись в журнал сессии."""
        self.history.append(message)

    def apply_death_penalty(self) -> DeathPenaltyResult:
        """
        Применить штрафы за поражение (золото, предметы, частичное HP).

        Returns:
            Структура с деталями для UI.
        """
        if not self.player:
            return DeathPenaltyResult(message="Нет активного игрока.")

        player = self.player
        gold_lost = player.coins // 10
        if gold_lost > 0:
            player.spend_coins(gold_lost)

        items_lost: List[str] = []
        non_quest_items = [
            (item, qty)
            for item, qty in player.inventory.list_items()
            if not item.is_quest_item()
        ]

        if non_quest_items:
            num_lost = random.randint(1, min(2, len(non_quest_items)))
            for _ in range(num_lost):
                if not non_quest_items:
                    break
                item, _qty = random.choice(non_quest_items)
                if player.inventory.remove(item.id, 1):
                    items_lost.append(item.name)
                    non_quest_items = [
                        entry
                        for entry in non_quest_items
                        if entry[0].id != item.id
                    ]

        restored_hp = max(1, int(player.max_health * 0.3))
        player.health = restored_hp

        message = (
            "Вас оглушили и оставили без сознания.\n"
            "Вы очнулись, потеряв часть добычи...\n\n"
            f"💰 Потеряно: {gold_lost} золота.\n"
        )
        if items_lost:
            message += "\n".join(
                f"🎒 Потерян предмет: {name}" for name in items_lost
            )
            message += "\n"
        message += "\n❤️ Вы восстановили часть здоровья."

        return DeathPenaltyResult(
            gold_lost=gold_lost,
            items_lost=items_lost,
            health_restored=restored_hp,
            message=message,
        )

    def restore_npc_state(self, npc_data: dict) -> None:
        """Восстановить состояние NPC из сохранения."""
        if not npc_data:
            return
        for npc_id, state in npc_data.items():
            npc = self.npc_manager.get_npc(npc_id)
            if not npc:
                continue
            npc.completed_quests_count = state.get(
                "completed_quests_count",
                npc.completed_quests_count,
            )
            quest_data = state.get("current_quest")
            if quest_data:
                npc.current_quest = GeneratedQuest.from_dict(quest_data)
            else:
                npc.current_quest = None

    def complete_quest_and_reduce_danger(
        self, quest_id: str
    ) -> str:
        """Сдать квест и снизить глобальную опасность.

        Args:
            quest_id: ID завершённого квеста.

        Returns:
            Сообщение о снижении опасности.
        """
        reduction = self.danger_manager.on_quest_completed()
        if reduction > 0:
            return (
                f"🛡️ Опасность снижена на {reduction:.0f}% "
                f"(теперь {self.danger_manager.danger_level:.0f}%)"
            )
        return "🛡️ Опасность уже на минимуме."

    def to_save_dict(self) -> dict:
        """Сериализовать сессию для сохранения."""
        return {
            "version": "2.0",
            "day": self.day,
            "history": self.history,
            "wins_in_row": self.wins_in_row,
            "player": (
                self.player.to_dict() if self.player else None
            ),
            "npcs": self.npc_manager.to_dict(),
            "danger": self.danger_manager.to_dict(),
        }


# Обратная совместимость: старый код импортирует Game
Game = GameSession
```

### 4.4. `core/models/player.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Игровой персонаж: прогрессия, инвентарь, навыки и уведомления для UI.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.models.companion import Companion
from core.models.creature import Creature
from core.models.inventory import Inventory
from core.utils import clamp
from data.items import Armor, ItemDatabase, Weapon


class Player(Creature):
    """Игровой персонаж с инвентарём, навыками и системой событий."""

    BACKGROUNDS = {
        "noble": {
            "name": "Обедневший дворянин",
            "coins": 500,
            "weapon_id": "w_iron_dagger",
            "armor_id": "a_leather_armor",
            "starting_items": [("p_small", 3)],
        },
        "squire": {
            "name": "Оруженосец",
            "coins": 50,
            "weapon_id": "w_iron_sword",
            "armor_id": "a_leather_armor",
            "starting_items": [("p_small", 2)],
        },
        "hunter": {
            "name": "Охотник",
            "coins": 200,
            "weapon_id": "w_iron_bow",
            "armor_id": "a_leather_armor",
            "starting_items": [("p_small", 2)],
        },
    }

    BASE_STATS = {
        "health": 100,
        "damage": 10,
        "critical_chance": 0.05,
        "luck": 1.0,
        "selling_multiplier": 1.0,
    }

    STAT_COEFFICIENTS = {
        "endurance": {"health": 15},
        "strength": {"damage": 2, "inventory_capacity": 5},
        "agility": {"critical_chance": 0.05},
        "luck": {"luck": 0.15},
        "trade": {"selling_multiplier": 0.1},
        "speed": {"move_speed": 15},
    }

    BASE_MOVE_SPEED = 200

    STARTING_SKILL_POINTS = 5

    def __init__(self, name: str, background: str = "squire"):
        """Создать нового игрока с выбранным фоном."""
        if background not in self.BACKGROUNDS:
            background = "squire"

        bg = self.BACKGROUNDS[background]
        super().__init__(
            name,
            self.BASE_STATS["health"],
            self.BASE_STATS["damage"],
            bg["coins"],
            level=1,
        )

        self.background = background
        self.inventory = Inventory(capacity=20)

        self.skill_points_available = self.STARTING_SKILL_POINTS
        self.skill_points_allocated = {
            "endurance": 0,
            "strength": 0,
            "agility": 0,
            "luck": 0,
            "trade": 0,
            "speed": 0,
        }

        self._move_speed = self.BASE_MOVE_SPEED

        self._critical_chance = self.BASE_STATS["critical_chance"]
        self._luck = self.BASE_STATS["luck"]
        self._selling_multiplier = self.BASE_STATS["selling_multiplier"]
        self._listeners: List = []

        self.last_global_pos: Optional[Tuple[float, float]] = None

        ItemDatabase.initialize()
        if bg["weapon_id"]:
            starter_weapon = ItemDatabase.get(bg["weapon_id"])
            if starter_weapon:
                self.equip_weapon(starter_weapon)

        if bg["armor_id"]:
            starter_armor = ItemDatabase.get(bg["armor_id"])
            if starter_armor:
                self.equip_armor(starter_armor)

        if bg["starting_items"]:
            for item_id, qty in bg["starting_items"]:
                item = ItemDatabase.get(item_id)
                if item:
                    self.inventory.add(item, qty)

        self.experience = 0
        self.companions: List[Companion] = []
        self.accepted_quests: List = []
        self.total_damage_dealt = 0
        self.total_damage_taken = 0
        self.enemies_defeated = 0
        self.battles_fought = 0
        self.last_location_pos: Dict[str, Tuple[float, float]] = {}
        # Позиции и экземпляры врагов на боевых картах (сохраняются между визитами)
        self.last_enemy_positions: Dict[str, List[Tuple[float, float]]] = {}
        self.last_enemy_creatures: Dict[str, List[Optional[Creature]]] = {}
        self.defeated_bosses = set()
        self.is_sneaking = False

    def allocate_skill_point(self, skill: str) -> bool:
        """Распределить одно очко навыка. Возвращает True при успехе."""
        if skill not in self.skill_points_allocated:
            return False
        if self.skill_points_available <= 0:
            return False

        self.skill_points_allocated[skill] += 1
        self.skill_points_available -= 1
        self._recalculate_derived_stats()
        self.notify_listeners("stats_changed")
        return True

    def deallocate_skill_point(self, skill: str) -> bool:
        """Вернуть одно очко навыка. Возвращает True при успехе."""
        if skill not in self.skill_points_allocated:
            return False
        if self.skill_points_allocated[skill] <= 0:
            return False

        self.skill_points_allocated[skill] -= 1
        self.skill_points_available += 1
        self._recalculate_derived_stats()
        self.notify_listeners("stats_changed")
        return True

    def _recalculate_derived_stats(self) -> None:
        """Пересчитать производные характеристики после изменения навыков."""
        new_health = (
            self.BASE_STATS["health"]
            + self.skill_points_allocated["endurance"]
            * self.STAT_COEFFICIENTS["endurance"]["health"]
        )
        self.base_health = new_health
        self.max_health = self._scale_stat(self.base_health)
        if self.health > self.max_health:
            self.health = self.max_health

        new_damage = (
            self.BASE_STATS["damage"]
            + self.skill_points_allocated["strength"]
            * self.STAT_COEFFICIENTS["strength"]["damage"]
        )
        self.base_damage = new_damage

        new_capacity = (
            20
            + self.skill_points_allocated["strength"]
            * self.STAT_COEFFICIENTS["strength"]["inventory_capacity"]
        )
        self.inventory.capacity = max(1, int(new_capacity))

        self._critical_chance = (
            self.BASE_STATS["critical_chance"]
            + self.skill_points_allocated["agility"]
            * self.STAT_COEFFICIENTS["agility"]["critical_chance"]
        )
        self._luck = (
            self.BASE_STATS["luck"]
            + self.skill_points_allocated["luck"]
            * self.STAT_COEFFICIENTS["luck"]["luck"]
        )
        self._selling_multiplier = (
            self.BASE_STATS["selling_multiplier"]
            + self.skill_points_allocated["trade"]
            * self.STAT_COEFFICIENTS["trade"]["selling_multiplier"]
        )

        self._move_speed = (
            self.BASE_MOVE_SPEED
            + self.skill_points_allocated["speed"]
            * self.STAT_COEFFICIENTS["speed"]["move_speed"]
        )

    @property
    def critical_chance(self) -> float:
        """Шанс критического удара (0.0–1.0)."""
        return clamp(self._critical_chance, 0.0, 1.0)

    @property
    def luck(self) -> float:
        """Множитель качества лута."""
        return max(0.0, self._luck)

    @property
    def selling_multiplier(self) -> float:
        """Множитель цены при продаже."""
        return max(0.0, self._selling_multiplier)

    @property
    def move_speed(self) -> int:
        """Скорость передвижения персонажа по карте."""
        return max(self.BASE_MOVE_SPEED, int(self._move_speed))

    def add_listener(self, callback) -> None:
        """Подписать UI-колбэк на изменения состояния игрока."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback) -> None:
        """Отписать колбэк."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify_listeners(self, event: str, **payload) -> None:
        """Оповестить подписчиков о событии (health, coins, level и т.д.)."""
        for callback in list(self._listeners):
            try:
                callback(event, **payload)
            except Exception:
                pass

    def equip_weapon(self, weapon: Weapon) -> bool:
        """
        Надеть оружие с учётом инвентаря.

        Returns:
            True, если экипировка прошла успешно.
        """
        if weapon is None:
            return False

        if self.weapon and self.weapon.id == weapon.id:
            return True

        if self.weapon and not self.inventory.has_space_for(1):
            return False

        in_inv_qty = self.inventory.qty(weapon.id)
        if in_inv_qty > 0:
            self.inventory.remove(weapon.id, 1)

        if self.weapon:
            prev = self.weapon
            prev.on_unequip(self)
            self.inventory.add(prev, 1)

        self.weapon = weapon
        weapon.on_equip(self)
        self.notify_listeners("stats_changed")
        return True

    def unequip_weapon(self) -> bool:
        """Снять оружие и вернуть в инвентарь, если есть место."""
        if not self.weapon:
            return True
        prev = self.weapon
        if self.inventory.has_space_for(1):
            prev.on_unequip(self)
            self.inventory.add(prev, 1)
            self.weapon = None
            self.notify_listeners("stats_changed")
            return True
        return False

    def equip_armor(self, armor: Armor) -> bool:
        """Надеть броню с учётом инвентаря."""
        if armor is None:
            return False

        if self.armor and self.armor.id == armor.id:
            return True

        if self.armor and not self.inventory.has_space_for(1):
            return False

        if self.inventory.qty(armor.id) > 0:
            self.inventory.remove(armor.id, 1)

        if self.armor:
            prev = self.armor
            prev.on_unequip(self)
            self.inventory.add(prev, 1)

        self.armor = armor
        armor.on_equip(self)
        self.notify_listeners("stats_changed")
        return True

    def unequip_armor(self) -> bool:
        """Снять броню и вернуть в инвентарь, если есть место."""
        if not self.armor:
            return True
        prev = self.armor
        if self.inventory.has_space_for(1):
            prev.on_unequip(self)
            self.inventory.add(prev, 1)
            self.armor = None
            self.notify_listeners("stats_changed")
            return True
        return False

    def add_experience(self, exp: int) -> List[str]:
        """Начислить опыт и обработать повышения уровня."""
        msgs: List[str] = []
        if exp <= 0:
            return msgs

        old_level = self.level
        old_exp = self.experience
        self.experience += exp
        msgs.append(f"+{exp} XP")

        while self.experience >= self.level * 100:
            self.experience -= self.level * 100
            self.level += 1
            self.max_health = self._scale_stat(self.base_health)
            self.base_damage = int(
                self.base_damage + (self.level - 1) * (self.base_damage * 0.05)
            )
            self.health = self.max_health
            self.skill_points_available += 1
            msgs.append(f"🎉 Уровень! {self.name} Lv {self.level}")
            msgs.append("📊 +1 очко для распределения")

        if old_exp != self.experience:
            self.notify_listeners("experience", old=old_exp, new=self.experience)
        if old_level != self.level:
            self.notify_listeners("level", old=old_level, new=self.level)

        return msgs

    def spend_coins(self, amount: int) -> bool:
        """
        Потратить монеты, если хватает баланса.

        Returns:
            True при успешной трате.
        """
        amount = int(amount)
        if amount <= 0 or self.coins < amount:
            return False
        self.coins -= amount
        return True

    def attack(self, target: Creature) -> Tuple[int, int]:
        """Атаковать цель. Возвращает (фактический урон, сырой урон)."""
        raw = self.damage
        dealt = target.take_damage(raw)
        self.total_damage_dealt += dealt
        return dealt, raw

    def use_item(self, item_id: str, battlefield=None) -> str:
        """Использовать предмет из инвентаря."""
        item = self.inventory.get(item_id)
        if not item:
            return "У тебя нет такого предмета."
        msg = item.use(self, battlefield)
        if item.is_consumable():
            self.inventory.remove(item_id, 1)
        return msg

    def buy(self, shop, item_id: str, qty: int = 1) -> str:
        """Купить предмет в магазине."""
        return shop.buy(self, item_id, qty)

    def sell(self, shop, item_id: str, qty: int = 1) -> str:
        """Продать предмет в магазине."""
        return shop.sell(self, item_id, qty)

    def get_session_stats(self) -> dict:
        """Собрать статистику текущей сессии."""
        return {
            "name": self.name,
            "class": self.background,
            "level": self.level,
            "experience": self.experience,
            "coins": self.coins,
            "total_damage_dealt": self.total_damage_dealt,
            "total_damage_taken": self.total_damage_taken,
            "enemies_defeated": self.enemies_defeated,
            "battles_fought": self.battles_fought,
            "inventory_items": sum(q for _, q in self.inventory.list_items()),
        }

    def add_loot(self, enemy_loot: str, enemy_loot_quantity: int) -> bool:
        """
        Добавить лут в инвентарь.

        Raises:
            ValueError: при некорректном ID или количестве.
        """
        if not isinstance(enemy_loot, str) or not enemy_loot.strip():
            raise ValueError("enemy_loot должен быть непустым ID предмета.")
        if not isinstance(enemy_loot_quantity, int) or enemy_loot_quantity <= 0:
            raise ValueError("enemy_loot_quantity должен быть положительным целым.")

        if not self.inventory.has_space_for(enemy_loot_quantity):
            return False

        item = ItemDatabase.get(enemy_loot)
        if item is None:
            return False
        return self.inventory.add(item, enemy_loot_quantity)

    @property
    def coins(self) -> int:
        """Текущий баланс монет."""
        return super().coins

    @coins.setter
    def coins(self, value: int) -> None:
        """Установить монеты с clamp >= 0 и уведомлением UI."""
        old = super().coins
        clamped = max(0, int(value))
        self._coins = clamped
        if old != clamped:
            self.notify_listeners("coins", old=old, new=clamped)

    @property
    def health(self) -> int:
        """Текущее здоровье."""
        return super().health

    @health.setter
    def health(self, value: int) -> None:
        """Установить здоровье с clamp и уведомлением UI."""
        old = super().health
        clamped = int(clamp(value, 0, self.max_health))
        self._health = clamped
        if old != clamped:
            self.notify_listeners("health", old=old, new=clamped)

    def update_quest_progress(self, enemy_name: str) -> None:
        """Обновить прогресс активных квестов на убийство."""
        for quest in self.accepted_quests:
            quest.update_progress(enemy_name)

    def to_dict(self) -> dict:
        """Сериализация для сохранения."""
        data = super().to_dict()
        data["type"] = "player"
        data["background"] = self.background
        data["inventory"] = self.inventory.to_dict()
        data["experience"] = self.experience
        data["skill_points_available"] = self.skill_points_available
        data["skill_points_allocated"] = self.skill_points_allocated
        data["companions"] = [c.to_dict() for c in self.companions]
        data["accepted_quests"] = [quest.to_dict() for quest in self.accepted_quests]
        data["session_stats"] = self.get_session_stats()
        data["last_location_pos"] = self.last_location_pos
        data["last_global_pos"] = (
            list(self.last_global_pos) if self.last_global_pos else None
        )
        data["last_enemy_positions"] = {
            scene_id: [list(pos) for pos in positions]
            for scene_id, positions in self.last_enemy_positions.items()
        }
        data["last_enemy_creatures"] = {
            scene_id: [creature.to_dict() if creature else None for creature in creatures]
            for scene_id, creatures in self.last_enemy_creatures.items()
        }
        data["defeated_bosses"] = list(self.defeated_bosses)
        data["is_sneaking"] = self.is_sneaking
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Player:
        """Восстановить игрока из сохранения."""
        background = data.get("background", "squire")
        player = cls(data["name"], background)

        player.level = data["level"]
        player.base_health = data["base_health"]
        player.base_damage = data["base_damage"]
        player.base_coins = data["base_coins"]
        player.health = data["health"]
        player.coins = data["coins"]
        player.experience = data.get("experience", 0)

        if "skill_points_allocated" in data:
            player.skill_points_allocated = data["skill_points_allocated"]
            player.skill_points_available = data.get("skill_points_available", 0)
            player._recalculate_derived_stats()

        player.max_health = player._scale_stat(player.base_health)
        player.base_damage = int(
            player.base_damage
            + (player.level - 1) * (player.base_damage * 0.05)
        )

        if "inventory" in data:
            ItemDatabase.initialize()
            player.inventory = Inventory.from_dict(data["inventory"])

        if data.get("weapon_id"):
            weapon = ItemDatabase.get(data["weapon_id"])
            if weapon:
                player.equip_weapon(weapon)

        if data.get("armor_id"):
            armor = ItemDatabase.get(data["armor_id"])
            if armor:
                player.equip_armor(armor)

        if "companions" in data:
            player.companions = [
                Companion.from_dict(c) for c in data["companions"]
            ]

        if "accepted_quests" in data:
            player.accepted_quests = []

        player.last_location_pos = {
            scene_id: tuple(pos)
            for scene_id, pos in data.get("last_location_pos", {}).items()
        }
        gp = data.get("last_global_pos")
        player.last_global_pos = tuple(gp) if gp else None
        player.last_enemy_positions = {
            scene_id: [tuple(pos) for pos in positions]
            for scene_id, positions in data.get("last_enemy_positions", {}).items()
        }
        player.last_enemy_creatures = {}
        for scene_id, creatures in data.get("last_enemy_creatures", {}).items():
            restored: List[Optional[Creature]] = []
            for creature_data in creatures:
                if creature_data is None:
                    restored.append(None)
                else:
                    restored.append(Creature.from_dict(creature_data))
            player.last_enemy_creatures[scene_id] = restored
        player.defeated_bosses = set(data.get("defeated_bosses", []))
        player.is_sneaking = bool(data.get("is_sneaking", False))

        return player


class TestPlayer(Player):
    """Тестовый игрок с усиленными характеристиками для QA и отладки."""

    def __init__(self, name: str):
        """Создать персонажа с максимальным снаряжением для тестов."""
        ItemDatabase.initialize()
        super().__init__(name, "squire")

        self.base_health = 1000
        self.base_damage = 1000
        self.max_health = self._scale_stat(self.base_health)
        self.health = self.max_health
        self.coins = 10000

        self.inventory = Inventory(capacity=20)

        test_weapon = ItemDatabase.get("w_dragon_sword")
        if test_weapon:
            self.equip_weapon(test_weapon)

        test_armor = ItemDatabase.get("a_dragon_lord_plate")
        if test_armor:
            self.equip_armor(test_armor)

        test_potion = ItemDatabase.get("p_mega")
        if test_potion:
            self.inventory.add(test_potion, 19)
```

### 4.5. `ui/screens/location_select.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Экран выбора локации на карте региона."""

import os
import random

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Translate, Scale
from kivy.clock import Clock
from kivy.metrics import dp

from ui.ui_styles import COLORS, BUTTONS_DIR
from data.locations import LocationManager
from data.local_scenes import COMBAT_SCENES, enter_local_scene, resolve_global_map_background
from ui.widgets.cover_background import cover_background_image
from ui.widgets.danger_bar import DangerBar
from ui.bindings.keyboard_handler import KeyboardHandler
from systems.roaming_entity_manager import RoamingEntityManager
from systems.stealth_controller import StealthController, StealthMode, DetectionLevel
from ui.widgets.encounter_dialog import EncounterDialog


class LocationSelectScreen(Screen, KeyboardHandler):
    """Экран выбора локации с информацией."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_location = None
        self.location_manager = None
        self.game = None

        # --- Camera constants ---
        self.CAMERA_ZOOM = 2.5
        self.CAMERA_LERP_SPEED = 6.0
        self.GLOBAL_MAP_SPEED_MULTIPLIER = 0.4
        self.PLAYER_MARKER_SIZE = dp(14)

        # --- Camera state (world pixel coords) ---
        self._cam_x = 0.0
        self._cam_y = 0.0
        self._cam_target_x = 0.0
        self._cam_target_y = 0.0

        # Player world position (pixels within map_overlay)
        self._player_world_x = 0.0
        self._player_world_y = 0.0

        # Player marker on the global map (widget that moves)
        self._player_marker = None
        self._destination = None
        self._move_ev = None
        self._move_speed = dp(147)
        self._enter_btn = None
        self._kb_move = {"up": False, "down": False, "left": False, "right": False}
        self._kb_move_ev = None

        self.roaming_manager = RoamingEntityManager()
        self.stealth_controller = StealthController()
        self._token_update_ev = None
        self._token_graphics_inited = False
        self._stealth_indicator = None
        self._noise_circle = None
        self._encounter_active = False
        self._encounter_cooldown = 0.0

        self.bind_keyboard()

        # positions on the map (normalized 0..1) for location hotspots
        self._map_positions = {
            'city': (0.19, 0.85),
            'forest': (0.18, 0.45),
            'swamp': (0.50, 0.60),
            'village': (0.73, 0.52),
            'mines': (0.70, 0.20),
            'mountains': (0.70, 0.90),
        }

        main_layout = BoxLayout(
            orientation='vertical',
            padding=dp(8),
            spacing=dp(8)
        )

        with main_layout.canvas.before:
            Color(0.12, 0.14, 0.16, 1)
            self.bg_rect = Rectangle()
            main_layout.bind(
                size=lambda i, v: setattr(self.bg_rect, 'size', i.size),
                pos=lambda i, v: setattr(self.bg_rect, 'pos', i.pos)
            )

        title_label = Label(
            text='🗺️ Карта региона',
            font_size=dp(22),
            size_hint_y=None,
            height=dp(48),
            color=(0.95, 0.85, 0.6, 1),
            bold=True
        )
        main_layout.add_widget(title_label)

        # --- Map container (viewport) ---
        self.map_container = FloatLayout(size_hint=(1, 0.82))

        # World layer zoomed/panned via canvas transform
        self.map_world = FloatLayout(size_hint=(1, 1))
        with self.map_world.canvas.before:
            PushMatrix()
            self._cam_translate = Translate()
            self._cam_scale = Scale()
        with self.map_world.canvas.after:
            PopMatrix()

        map_src = resolve_global_map_background() or ""
        self.map_image = cover_background_image(map_src) if map_src else Widget(
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )
        self.map_world.add_widget(self.map_image)

        self.map_overlay = FloatLayout(size_hint=(1, 1))
        self.map_world.add_widget(self.map_overlay)

        self.map_container.add_widget(self.map_world)

        main_layout.add_widget(self.map_container)

        self.add_widget(main_layout)

        # Start camera update loop
        self._cam_ev = Clock.schedule_interval(self._camera_update, 1.0 / 60.0)

    # --- Camera ---

    def _screen_to_world(self, sx, sy):
        """Convert screen coordinates (relative to map_container) to world coordinates."""
        cw = max(1, self.map_container.width)
        ch = max(1, self.map_container.height)
        wx = (sx - cw / 2) / self.CAMERA_ZOOM + self._cam_x
        wy = (sy - ch / 2) / self.CAMERA_ZOOM + self._cam_y
        return wx, wy

    def _world_to_screen(self, wx, wy):
        """Convert world coordinates to screen coordinates (relative to map_container)."""
        cw = max(1, self.map_container.width)
        ch = max(1, self.map_container.height)
        sx = (wx - self._cam_x) * self.CAMERA_ZOOM + cw / 2
        sy = (wy - self._cam_y) * self.CAMERA_ZOOM + ch / 2
        return sx, sy

    def _camera_update(self, dt):
        """LERP camera toward target, update canvas transform."""
        lerp_factor = 1.0 - 2.71828 ** (-self.CAMERA_LERP_SPEED * dt)
        self._cam_x += (self._cam_target_x - self._cam_x) * lerp_factor
        self._cam_y += (self._cam_target_y - self._cam_y) * lerp_factor

        cw = max(1, self.map_container.width)
        ch = max(1, self.map_container.height)

        self._cam_scale.x = self.CAMERA_ZOOM
        self._cam_scale.y = self.CAMERA_ZOOM
        self._cam_translate.x = cw / 2 - self._cam_x * self.CAMERA_ZOOM
        self._cam_translate.y = ch / 2 - self._cam_y * self.CAMERA_ZOOM

    # --- Keyboard movement ---

    def _start_kb_move(self):
        if getattr(self, "_kb_move_ev", None):
            return
        self._kb_move_ev = Clock.schedule_interval(self._kb_move_tick, 1.0 / 60.0)

    def _stop_kb_move(self):
        if getattr(self, "_kb_move_ev", None):
            try:
                self._kb_move_ev.cancel()
            except Exception:
                pass
            self._kb_move_ev = None

    def _kb_move_tick(self, dt):
        if self._encounter_active:
            self._stop_kb_move()
            return
        if not getattr(self, "_player_marker", None) or not getattr(self, "map_overlay", None):
            self._stop_kb_move()
            return

        mx = (1 if self._kb_move["right"] else 0) - (1 if self._kb_move["left"] else 0)
        my = (1 if self._kb_move["up"] else 0) - (1 if self._kb_move["down"] else 0)
        if not (mx or my):
            self._stop_kb_move()
            return

        if getattr(self, "_destination", None):
            self._destination = None
            self._stop_moving()

        try:
            app = App.get_running_app()
            if getattr(app, "game", None) and getattr(app.game, "danger_manager", None):
                ambush = app.game.danger_manager.update(dt, app.game.location_manager)
                if ambush:
                    self._trigger_ambush(ambush)
                    return
        except Exception:
            pass

        length = (mx * mx + my * my) ** 0.5
        if not length:
            return

        ow = max(1, self.map_overlay.width)
        oh = max(1, self.map_overlay.height)
        speed = self._move_speed * self.GLOBAL_MAP_SPEED_MULTIPLIER * dt * self.stealth_controller.speed_multiplier
        pm_size = self.PLAYER_MARKER_SIZE

        nx = self._player_world_x + (mx / length) * speed
        ny = self._player_world_y + (my / length) * speed
        nx = max(pm_size / 2, min(nx, ow - pm_size / 2))
        ny = max(pm_size / 2, min(ny, oh - pm_size / 2))
        self._player_world_x = nx
        self._player_world_y = ny

        self._cam_target_x = nx
        self._cam_target_y = ny

        self._sync_marker_screen_pos()
        self._update_enter_button()

    # --- Hotspot helpers ---

    def _nearest_hotspot(self):
        try:
            if not getattr(self, "_player_marker", None):
                return None, None
            cx = self._player_world_x
            cy = self._player_world_y
            nearest = None
            nearest_dist = None
            for btn in getattr(self, "_hotspot_buttons", []):
                try:
                    bx = btn.pos[0] + btn.size[0] / 2
                    by = btn.pos[1] + btn.size[1] / 2
                    d = ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5
                    if nearest is None or d < nearest_dist:
                        nearest = btn
                        nearest_dist = d
                except Exception:
                    continue
            return nearest, nearest_dist
        except Exception:
            return None, None

    def _move_to_nearest_hotspot(self):
        nearest, _dist = self._nearest_hotspot()
        if not nearest:
            return False
        try:
            bx = nearest.pos[0] + nearest.size[0] / 2
            by = nearest.pos[1] + nearest.size[1] / 2
            self._destination = (bx, by)
            self._start_moving()
            return True
        except Exception:
            return False

    def _exit_to_menu(self):
        app = App.get_running_app()
        try:
            if getattr(app, "game", None) and getattr(app.game, "player", None):
                app.game.autosave()
        except Exception:
            pass
        try:
            if getattr(app, "hud", None):
                try:
                    app.hud.unbind_player()
                except Exception:
                    app.hud.opacity = 0
        except Exception:
            pass
        self.manager.current = "main_menu"

    def handle_keyboard_action(self, action: str, pressed: bool = True) -> bool:
        if action == "move_up":
            if self._encounter_active:
                return True
            self._kb_move["up"] = pressed
            (self._start_kb_move() if pressed else None)
            return True
        if action == "move_down":
            if self._encounter_active:
                return True
            self._kb_move["down"] = pressed
            (self._start_kb_move() if pressed else None)
            return True
        if action == "move_left":
            if self._encounter_active:
                return True
            self._kb_move["left"] = pressed
            (self._start_kb_move() if pressed else None)
            return True
        if action == "move_right":
            if self._encounter_active:
                return True
            self._kb_move["right"] = pressed
            (self._start_kb_move() if pressed else None)
            return True

        if action == "enter_location" and pressed:
            eb = getattr(self, "_enter_btn", None)
            if eb and getattr(eb, "opacity", 0) > 0.5:
                loc_id = getattr(eb, "_target_loc_id", None)
                if loc_id:
                    self.on_select_location(loc_id)
                    return True
            return bool(self._move_to_nearest_hotspot())

        if action == "open_inventory" and pressed:
            from ui.widgets.navigation_buttons import prepare_inventory_navigation
            app = App.get_running_app()
            prepare_inventory_navigation("location_select")
            if getattr(app, "inventory_screen", None):
                try:
                    app.inventory_screen.update_inventory()
                except Exception:
                    pass
            if getattr(app, "game", None) and getattr(app.game, "player", None):
                self.manager.current = "inventory"
            return True

        if action == "open_status" and pressed:
            app = App.get_running_app()
            if getattr(app, "status_screen", None):
                try:
                    app.status_screen.update_status()
                except Exception:
                    pass
            if getattr(app, "game", None) and getattr(app.game, "player", None):
                self.manager.current = "status"
            return True

        if action == "open_companions" and pressed:
            app = App.get_running_app()
            if getattr(app, "companion_management_screen", None):
                try:
                    app.companion_management_screen.update_companion()
                except Exception:
                    pass
            if getattr(app, "game", None) and getattr(app.game, "player", None):
                self.manager.current = "companion_management"
            return True

        if action == "open_quests" and pressed:
            app = App.get_running_app()
            if getattr(app, "active_quests_screen", None):
                try:
                    app.active_quests_screen.update_quests()
                except Exception:
                    pass
            if getattr(app, "game", None) and getattr(app.game, "player", None):
                self.manager.current = "active_quests"
            return True

        if action == "open_menu" and pressed:
            self._exit_to_menu()
            return True

        if action == "open_save" and pressed:
            app = App.get_running_app()
            try:
                if getattr(app, "game", None) and getattr(app.game, "player", None):
                    app.game.autosave()
            except Exception:
                pass
            return True

        if action == "toggle_sneak" and pressed:
            if self.stealth_controller.mode == StealthMode.STEALTH:
                self.stealth_controller.set_mode(StealthMode.NORMAL)
            else:
                self.stealth_controller.set_mode(StealthMode.STEALTH)
            self._update_camera_zoom()
            return True

        if action == "exit_location" and pressed:
            self._exit_to_menu()
            return True

        return False

    def update_locations(self):
        """Обновление списка локаций."""
        app = App.get_running_app()
        self.game = app.game
        pass
        self.location_manager = self.game.location_manager if (self.game and getattr(self.game, 'location_manager', None)) else LocationManager()

        try:
            pass
            self.map_overlay.clear_widgets()
            try:
                if getattr(self, '_hotspot_markers', None):
                    for entry in list(self._hotspot_markers):
                        try:
                            btn, col, ell = entry
                        except Exception:
                            try:
                                col, ell = entry
                                btn = None
                            except Exception:
                                continue
                        try:
                            if ell in self.map_overlay.canvas.before:
                                self.map_overlay.canvas.before.remove(ell)
                        except Exception:
                            pass
                        try:
                            if col in self.map_overlay.canvas.before:
                                self.map_overlay.canvas.before.remove(col)
                        except Exception:
                            pass
                    self._hotspot_markers = []
            except Exception:
                pass
        except Exception:
            pass
            try:
                self.locations_layout.clear_widgets()
            except Exception:
                pass
            for loc_id, location in self.location_manager.locations.items():
                btn_text = self._get_location_text(location)
                btn = Button(
                    text=btn_text,
                    size_hint_y=None,
                    height=dp(80),
                    font_size=dp(15),
                    background_color=(
                        (0.48, 0.35, 0.22, 1) if not location.is_locked
                        else (0.55, 0.28, 0.20, 1)
                    )
                )
                if not location.is_locked:
                    btn.bind(on_press=lambda b, lid=loc_id: self.on_select_location(lid))
                else:
                    btn.bind(on_press=lambda b, loc=location: self.on_locked_location(loc))
                self.locations_layout.add_widget(btn)
            return

        pass

        self._hotspot_buttons = []
        if not getattr(self, '_hotspot_markers', None):
            self._hotspot_markers = []

        for loc_id, location in self.location_manager.locations.items():
            pos = self._map_positions.get(loc_id)
            if not pos:
                continue
            x, y = pos
            size_dp = dp(120)
            adj_x = x
            adj_y = y
            if loc_id == 'forest':
                size_dp = dp(120) * 2
                adj_y = max(0.05, y - 0.08)
            elif loc_id == 'swamp':
                size_dp = dp(120) * 2
            elif loc_id == 'mines':
                size_dp = dp(120) * 2
                adj_x = min(0.95, x + 0.06)
            elif loc_id == 'mountains':
                size_dp = dp(120) * 2
                adj_x = max(0.05, x - 0.05)
            btn = Button(
                text='',
                size_hint=(None, None),
                size=(size_dp, size_dp),
                pos_hint={'center_x': adj_x, 'center_y': adj_y},
                background_normal='',
                background_down='',
                background_color=(0, 0, 0, 0)
            )
            btn._loc_id = loc_id
            btn._loc_name = getattr(location, 'name', loc_id)
            self._hotspot_buttons.append(btn)

            try:
                from kivy.graphics import Color, Ellipse
                col = Color(0.35, 0.22, 0.10, 0.16)
                ell = Ellipse(pos=(0, 0), size=(size_dp, size_dp))
                self.map_overlay.canvas.before.add(col)
                self.map_overlay.canvas.before.add(ell)
                self._hotspot_markers.append((btn, col, ell))

                def _update_marker(*args):
                    try:
                        ell.pos = btn.pos
                        ell.size = btn.size
                    except Exception:
                        pass

                btn.bind(pos=_update_marker, size=_update_marker)
                Clock.schedule_once(lambda dt: _update_marker(), 0.05)
            except Exception:
                pass

            self.map_overlay.add_widget(btn)

        try:
            city_pos = self._map_positions.get('city')
            cx, cy = city_pos
            size_dp = dp(120) * 2
            adj_cx = cx
            adj_cy = max(0.05, cy - 0.08)
            city_btn = Button(
                text='',
                size_hint=(None, None),
                size=(size_dp, size_dp),
                pos_hint={'center_x': adj_cx, 'center_y': adj_cy},
                background_normal='',
                background_down='',
                background_color=(0, 0, 0, 0)
            )
            city_btn._loc_id = 'city'
            city_btn._loc_name = 'Город'

            self._hotspot_buttons.append(city_btn)
            self.map_overlay.add_widget(city_btn)

            try:
                from kivy.graphics import Color, Ellipse
                col = Color(0.35, 0.22, 0.10, 0.16)
                ell = Ellipse(pos=city_btn.pos, size=city_btn.size)
                self.map_overlay.canvas.before.add(col)
                self.map_overlay.canvas.before.add(ell)
                self._hotspot_markers.append((city_btn, col, ell))

                def _update_city_marker(btn, *args):
                    try:
                        ell.pos = btn.pos
                        ell.size = btn.size
                    except Exception:
                        pass

                city_btn.bind(pos=lambda inst, val: _update_city_marker(city_btn),
                              size=lambda inst, val: _update_city_marker(city_btn))
                Clock.schedule_once(lambda dt: _update_city_marker(city_btn), 0.05)
            except Exception as e:
                pass
        except Exception:
            pass

        try:
            v_pos = self._map_positions.get('village')
            if v_pos:
                vx, vy = v_pos
                size_dp = dp(120) * 2
                village_btn = Button(
                    text='',
                    size_hint=(None, None),
                    size=(size_dp, size_dp),
                    pos_hint={'center_x': vx, 'center_y': vy},
                    background_normal='',
                    background_down='',
                    background_color=(0, 0, 0, 0)
                )
                village_btn._loc_id = 'village'
                village_btn._loc_name = 'Деревня'
                self._hotspot_buttons.append(village_btn)
                self.map_overlay.add_widget(village_btn)

                try:
                    from kivy.graphics import Color, Ellipse
                    col = Color(0.35, 0.22, 0.10, 0.16)
                    ell = Ellipse(pos=village_btn.pos, size=village_btn.size)
                    self.map_overlay.canvas.before.add(col)
                    self.map_overlay.canvas.before.add(ell)
                    self._hotspot_markers.append((village_btn, col, ell))

                    def _update_village_marker(btn, *args):
                        try:
                            ell.pos = btn.pos
                            ell.size = btn.size
                        except Exception:
                            pass

                    village_btn.bind(
                        pos=lambda inst, val: _update_village_marker(village_btn),
                        size=lambda inst, val: _update_village_marker(village_btn),
                    )
                    Clock.schedule_once(lambda dt: _update_village_marker(village_btn), 0.05)
                except Exception:
                    pass
        except Exception:
            pass

        # Hover tooltip widget
        if not hasattr(self, '_hover_widget'):
            hw = BoxLayout(size_hint=(None, None), size=(dp(180), dp(40)))
            with hw.canvas.before:
                Color(0.12, 0.07, 0.03, 0.9)
                hw._rect = Rectangle(pos=hw.pos, size=hw.size)
            lbl = Label(text='', halign='center', valign='middle', color=(1, 1, 1, 1))
            lbl.text_size = (hw.width, hw.height)
            hw.add_widget(lbl)
            hw.label = lbl
            hw.opacity = 0
            self.map_overlay.add_widget(hw)
            hw.bind(pos=lambda inst, val: setattr(hw._rect, 'pos', val))
            hw.bind(size=lambda inst, val: setattr(hw._rect, 'size', val))
            self._hover_widget = hw

        try:
            from kivy.core.window import Window
            if not getattr(self, '_mouse_bound', False):
                Window.bind(mouse_pos=self._on_mouse_pos)
                self._mouse_bound = True
        except Exception:
            pass

        try:
            if not getattr(self, '_map_touch_bound', False):
                try:
                    self.map_overlay.bind(on_touch_down=self._on_map_touch)
                except Exception:
                    pass
                self._map_touch_bound = True
        except Exception:
            pass

        try:
            def _refresh_all_markers(*args):
                try:
                    if not getattr(self, '_hotspot_markers', None):
                        return
                    for entry in self._hotspot_markers:
                        try:
                            btn, col, ell = entry
                        except Exception:
                            continue
                        try:
                            ell.pos = btn.pos
                            ell.size = btn.size
                        except Exception:
                            pass
                except Exception:
                    pass

            self.map_overlay.bind(size=_refresh_all_markers, pos=_refresh_all_markers)
            Clock.schedule_once(lambda dt: _refresh_all_markers(), 0.1)
        except Exception:
            pass

        # Create player marker
        try:
            if not getattr(self, '_player_marker', None):
                size_px = self.PLAYER_MARKER_SIZE
                start_world_x = 0.25
                start_world_y = 0.60
                adj_cx = start_world_x
                adj_cy = start_world_y
                pm = Widget(size_hint=(None, None), size=(size_px, size_px))
                from kivy.graphics import Color, Ellipse
                with pm.canvas:
                    Color(0.12, 0.08, 0.03, 1)
                    pm._outline = Ellipse(pos=(pm.x - dp(2), pm.y - dp(2)), size=(pm.width + dp(4), pm.height + dp(4)))
                    Color(1.0, 0.85, 0.05, 1)
                    pm._ell = Ellipse(pos=pm.pos, size=pm.size)

                def _update_pm(*args):
                    try:
                        pm._ell.pos = pm.pos
                        pm._ell.size = pm.size
                        pm._outline.pos = (pm.x - dp(2), pm.y - dp(2))
                        pm._outline.size = (pm.width + dp(4), pm.height + dp(4))
                    except Exception:
                        pass
                pm.bind(pos=_update_pm, size=_update_pm)

                # Add player marker to map_container (screen-space, outside camera transform)
                self.map_container.add_widget(pm)
                self._player_marker = pm

                def _place_pm(dt=None):
                    try:
                        if getattr(self, '_position_set', False):
                            return
                        w = max(1, self.map_overlay.width)
                        h = max(1, self.map_overlay.height)
                        self._player_world_x = float(w * 0.25)
                        self._player_world_y = float(h * 0.60)
                        self._cam_target_x = self._player_world_x
                        self._cam_target_y = self._player_world_y
                        self._cam_x = self._player_world_x
                        self._cam_y = self._player_world_y
                        sx, sy = self._world_to_screen(self._player_world_x, self._player_world_y)
                        pm.pos = (sx - pm.width / 2, sy - pm.height / 2)
                        _update_pm()
                        self._position_set = True
                    except Exception:
                        pass

                Clock.schedule_once(_place_pm, 0.06)
                self.map_overlay.bind(size=self._reposition_marker_on_resize)
        except Exception:
            pass

        # Danger Bar
        def _place_danger_bar(dt=None):
            try:
                ow = self.map_container.width
                oh = self.map_container.height
                db = self._danger_bar
                if not db or db.width <= 0 or db.height <= 0:
                    return
                x = int(ow * 0.82) - db.width
                y = oh - db.height - dp(8)
                db.pos = (max(dp(4), x), max(dp(4), y))
            except Exception:
                pass

        try:
            if not getattr(self, '_danger_bar', None) or self._danger_bar.parent is None:
                if getattr(self, '_danger_bar', None):
                    self._danger_bar.cleanup()
                danger_bar = DangerBar()
                self.map_container.add_widget(danger_bar)
                self._danger_bar = danger_bar
                Clock.schedule_once(_place_danger_bar, 0.12)
                self.map_container.bind(size=lambda i, v: _place_danger_bar())
            else:
                try:
                    self.map_container.remove_widget(self._danger_bar)
                except Exception:
                    pass
                self.map_container.add_widget(self._danger_bar)
        except Exception:
            pass

        # Exit to main menu button
        def _exit_to_menu(*args):
            app = App.get_running_app()
            try:
                if getattr(app, 'game', None) and getattr(app.game, 'player', None):
                    app.game.autosave()
            except Exception as e:
                pass
            try:
                if getattr(app, 'hud', None):
                    try:
                        app.hud.unbind_player()
                    except Exception:
                        app.hud.opacity = 0
            except Exception:
                pass
            self.manager.current = 'main_menu'

        exit_menu_btn = Button(
            text='',
            size_hint=(None, None),
            size=(dp(56), dp(56)),
            pos_hint={'right': 0.98, 'top': 0.98},
            background_normal=os.path.join(BUTTONS_DIR, 'menu.png'),
            background_down=os.path.join(BUTTONS_DIR, 'menu.png'),
            background_color=(1, 1, 1, 1)
        )
        exit_menu_btn.bind(on_press=_exit_to_menu)
        self.map_container.add_widget(exit_menu_btn)

        # Inventory quick-access button
        def _open_inventory(*args):
            from ui.widgets.navigation_buttons import prepare_inventory_navigation

            app = App.get_running_app()
            prepare_inventory_navigation('location_select')
            if getattr(app, 'inventory_screen', None):
                try:
                    app.inventory_screen.update_inventory()
                except Exception:
                    pass
            if getattr(app, 'game', None) and getattr(app.game, 'player', None):
                try:
                    self.manager.current = 'inventory'
                except Exception:
                    pass

        inv_btn = Button(
            text='',
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.01, 'y': 0.01},
            background_normal=os.path.join(BUTTONS_DIR, 'inventory.png'),
            background_down=os.path.join(BUTTONS_DIR, 'inventory.png'),
            background_color=(1, 1, 1, 1)
        )
        inv_btn.bind(on_press=_open_inventory)
        self.map_container.add_widget(inv_btn)

        # Status button
        def _open_status(*args):
            app = App.get_running_app()
            if getattr(app, 'status_screen', None):
                try:
                    app.status_screen.update_status()
                except Exception:
                    pass
            if getattr(app, 'game', None) and getattr(app.game, 'player', None):
                try:
                    self.manager.current = 'status'
                except Exception:
                    pass

        status_btn = Button(
            text='',
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.12, 'y': 0.01},
            background_normal=os.path.join(BUTTONS_DIR, 'status.png'),
            background_down=os.path.join(BUTTONS_DIR, 'status.png'),
            background_color=(1, 1, 1, 1)
        )
        status_btn.bind(on_press=_open_status)
        self.map_container.add_widget(status_btn)

        # Companions button
        def _open_companions(*args):
            app = App.get_running_app()
            if getattr(app, 'companion_management_screen', None):
                try:
                    app.companion_management_screen.update_companion()
                except Exception:
                    pass
            if getattr(app, 'game', None) and getattr(app.game, 'player', None):
                try:
                    self.manager.current = 'companion_management'
                except Exception:
                    pass

        comp_btn = Button(
            text='',
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.23, 'y': 0.01},
            background_normal=os.path.join(BUTTONS_DIR, 'companion.png'),
            background_down=os.path.join(BUTTONS_DIR, 'companion.png'),
            background_color=(1, 1, 1, 1)
        )
        comp_btn.bind(on_press=_open_companions)
        self.map_container.add_widget(comp_btn)

        # Quests button
        def _open_active_quests(*args):
            app = App.get_running_app()
            if getattr(app, 'active_quests_screen', None):
                try:
                    app.active_quests_screen.update_quests()
                except Exception:
                    pass
            if getattr(app, 'game', None) and getattr(app.game, 'player', None):
                try:
                    self.manager.current = 'active_quests'
                except Exception:
                    pass

        quests_btn = Button(
            text='',
            size_hint=(None, None),
            size=(dp(72), dp(72)),
            pos_hint={'x': 0.34, 'y': 0.01},
            background_normal=os.path.join(BUTTONS_DIR, 'active_quests.png'),
            background_down=os.path.join(BUTTONS_DIR, 'active_quests.png'),
            background_color=(1, 1, 1, 1)
        )
        quests_btn.bind(on_press=_open_active_quests)
        self.map_container.add_widget(quests_btn)

        # Token spawning + graphics deferred to _start_token_updates (called from on_enter)
        # when map_overlay has its final layout size

    def _update_tokens(self, dt):
        try:
            if self._encounter_active:
                self.roaming_manager.update_graphics()
                return

            if self._encounter_cooldown > 0:
                self._encounter_cooldown = max(0.0, self._encounter_cooldown - dt)
                px = self._player_world_x
                py = self._player_world_y
                moved = abs(px - self._prev_player_world_x) > 0.5 or abs(py - self._prev_player_world_y) > 0.5 if hasattr(self, '_prev_player_world_x') else False
                is_sneaking = (self.stealth_controller.mode == StealthMode.STEALTH)
                self.roaming_manager.update(dt, px, py, player_is_noisy=(moved and not is_sneaking), is_sneaking=is_sneaking)
                self.roaming_manager.update_graphics()
                self._prev_player_world_x = px
                self._prev_player_world_y = py
                return

            px = self._player_world_x
            py = self._player_world_y

            moved = False
            if hasattr(self, '_prev_player_world_x'):
                dx = abs(px - self._prev_player_world_x)
                dy = abs(py - self._prev_player_world_y)
                moved = dx > 0.5 or dy > 0.5

            is_sneaking = (self.stealth_controller.mode == StealthMode.STEALTH)
            player_is_noisy = moved and not is_sneaking

            encounter = self.roaming_manager.update(
                dt,
                px,
                py,
                player_is_noisy=player_is_noisy,
                is_sneaking=is_sneaking,
            )
            if encounter:
                self._encounter_active = True
                self._stop_moving()
                self._stop_kb_move()
                self._show_encounter(encounter)

            self.roaming_manager.update_graphics()

            self._prev_player_world_x = px
            self._prev_player_world_y = py
        except Exception:
            pass

    def _destroy_all_token_canvas(self):
        try:
            self.roaming_manager.destroy_graphics()
            self._token_graphics_inited = False
        except Exception:
            pass

    def _get_location_text(self, location):
        """Получить текст кнопки локации."""
        lock_icon = '🔐' if location.is_locked else '🔓'
        difficulty = {
            'forest': '⭐ Лёгкая',
            'swamp': '⭐⭐ Средняя',
            'mines': '⭐⭐⭐ Сложная',
            'mountains': '⭐⭐⭐⭐ Очень сложная',
            'ancient': '⭐⭐⭐⭐⭐ Экстрем'
        }.get(location.id, 'Неизвестная')

        text = f"{lock_icon} {location.name}\n{difficulty}"

        if location.is_locked and location.unlock_condition:
            text += f"\n⚠️ {location.unlock_condition}"
        else:
            text += f"\n✅ Враги: {len(location.enemy_types)}"

        return text

    def _on_mouse_pos(self, window, pos):
        """Handle global mouse movement to show hover tooltip for hotspots."""
        try:
            if not getattr(self, 'map_overlay', None) or not getattr(self, '_hotspot_buttons', None):
                return

            found = None
            mouse_x, mouse_y = pos

            # Convert mouse screen coords to world coords relative to map_container
            try:
                local = self.map_container.to_widget(mouse_x, mouse_y)
                world_x, world_y = self._screen_to_world(local[0], local[1])
            except Exception:
                world_x, world_y = mouse_x, mouse_y

            if not getattr(self, '_debug_logged_mouse', False):
                print(f"[DEBUG _on_mouse_pos] _hotspot_buttons count: {len(self._hotspot_buttons)}")
                self._debug_logged_mouse = True

            for btn in self._hotspot_buttons:
                try:
                    btn_x = btn.pos[0]
                    btn_y = btn.pos[1]
                    btn_right = btn_x + btn.size[0]
                    btn_top = btn_y + btn.size[1]

                    if btn_x <= world_x <= btn_right and btn_y <= world_y <= btn_top:
                        found = btn
                        break
                except Exception:
                    continue

            if not found:
                try:
                    for token in self.roaming_manager.tokens:
                        if token.id in self.roaming_manager._lockout_ids:
                            continue
                        d = ((world_x - token.x) ** 2 + (world_y - token.y) ** 2) ** 0.5
                        if d < 16.0:
                            found = token
                            break
                except Exception:
                    pass

            if found and getattr(self, '_hover_widget', None):
                hw = self._hover_widget
                try:
                    if hasattr(found, '_loc_name'):
                        hw.label.text = found._loc_name
                    elif hasattr(found, 'name'):
                        zone = self.roaming_manager.get_zone_at(
                            found.x, found.y
                        )
                        loc_name = zone.location_id if zone else ""
                        hw.label.text = f"{found.name} ({loc_name})"
                    else:
                        hw.label.text = str(found._loc_id)
                except Exception:
                    hw.label.text = str(found)
                try:
                    from kivy.core.window import Window
                    x = mouse_x - hw.width / 2
                    y = mouse_y + dp(10)
                    try:
                        root = App.get_running_app().root
                        max_x = max(0, root.width - hw.width)
                        max_y = max(0, root.height - hw.height)
                        x = max(0, min(x, max_x))
                        y = max(0, min(y, max_y))
                        try:
                            if hw.parent is not root:
                                try:
                                    hw.parent.remove_widget(hw)
                                except Exception:
                                    pass
                                try:
                                    root.add_widget(hw)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        hw.pos = (x, y)
                    except Exception:
                        try:
                            cx = found.pos[0] + found.size[0] / 2
                            cy = found.pos[1] + found.size[1] / 2
                            x = cx - hw.width / 2
                            y = cy + dp(10)
                            parent = self.map_overlay
                            max_x = max(0, parent.width - hw.width)
                            x = max(0, min(x, max_x))
                            max_y = max(0, parent.height - hw.height)
                            y = max(0, min(y, max_y))
                            hw.pos = (x, y)
                        except Exception:
                            pass
                except Exception:
                    pass
                hw.opacity = 1
            else:
                try:
                    if getattr(self, '_hover_widget', None):
                        self._hover_widget.opacity = 0
                except Exception:
                    pass
        except Exception:
            pass

    # --- Movement & map interaction for player marker ---

    def _on_map_touch(self, instance, touch):
        """Handle clicks/touches on the map overlay to set destination."""
        try:
            if self._encounter_active:
                return False
            if not getattr(self, 'map_overlay', None):
                return False
            tb = getattr(touch, 'button', None)
            if tb and tb != 'left':
                return False
            try:
                # Convert touch screen coords to world coords
                local = self.map_container.to_widget(touch.x, touch.y)
                world_x, world_y = self._screen_to_world(local[0], local[1])

                try:
                    for child in list(self.map_overlay.children):
                        if child is getattr(self, '_player_marker', None) or child is getattr(self, '_hover_widget', None):
                            continue
                        try:
                            if hasattr(child, '_loc_id'):
                                continue
                        except Exception:
                            pass
                        try:
                            if child.collide_point(world_x, world_y):
                                return False
                        except Exception:
                            continue
                except Exception:
                    pass

                self._destination = (world_x, world_y)
            except Exception:
                self._destination = touch.pos
            self._start_moving()
            return True
        except Exception:
            return False

    def _sync_marker_screen_pos(self):
        """Update player marker's screen position based on world coords and camera."""
        try:
            pm = self._player_marker
            if not pm:
                return
            sx, sy = self._world_to_screen(self._player_world_x, self._player_world_y)
            pm.pos = (sx - pm.width / 2, sy - pm.height / 2)
            # Update label
            if getattr(self, '_player_label', None):
                player_label = self._player_label
                label_x = sx - player_label.width / 2
                label_y = sy + pm.size[1] + dp(5)
                player_label.pos = (label_x, label_y)
        except Exception:
            pass

    def _reposition_marker_on_resize(self, instance, new_size):
        """Безопасный обработчик ресайза: не меняет мировые координаты,
        только пересчитывает экранную позицию маркера."""
        try:
            pm = self._player_marker
            if not pm:
                return
            sx, sy = self._world_to_screen(self._player_world_x, self._player_world_y)
            pm.pos = (sx - pm.width / 2, sy - pm.height / 2)
            if getattr(self, '_player_label', None):
                player_label = self._player_label
                label_x = sx - player_label.width / 2
                label_y = sy + pm.size[1] + dp(5)
                player_label.pos = (label_x, label_y)
        except Exception:
            pass

    def _start_moving(self):
        try:
            if getattr(self, '_move_ev', None):
                return
            self._move_ev = Clock.schedule_interval(self._move_player, 1.0 / 60.0)
        except Exception:
            pass

    def _stop_moving(self):
        try:
            if getattr(self, '_move_ev', None):
                self._move_ev.cancel()
                self._move_ev = None
        except Exception:
            pass

    def _move_player(self, dt):
        """Move the player marker towards destination each frame."""
        try:
            if self._encounter_active:
                self._stop_moving()
                return
            if not getattr(self, '_player_marker', None) or not getattr(self, '_destination', None):
                self._stop_moving()
                return
            try:
                app = App.get_running_app()
                if (getattr(app, 'game', None)
                        and getattr(app.game, 'danger_manager', None)):
                    ambush = app.game.danger_manager.update(
                        dt, app.game.location_manager
                    )
                    if ambush:
                        self._stop_moving()
                        self._trigger_ambush(ambush)
                        return
            except Exception:
                pass

            ow = max(1, self.map_overlay.width)
            oh = max(1, self.map_overlay.height)
            pm_size = self.PLAYER_MARKER_SIZE
            cur_x = self._player_world_x
            cur_y = self._player_world_y
            dest_x, dest_y = self._destination
            dx = dest_x - cur_x
            dy = dest_y - cur_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < 4:
                self._destination = None
                self._stop_moving()
                self._update_enter_button()
                return
            step = self._move_speed * self.GLOBAL_MAP_SPEED_MULTIPLIER * dt * self.stealth_controller.speed_multiplier
            if step >= dist:
                self._player_world_x = dest_x
                self._player_world_y = dest_y
            else:
                self._player_world_x = cur_x + dx / dist * step
                self._player_world_y = cur_y + dy / dist * step

            self._player_world_x = max(pm_size / 2, min(self._player_world_x, ow - pm_size / 2))
            self._player_world_y = max(pm_size / 2, min(self._player_world_y, oh - pm_size / 2))

            self._cam_target_x = self._player_world_x
            self._cam_target_y = self._player_world_y

            self._sync_marker_screen_pos()
            self._update_enter_button()
        except Exception:
            pass

    def _check_roaming_collision(self):
        pass

    def _show_encounter(self, encounter_data: dict):
        try:
            dialog = EncounterDialog(encounter_data)
            dialog.set_result_handler(self._on_encounter_result)
            dialog.open()
        except Exception:
            self._encounter_active = False

    def _on_encounter_result(self, action_id: str, encounter_data: dict):
        self._encounter_active = False
        self._encounter_cooldown = 2.0

        group = encounter_data.get("group", [])
        main_token_id = encounter_data.get("token_id", "")

        if action_id == "fight":
            for member in group:
                self.roaming_manager.remove_token(member.get("token_id", ""))
            self._start_encounter_battle(encounter_data)
        else:
            for member in group:
                self.roaming_manager.reset_token(member.get("token_id", main_token_id), cooldown=10.0)

    def _start_encounter_battle(self, encounter_data: dict):
        try:
            app = App.get_running_app()
            if not app.game or not app.game.player:
                return
            group = encounter_data.get("group", [])
            if not group:
                return
            from data.enemies import EnemyDatabase
            from core.creatures import Creature
            from core.combat.enemy_spawner import EnemyGenerator
            player = app.game.player
            enemies = []
            names = []
            for member in group:
                enemy_type = member.get("enemy_type", "")
                enemy_name = member.get("name", "Враг")
                template = EnemyDatabase.get(enemy_type)
                if not template:
                    enemy = Creature(
                        enemy_name,
                        base_health=30,
                        base_damage=8,
                        base_coins=5,
                        level=max(1, player.level),
                    )
                    enemies.append(enemy)
                    names.append(enemy_name)
                    continue
                enemy = Creature(
                    template.name,
                    template.base_health,
                    template.base_damage,
                    template.base_coins,
                    level=max(1, player.level),
                )
                enemy._template = template
                EnemyGenerator._equip_from_loot_table(enemy)
                enemies.append(enemy)
                names.append(member.get("name", template.name))
            if not enemies:
                return

            surprise = encounter_data.get("surprise_attack", False)
            battlefield, _ = app.game.create_battle(enemies)
            if surprise:
                battlefield.surprise_attack_ready = True
            title = ", ".join(names)
            if len(names) > 1:
                title = f"⚔️ {title} ({len(names)} врага)"
            else:
                title = f"⚔️ {title}"
            if surprise:
                title = f"🗡️ Крит! {title}"
            app.battle_screen.start_battle(battlefield, title)
            self.manager.current = "battle"
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _update_camera_zoom(self):
        self.CAMERA_ZOOM = self.stealth_controller.camera_zoom

    def _start_token_updates(self):
        if self._token_update_ev:
            return
        if not self._token_graphics_inited:
            try:
                ow = max(1, self.map_overlay.width)
                oh = max(1, self.map_overlay.height)
                self.roaming_manager.set_map_size(ow, oh)
                self.roaming_manager.init_graphics(self.map_overlay.canvas.before)
                self._token_graphics_inited = True
            except Exception:
                pass
        self._token_update_ev = Clock.schedule_interval(self._update_tokens, 0.1)

    def _stop_token_updates(self):
        if self._token_update_ev:
            self._token_update_ev.cancel()
            self._token_update_ev = None
        self._destroy_all_token_canvas()

    def _update_enter_button(self):
        """Show enter button if player is near a hotspot, hide otherwise."""
        try:
            if not getattr(self, '_player_marker', None):
                return
            cx = self._player_world_x
            cy = self._player_world_y
            nearest = None
            nearest_dist = 1e9
            for btn in getattr(self, '_hotspot_buttons', []):
                try:
                    bx = btn.pos[0] + btn.size[0] / 2
                    by = btn.pos[1] + btn.size[1] / 2
                    d = ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5
                    if d < nearest_dist:
                        nearest_dist = d
                        nearest = btn
                except Exception:
                    continue
            show = False
            loc_id = None
            if nearest:
                radius = min(nearest.size[0], nearest.size[1]) / 2
                if nearest_dist <= max(42, radius * 0.6):
                    show = True
                    loc_id = getattr(nearest, '_loc_id', None)
            if show:
                if not getattr(self, '_enter_btn', None):
                    eb = Button(text='Войти', size_hint=(None, None), size=(dp(92), dp(40)))
                    def _enter(b):
                        try:
                            entered_loc = getattr(b, '_target_loc_id', 'city')
                            self.on_select_location(entered_loc)
                        except Exception:
                            pass
                    eb.bind(on_press=_enter)
                    self._enter_btn = eb
                    try:
                        root = App.get_running_app().root
                        root.add_widget(eb)
                    except Exception:
                        try:
                            self.map_container.add_widget(eb)
                        except Exception:
                            pass
                try:
                    eb = self._enter_btn
                    eb._target_loc_id = loc_id
                    # Position enter button in screen space, near player's screen position
                    sx, sy = self._world_to_screen(cx, cy)
                    win = App.get_running_app().root
                    ex = sx - eb.width / 2
                    ey = sy - self.PLAYER_MARKER_SIZE / 2 - eb.height - dp(6)
                    ex = max(0, min(ex, max(0, win.width - eb.width)))
                    ey = max(0, min(ey, max(0, win.height - eb.height)))
                    eb.pos = (ex, ey)
                    eb.opacity = 1
                except Exception:
                    pass
            else:
                if getattr(self, '_enter_btn', None):
                    try:
                        self._enter_btn.opacity = 0
                    except Exception:
                        pass
        except Exception:
            pass

    def on_select_location(self, loc_id):
        """Выбор локации для входа."""
        app = App.get_running_app()
        if not getattr(app, 'game', None) or not getattr(app.game, 'player', None):
            popup = Popup(
                title='Ошибка',
                content=Label(text='Игра не инициализирована!'),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            return

        player = app.game.player
        player.last_global_pos = (
            self._player_world_x / max(1, self.map_overlay.width),
            self._player_world_y / max(1, self.map_overlay.height),
        )
        player.is_sneaking = (self.stealth_controller.mode == StealthMode.STEALTH)

        try:
            location_mgr = app.game.location_manager
            if not location_mgr.is_location_available(loc_id):
                location = location_mgr.get_location(loc_id)
                unlock_msg = location.unlock_description() if location else "Локация заблокирована"
                popup = Popup(
                    title='Локация закрыта',
                    content=Label(text=unlock_msg),
                    size_hint=(0.7, 0.3)
                )
                popup.open()
                return
        except Exception as e:
            print(f"[DEBUG] Error checking location availability: {e}")
            pass

        if loc_id in COMBAT_SCENES or loc_id == 'city':
            screen = getattr(app, 'local_location_screen', None)
            if not screen:
                return
            if loc_id in COMBAT_SCENES:
                screen._defeated_enemies = set()
                screen._returning_from_battle = False
            if enter_local_scene(app, loc_id):
                return
            popup = Popup(
                title='Ошибка',
                content=Label(text='Не удалось открыть локацию.'),
                size_hint=(0.6, 0.3),
            )
            popup.open()
            return

        if loc_id == 'ancient_cave':
            popup = Popup(
                title='Пещера Древних',
                content=Label(
                    text='Боссы теперь обитают в своих локациях:\n'
                         'лес, болота, шахты и горы.',
                    halign='center',
                ),
                size_hint=(0.7, 0.35),
            )
            popup.open()
            return

        if loc_id == 'village':
            popup = Popup(
                title='Деревня',
                content=Label(text='в разработке', halign='center'),
                size_hint=(0.6, 0.28),
            )
            popup.open()
            return

    def on_status(self, instance):
        """Открыть статус."""
        self.manager.current = 'status'

    def on_enter(self):
        """Обновить карту при входе на экран."""
        try:
            app = App.get_running_app()
            player = app.game.player if app.game else None
            gp = player.last_global_pos if player else None
            if gp and hasattr(self, 'map_overlay') and hasattr(self, '_player_marker'):
                w = max(1, self.map_overlay.width)
                h = max(1, self.map_overlay.height)
                self._player_world_x = float(w * gp[0])
                self._player_world_y = float(h * gp[1])
                self._cam_target_x = self._player_world_x
                self._cam_target_y = self._player_world_y
                self._cam_x = self._player_world_x
                self._cam_y = self._player_world_y
                pm = self._player_marker
                sx, sy = self._world_to_screen(self._player_world_x, self._player_world_y)
                pm.pos = (sx - pm.width / 2, sy - pm.height / 2)
                player.last_global_pos = None
                self._position_set = True
        except Exception:
            pass

        try:
            app = App.get_running_app()
            if app.game and app.game.player and app.game.player.is_sneaking:
                self.stealth_controller.set_mode(StealthMode.STEALTH)
                self._update_camera_zoom()
        except Exception:
            pass

        try:
            self.update_locations()
        except Exception:
            pass

        self._encounter_active = False
        self._encounter_cooldown = 0.0
        self.roaming_manager._lockout_ids.clear()
        self._prev_player_world_x = self._player_world_x
        self._prev_player_world_y = self._player_world_y
        self._start_token_updates()

        try:
            if hasattr(self, 'map_overlay') and hasattr(self, '_player_marker'):
                app = App.get_running_app()
                if app.game and app.game.player:
                    if hasattr(self, '_player_label') and self._player_label:
                        try:
                            self.map_container.remove_widget(self._player_label)
                        except Exception:
                            pass

                    player_name = app.game.player.name
                    player_label = Label(
                        text=player_name,
                        size_hint=(None, None),
                        size=(dp(100), dp(25)),
                        font_size=dp(14),
                        color=COLORS['gold'],
                        bold=True
                    )
                    # Add label to map_container (screen space), not map_overlay
                    self.map_container.add_widget(player_label)
                    self._player_label = player_label

                    # Position it above the player marker, using screen coords
                    sx, sy = self._world_to_screen(self._player_world_x, self._player_world_y)
                    label_x = sx - player_label.width / 2
                    label_y = sy + self.PLAYER_MARKER_SIZE / 2 + dp(5)
                    player_label.pos = (label_x, label_y)
        except Exception as e:
            print(f"[ERROR] Failed to create player label: {e}")

        try:
            from kivy.core.window import Window
            try:
                Window.unbind(mouse_pos=self._on_mouse_pos)
            except Exception:
                pass
            try:
                Window.bind(mouse_pos=self._on_mouse_pos)
            except Exception:
                pass
        except Exception:
            pass

    def on_leave(self):
        """Cleanup when leaving screen: hide tooltip, unbind mouse handler, remove enter button."""
        try:
            if getattr(self, '_danger_bar', None):
                self._danger_bar.cleanup()
                try:
                    self.map_container.remove_widget(self._danger_bar)
                except Exception:
                    pass
                self._danger_bar = None
        except Exception:
            pass
        try:
            if getattr(self, '_hover_widget', None):
                try:
                    self._hover_widget.opacity = 0
                except Exception:
                    pass
        except Exception:
            pass
        try:
            from kivy.core.window import Window
            try:
                Window.unbind(mouse_pos=self._on_mouse_pos)
            except Exception:
                pass
        except Exception:
            pass
        try:
            if getattr(self, '_enter_btn', None):
                root = App.get_running_app().root
                if self._enter_btn in root.children:
                    root.remove_widget(self._enter_btn)
                self._enter_btn = None
        except Exception:
            pass

        self._stop_token_updates()

    def _trigger_ambush(self, enemy_id):
        """Начать бой при засаде (danger = 100%) с предупреждением."""
        try:
            app = App.get_running_app()
            if not app.game or not app.game.player:
                return
            from data.enemies import EnemyDatabase
            template = EnemyDatabase.get(enemy_id)
            if not template:
                return
            from core.creatures import Creature
            player = app.game.player
            enemy = Creature(
                template.name,
                template.base_health,
                template.base_damage,
                template.base_coins,
                level=max(1, player.level),
            )
            enemy_name = template.name

            def _start_ambush_battle(*args):
                try:
                    battlefield, _ = app.game.create_battle([enemy])
                    if hasattr(app, 'battle_screen'):
                        app.battle_screen.start_battle(battlefield, f"⚔️ Засада! {enemy_name}")
                        app.root.current = 'battle'
                except Exception as e:
                    print(f"[AMBUSH] Battle start error: {e}")

            popup = Popup(
                title='⚠️ ЗАСАДА!',
                content=Label(
                    text=(
                        f'Опасность достигла максимума!\n\n'
                        f'На вас нападает: {enemy_name}!\n\n'
                        f'🔴 Глобальная опасность: '
                        f'{app.game.danger_manager.danger_level:.0f}%'
                    ),
                    text_size=(None, None),
                    halign='center',
                    valign='middle',
                    font_size=dp(18),
                    color=(0.9, 0.3, 0.2, 1),
                ),
                size_hint=(0.7, 0.4),
            )
            popup.open()
            Clock.schedule_once(
                lambda dt: (popup.dismiss(), _start_ambush_battle()),
                1.8,
            )
        except Exception as e:
            print(f"[AMBUSH] Error: {e}")

    def on_locked_location(self, location):
        """Показать требования для разблокировки локации."""
        if not location.unlock_condition:
            condition_text = "Эта локация пока недоступна."
        else:
            condition_text = f"Требования для разблокировки:\n{location.unlock_condition}"

        popup = Popup(
            title=f'🔒 {location.name}',
            content=Label(
                text=condition_text,
                text_size=(None, None),
                halign='center',
                valign='middle',
                font_size=dp(18)
            ),
            size_hint=(0.7, 0.4)
        )
        popup.open()
```

### 4.6. `core/combat/battlefield.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Боевое поле: раунды, атаки игрока и врагов, способности, побег.
"""

import random
from typing import List, Optional, Tuple

from core.combat.damage import (
    ENEMY_VARIANCE,
    apply_critical,
    apply_forced_critical,
    armor_ignore_bonus,
    player_crit_chance,
    resolve_hit,
    roll_raw_damage,
)
from core.combat.loot import BattleResult, LootDrop
from core.creatures import Creature, Player


class Battlefield:
    """Состояние одного боя: игрок, враги, раунд, флаги способностей."""

    def __init__(
        self,
        player: Player,
        enemies: List[Creature],
        surprise_attack: bool = False,
    ):
        """Инициализировать бой."""
        self.player = player
        self.enemies = list(enemies)
        self.round = 0
        self.ability_used_this_battle = False
        self.surprise_attack_ready = bool(surprise_attack)

    def alive_enemies(self) -> List[Creature]:
        """Список живых врагов."""
        return [enemy for enemy in self.enemies if enemy.is_alive]

    def is_over(self) -> bool:
        """True, если игрок мёртв или все враги повержены."""
        return not self.player.is_alive or not self.alive_enemies()

    def _select_target(
        self,
        enemy_index: Optional[int],
    ) -> Tuple[Optional[Creature], str]:
        """
        Выбрать цель атаки по индексу в списке живых врагов.

        Returns:
            (цель, сообщение об ошибке). При успехе ошибка пустая.
        """
        enemies = self.alive_enemies()
        if not enemies:
            return None, "Нет врагов!"

        if enemy_index is None:
            return random.choice(enemies), ""

        if enemy_index < 0 or enemy_index >= len(enemies):
            return None, "Неверная цель!"

        return enemies[enemy_index], ""

    def _apply_passive_abilities(self, damage: int) -> int:
        """Бонус от пассивных способностей оружия."""
        weapon = self.player.weapon
        if not weapon or not getattr(weapon, "ability", None):
            return damage

        ability = weapon.ability
        if not ability or ability.ability_type != "passive":
            return damage

        if hasattr(ability, "damage_per_hit"):
            damage += ability.damage_per_hit

        return damage

    def _get_armor_ignore_ratio(self) -> float:
        """Доля игнорируемой брони (топоры)."""
        weapon = self.player.weapon
        if not weapon or not getattr(weapon, "ability", None):
            return 0.0
        ability = weapon.ability
        return float(getattr(ability, "armor_ignore", 0.0) or 0.0)

    def _build_player_hit(
        self,
        target: Creature,
        damage_multiplier: float = 1.0,
        variance=(-3, 5),
    ) -> Tuple[int, bool, int, bool]:
        """
        Рассчитать удар игрока по цели.

        Returns:
            (фактический урон, был ли крит, проигнорированная броня, внезапный крит).
        """
        damage = roll_raw_damage(
            int(self.player.damage * damage_multiplier),
            variance=variance,
        )
        damage = self._apply_passive_abilities(damage)

        ignore_ratio = self._get_armor_ignore_ratio()
        ignored = armor_ignore_bonus(int(target.defense), ignore_ratio)
        damage += ignored

        surprise_critical = self.surprise_attack_ready
        if surprise_critical:
            damage = apply_forced_critical(damage)
            is_critical = True
            self.surprise_attack_ready = False
        else:
            damage, is_critical = apply_critical(
                damage,
                player_crit_chance(self.player),
            )
        dealt = resolve_hit(damage, target)
        return dealt, is_critical, ignored, surprise_critical

    def player_attack(
        self,
        enemy_index: Optional[int] = None,
    ) -> Tuple[str, bool]:
        """
        Атака игрока по выбранному или случайному врагу.

        Args:
            enemy_index: индекс в списке alive_enemies(); None — случайная цель.

        Returns:
            (сообщение в лог, враг убит).
        """
        target, error = self._select_target(enemy_index)
        if target is None:
            return error, False

        dealt, is_critical, armor_ignored, surprise_critical = self._build_player_hit(target)
        ignore_text = (
            f" (игнорируя {armor_ignored} ед. брони)"
            if armor_ignored > 0
            else ""
        )

        if surprise_critical:
            log = (
                f"Из засады! ⚡ КРИТИЧЕСКИЙ УДАР! ⚡ Вы наносите "
                f"{dealt} урона по {target.name}!{ignore_text}"
            )
        elif is_critical:
            log = (
                f"⚡ КРИТИЧЕСКИЙ УДАР! ⚡ Вы наносите "
                f"{dealt} урона по {target.name}!{ignore_text}"
            )
        else:
            log = f"Вы наносите {dealt} урона по {target.name}.{ignore_text}"

        killed = not target.is_alive
        if killed:
            log += f" 💥 {target.name} повержен!"
            self.player.update_quest_progress(target.name)

        return log, killed

    def use_weapon_ability(self) -> Tuple[bool, List[str]]:
        """Использовать активную способность экипированного оружия."""
        weapon = self.player.weapon
        if not weapon or not getattr(weapon, "ability", None):
            return False, ["Оружие не имеет активной способности."]

        ability = weapon.ability
        if ability.ability_type != "active":
            return False, ["Это пассивная способность, не активная."]

        if self.ability_used_this_battle:
            return False, ["Способность уже использована в этой битве!"]

        enemies = self.alive_enemies()
        if not enemies:
            return False, ["Нет врагов для атаки!"]

        logs: List[str] = []
        weapon_type = getattr(weapon, "weapon_type", "sword")

        if weapon_type == "sword":
            target = random.choice(enemies)
            total_damage = 0
            for hit in range(2):
                dealt, _, _, _ = self._build_player_hit(
                    target,
                    damage_multiplier=1.3,
                    variance=(-1, 3),
                )
                total_damage += dealt
                logs.append(
                    f"⚔️ Удар {hit + 1}! Вы наносите {dealt} урона "
                    f"по {target.name}."
                )
                if not target.is_alive:
                    logs.append(f"💥 {target.name} повержен мечом!")
                    self.player.update_quest_progress(target.name)
                    break
            if target.is_alive:
                logs.append(f"⚡ Всего урона: {total_damage}!")

        elif weapon_type == "bow":
            targets = random.sample(enemies, min(2, len(enemies)))
            for i, target in enumerate(targets):
                dealt, _, _, _ = self._build_player_hit(
                    target,
                    variance=(-2, 2),
                )
                logs.append(
                    f"🏹 Выстрел {i + 1}! Вы наносите {dealt} урона "
                    f"по {target.name}."
                )
                if not target.is_alive:
                    logs.append(f"💥 {target.name} поражен стрелой!")
                    self.player.update_quest_progress(target.name)

        elif weapon_type == "staff":
            for target in list(enemies):
                if not target.is_alive:
                    continue
                dealt, _, _, _ = self._build_player_hit(
                    target,
                    variance=(-3, 2),
                )
                logs.append(
                    f"✨ Магический взрыв наносит {dealt} урона "
                    f"по {target.name}!"
                )
                if not target.is_alive:
                    logs.append(f"💥 {target.name} повержен!")
                    self.player.update_quest_progress(target.name)

        self.ability_used_this_battle = True
        return True, logs

    def companion_turn(self) -> List[str]:
        """Ход спутников: каждый живой бьёт случайного врага."""
        logs: List[str] = []
        for companion in self.player.companions:
            if not companion.is_alive:
                continue
            enemies = self.alive_enemies()
            if not enemies:
                break

            target = random.choice(enemies)
            damage = roll_raw_damage(companion.damage, variance=(-1, 2))
            dealt = resolve_hit(damage, target)
            logs.append(
                f"{companion.name} наносит {dealt} урона по {target.name}."
            )

            if not target.is_alive:
                logs.append(f"💥 {target.name} повержен!")
                self.player.update_quest_progress(target.name)
                # Награда за убийство спутником — монеты игроку
                self.player.coins += target.coins

        return logs

    def enemy_turn(self) -> List[str]:
        """Ход всех живых врагов."""
        logs: List[str] = []
        for enemy in self.alive_enemies():
            possible_targets = [self.player] + [
                companion
                for companion in self.player.companions
                if companion.is_alive
            ]
            if not possible_targets:
                continue

            target = random.choice(possible_targets)
            damage = roll_raw_damage(enemy.damage, variance=ENEMY_VARIANCE)
            damage, is_critical = apply_critical(damage, 0.04)
            dealt = resolve_hit(damage, target)

            if target == self.player:
                if is_critical:
                    logs.append(
                        f"⚡ {enemy.name} наносит "
                        f"КРИТИЧЕСКИЙ УДАР! {dealt} урона вам!"
                    )
                else:
                    logs.append(f"{enemy.name} наносит {dealt} урона вам!")
                if not self.player.is_alive:
                    logs.append("💀 Вы были повержены!")
            else:
                if is_critical:
                    logs.append(
                        f"⚡ {enemy.name} наносит "
                        f"КРИТИЧЕСКИЙ УДАР по {target.name}! "
                        f"{dealt} урона!"
                    )
                else:
                    logs.append(
                        f"{enemy.name} наносит {dealt} урона {target.name}!"
                    )
                if not target.is_alive:
                    logs.append(f"💔 {target.name} выбывает из боя!")

        return logs

    def attempt_escape(self) -> Tuple[bool, List[str]]:
        """
        Попытка побега (30% успех).

        Returns:
            (успех, список сообщений).
        """
        logs: List[str] = []
        if random.random() < 0.3:
            logs.append("Вы успешно сбежали!")
            return True, logs

        logs.append("Враги преследуют вас!")
        for enemy in self.alive_enemies():
            damage = max(1, enemy.damage // 2)
            dealt = self.player.take_damage(damage)
            logs.append(f"{enemy.name} наносит {dealt} урона!")
        return False, logs

    def generate_battle_loot(self) -> BattleResult:
        """Собрать лут, золото и XP с поверженных врагов."""
        loot_items: List[LootDrop] = []
        total_gold = 0
        total_xp = 0

        for enemy in self.enemies:
            if enemy.is_alive:
                continue

            total_gold += enemy.coins
            template = getattr(enemy, "_template", None)
            if template:
                total_xp += template.xp_reward
            else:
                total_xp += enemy.level * 30

            if getattr(enemy, "weapon", None):
                weapon_id = getattr(enemy.weapon, "id", None)
                if weapon_id:
                    loot_items.append(LootDrop(weapon_id, 1))

            if getattr(enemy, "armor", None):
                armor_id = getattr(enemy.armor, "id", None)
                if armor_id:
                    loot_items.append(LootDrop(armor_id, 1))

            if template and template.loot_table:
                player_luck = float(getattr(self.player, "luck", 1.0))
                bonus_chance = 0.15 * player_luck
                if random.random() < bonus_chance:
                    items = [item_id for item_id, _ in template.loot_table]
                    chances = [chance for _, chance in template.loot_table]
                    adj_chances = [max(0.0, c * player_luck) for c in chances]
                    bonus_item = random.choices(
                        items,
                        weights=adj_chances,
                        k=1,
                    )[0]
                    loot_items.append(LootDrop(bonus_item, 1))

        return BattleResult(
            victory=True,
            loot=loot_items,
            gold_earned=total_gold,
            xp_earned=total_xp,
        )
```

### 4.7. `systems/danger_manager.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DangerManager — система «Глобальной Опасности» (Global Danger).

Шкала опасности (0.0–100.0) растёт, пока игрок перемещается по глобальной
карте, и влияет на цены в магазине.  При 100% возможны случайные засады.
Скорость роста зависит от количества живых боссов.
Снижение — через сдачу квестов NPC.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from data.locations import LocationManager


# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------

DANGER_MIN: float = 0.0
DANGER_MAX: float = 100.0
DANGER_INITIAL: float = 30.0

# Базовый интервал (в секундах) между +1% при 4 живых боссах
BASE_TICK_SECONDS: float = 2.0

# Множители интервала в зависимости от живых боссов
# bosses_alive -> multiplier  (итоговый интервал = BASE * multiplier)
BOSS_MULTIPLIERS = {
    4: 1,   # +1% каждые 2 сек
    3: 2,   # +1% каждые 4 сек
    2: 3,   # +1% каждые 6 сек
    1: 4,   # +1% каждые 8 сек
    0: 5,   # +1% каждые 10 сек (эндгейм)
}

# Пороги градаций и соответствующие модификаторы цен
THRESHOLDS: List[Tuple[float, float, str]] = [
    # (нижняя граница, модификатор цен, название)
    (100.0, 2.0, "Апокалипсис"),
    (80.0,  1.5, "Критическая опасность"),
    (50.0,  1.2, "Повышенная опасность"),
    (0.0,   1.0, "Безопасно"),
]

# Снижение опасности за сдачу квеста
QUEST_DANGER_REDUCTION: float = 25.0

# Шанс засады за секунду движения при danger == 100 (10%)
AMBUSH_CHANCE_PER_SECOND: float = 0.10


class DangerManager:
    """Менеджер глобальной опасности."""

    def __init__(self, initial: float = DANGER_INITIAL):
        self._danger_level: float = max(DANGER_MIN, min(DANGER_MAX, initial))
        self._bosses_alive: int = 4
        self._accumulator: float = 0.0

    @property
    def danger_level(self) -> float:
        """Текущий уровень опасности (0.0–100.0)."""
        return self._danger_level

    @danger_level.setter
    def danger_level(self, value: float) -> None:
        self._danger_level = max(DANGER_MIN, min(DANGER_MAX, value))

    @property
    def bosses_alive(self) -> int:
        """Количество живых боссов."""
        return self._bosses_alive

    @property
    def tier_name(self) -> str:
        """Название текущей градации опасности."""
        for threshold, _, name in THRESHOLDS:
            if self._danger_level >= threshold:
                return name
        return "Безопасно"

    def set_bosses_alive(self, count: int) -> None:
        """Установить количество живых боссов (0–4)."""
        self._bosses_alive = max(0, min(4, count))

    def update_bosses_from_location_manager(
        self, location_manager: "LocationManager"
    ) -> None:
        """Определить кол-во живых боссов из LocationManager."""
        defeated = 0
        for boss_id in range(1, 5):
            if location_manager.is_boss_defeated(boss_id):
                defeated += 1
        self._bosses_alive = 4 - defeated

    def get_price_modifier(self) -> float:
        """Множитель цен для магазина."""
        for threshold, modifier, _ in THRESHOLDS:
            if self._danger_level >= threshold:
                return modifier
        return 1.0

    def update(
        self,
        dt: float,
        location_manager: Optional["LocationManager"] = None,
    ) -> Optional[str]:
        """Обновить опасность при движении по глобальной карте."""
        if location_manager is not None:
            self.update_bosses_from_location_manager(location_manager)

        interval = self._get_tick_interval()
        self._accumulator += dt

        while self._accumulator >= interval and self._danger_level < DANGER_MAX:
            self._danger_level = min(DANGER_MAX, self._danger_level + 1.0)
            self._accumulator -= interval

        if self._danger_level >= DANGER_MAX:
            self._accumulator = 0.0

        return self.check_ambush(dt)

    def check_ambush(self, dt: float) -> Optional[str]:
        """Проверить шанс засады."""
        if self._danger_level < DANGER_MAX:
            return None

        base = 1.0 - AMBUSH_CHANCE_PER_SECOND
        chance = 1.0 - base ** dt
        if random.random() < chance:
            return self._pick_random_enemy()
        return None

    def on_quest_completed(self, reduction: float = QUEST_DANGER_REDUCTION) -> float:
        """Вызвать при сдаче квеста NPC."""
        old = self._danger_level
        self._danger_level = max(DANGER_MIN, self._danger_level - reduction)
        return old - self._danger_level

    def reset(self) -> None:
        """Сбросить к начальному состоянию (новая игра)."""
        self._danger_level = DANGER_INITIAL
        self._bosses_alive = 4
        self._accumulator = 0.0

    def to_dict(self) -> dict:
        """Для сохранения."""
        return {
            "danger_level": self._danger_level,
            "bosses_alive": self._bosses_alive,
            "accumulator": self._accumulator,
        }

    def from_dict(self, data: dict) -> None:
        """Восстановить из сохранения."""
        if not data:
            return
        self._danger_level = float(data.get("danger_level", DANGER_INITIAL))
        self._bosses_alive = int(data.get("bosses_alive", 4))
        self._accumulator = float(data.get("accumulator", 0.0))

    def _get_tick_interval(self) -> float:
        """Интервал (сек) между +1% в зависимости от живых боссов."""
        mult = BOSS_MULTIPLIERS.get(self._bosses_alive, BOSS_MULTIPLIERS[0])
        return BASE_TICK_SECONDS * mult

    @staticmethod
    def _pick_random_enemy() -> str:
        """Случайный враг из любого биома для засады."""
        all_enemies = [
            "enemy_forest_wolf", "enemy_forest_raider", "enemy_forest_bandit", "enemy_forest_scout",
            "enemy_swamp_goblin", "enemy_swamp_toad", "enemy_swamp_shamanic",
            "enemy_mines_orc", "enemy_mines_draugr", "enemy_mines_golem", "enemy_mines_skeleton", "enemy_mines_greyling",
            "enemy_mountains_dragon", "enemy_mountains_specter", "enemy_mountains_troll", "enemy_mountains_giant", "enemy_mountains_drake",
        ]
        return random.choice(all_enemies)
```

---

## 5. Ключевые потоки данных (Data Flow)

### 5.1. Запуск игры
```
main.py → RPGApp.build() → ScreenManager с 18 экранами + HUD
      ↓
MainMenuScreen (продолжить/новая игра/загрузить)
      ↓
CharacterCreationScreen → Player(name, background) → GameSession.start_new_game()
      ↓
LocationSelectScreen (глобальная карта)
```

### 5.2. Боевой цикл
```
LocationSelectScreen / LocalLocationScreen → вход в локацию / встреча с токеном
      ↓
GameSession.create_battle(enemies) → (Battlefield, BattleService)
      ↓
BattleScreen.start_battle(battlefield)
      ↓
[Цикл]: игрок нажимает врага → service.player_attack_enemy() → service.run_enemy_phase()
      ↓
Battlefield.is_over() → end_battle() → loot_window
```

### 5.3. Сохранение/Загрузка
```
Сохранение: GameSession.to_save_dict() → save_session() → JSON → saves/*.json
Загрузка:  load_session_into(session, filename) → Player.from_dict() → restore NPC/Danger
```

### 5.4. Глобальная опасность
```
DangerManager.update(dt, location_manager) — вызывается каждый кадр при движении
  → накопление времени → +1% к danger_level по интервалу
  → при danger_level == 100% → шанс засады (check_ambush)
  → цена в магазине: Shop.buy() умножает price на get_price_modifier()
```

---

## 6. Известные технические долги и TODO

1. **`location_select.py` (1680 строк):** Экстремально раздутый экран. Логика отрисовки карты, обработки столкновений, токенов, стелса и перемещения — всё в одном классе. Требуется декомпозиция.
2. **Многослойные try/except pass:** Файлы `location_select.py` и `local_location_base.py` содержат сотни блоков `try/except: pass`, что маскирует реальные ошибки и затрудняет отладку.
3. **BattleScreen vs systems/battle_service.py:** Две параллельные реализации обработки конца боя (лут, разблокировка локаций) — в `ui/screens/battle.py` (end_battle) и в `core/combat/battlefield.py` (generate_battle_loot). Логика частично дублируется.
4. **Реэкспорты:** `core/game.py` = реэкспорт GameSession, `core/creatures.py` = реэкспорт из `core/models/`. Создано для обратной совместимости.
5. **NPC-квесты:** Система `GeneratedQuest` в `systems/npcs.py` и старая `Quest` в `systems/quests.py` сосуществуют, часть функциональности пересекается.
6. **Отсутствие централизованного логирования:** Везде используются `print()` вместо модуля `logging`.