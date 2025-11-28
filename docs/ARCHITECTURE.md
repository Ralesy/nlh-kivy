# 🏗️ Архитектура проекта NLH Remake

## Общая структура

```
NLH_remake/
├── main.py              # Точка входа приложения
├── core/                # Ядро игры (логика персонажа, игры)
│   ├── game.py         # Главный класс Game
│   ├── creatures.py    # Creature, Player, Companion
│   ├── config.py       # Конфигурация и константы
│   └── utils.py        # Утилиты
├── data/               # Игровые данные (враги, предметы, локации)
│   ├── enemies.py      # Определение врагов
│   ├── items.py        # Определение предметов
│   ├── locations.py    # Определение локаций
│   └── weapon_abilities.py  # Способности оружия
├── systems/            # Игровые системы (боевая, квесты, магазин)
│   ├── battle.py       # Боевая система (Battlefield, EnemyGenerator)
│   ├── battle_service.py   # Service слой для боя (опционально)
│   ├── location_service.py # Service слой для локаций (опционально)
│   ├── quests.py       # Система квестов
│   ├── npcs.py         # Управление NPC
│   ├── shop_casino.py  # Магазин и казино
│   ├── save_system.py  # Сохранение и загрузка
│   └── active_quests.py # Активные квесты
├── ui/                 # Пользовательский интерфейс (Kivy)
│   └── ui_app.py       # 15+ экранов игры
├── tests/              # Тесты (25+ тестов)
├── docs/               # Документация
└── assets/             # Графика и звуки
```

## Слои архитектуры

### 1️⃣ Data Layer (`data/`)
Чистые данные без логики:
- **enemies.py** - Определение врагов и их характеристик
- **items.py** - Определение предметов (оружие, броня, зелья)
- **locations.py** - Определение локаций и их требований
- **weapon_abilities.py** - Способности оружия

### 2️⃣ Core Layer (`core/`)
Основная логика игры:
- **creatures.py** - Классы Creature, Player, Companion
- **game.py** - Главный контроллер Game
- **config.py** - Константы и конфигурация
- **utils.py** - Вспомогательные функции

### 3️⃣ Systems Layer (`systems/`)
Игровые системы:
- **battle.py** - Боевая механика (раунды, атаки, урон)
- **quests.py** - Система квестов
- **npcs.py** - NPC и диалоги
- **shop_casino.py** - Торговля и азартные игры
- **save_system.py** - Сохранение/загрузка игры

### 4️⃣ UI Layer (`ui/`)
Интерфейс на Kivy:
- **ui_app.py** - Все экраны (карта, боевой экран, инвентарь и т.д.)

## Поток данных

```
Player Input (UI)
        ↓
  BattleScreen (display)
        ↓
  Battlefield (logic)
        ↓
  Creature (state)
        ↓
  ItemDatabase (data)
```

## Ключевые классы

### Creature
```python
class Creature:
    name: str
    health: int
    max_health: int
    damage: int
    defense: int
    level: int
```

### Player (наследник Creature)
```python
class Player(Creature):
    inventory: Inventory
    weapon: Weapon
    armor: Armor
    companions: List[Companion]
    coins: int
    xp: int
```

### Battlefield
```python
class Battlefield:
    player: Player
    enemies: List[Creature]
    round: int
    
    def player_attack() -> Tuple[str, bool]
    def enemy_attack() -> List[str]
    def is_over() -> bool
```

### Item & Weapon
```python
class Item:
    id: str
    name: str
    description: str

class Weapon(Item):
    damage: int
    ability: Optional[Ability]

class Armor(Item):
    defense: int
```

## Разделение ответственности

| Слой | Отвечает за | Примеры |
|------|------------|---------|
| **Data** | Хранение данных | Враги, предметы, локации |
| **Core** | Состояние игры | Player, Creature, Game |
| **Systems** | Игровая логика | Боевая система, квесты |
| **UI** | Отображение | Экраны, кнопки, текст |

## Service Layer (опционально)

Если нужна лучшая абстракция:

```python
# systems/battle_service.py
class BattleService:
    def get_battle_status() -> dict
    def player_attack_enemy() -> Tuple[str, bool]
    def use_ability() -> Tuple[bool, List[str]]
    def enemy_attack() -> Tuple[str, bool]
```

## Как добавить новую фичу

1. **Определить данные** (`data/`)
2. **Добавить логику** (`systems/` или `core/`)
3. **Обновить UI** (`ui/ui_app.py`)
4. **Добавить тесты** (`tests/`)

Пример: Добавить новую локацию
- Добавить в `data/locations.py`
- Создать врагов в `data/enemies.py`
- Обновить UI карты
- Протестировать

## Текущие интеграции

- ✅ Боевая система полностью интегрирована
- ✅ Инвентарь работает с сохранениями
- ✅ Квесты привязаны к NPC
- ✅ Магазин обновляется при разблокировке локаций
- ✅ Service слой готов к использованию
