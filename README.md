# 🎮 NLH Remake - Mini RPG

> Современная RPG игра на Python с полноценной боевой системой, системой квестов, прогрессией и мультиплатформенным Kivy UI.

[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Kivy 2.3.1](https://img.shields.io/badge/Kivy-2.3.1-green.svg)](https://kivy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📚 Оглавление

- [Особенности](#особенности)
- [Архитектура](#архитектура)
- [Быстрый старт](#быстрый-старт)
- [Геймплей](#геймплей)
- [Разработка](#разработка)
- [Документация](#документация)
- [Service Layer](#service-layer)

## ✨ Особенности

### Игровые системы
- 🎯 **Боевая система** - Пошаговый бой с врагами и боссами
- 📍 **Система прогрессии** - 5 локаций с постепенным увеличением сложности
- 👹 **Враги и боссы** - 40+ типов врагов и 4 уникальных босса
- 💎 **Система предметов** - 50+ предметов (оружие, броня, зелья)
- 🎲 **Случайные события** - События в локациях
- 💾 **Сохранения** - Полная система сохранения/загрузки
- 🛍️ **Магазин** - Покупка и продажа предметов
- 🎰 **Казино** - Азартные игры
- 📜 **Квесты** - Система квестов и NPC диалоги
- 🤝 **Спутники** - Боевые спутники

### Архитектура
- ✅ Модульная структура (легко расширять)
- ✅ Type hints для всего кода
- ✅ 25/25 тестов проходят ✓
- ✅ Разделение логики и UI
- ✅ Кроссплатформенная поддержка
- ✅ **NEW:** Service Layer для чистой архитектуры (v1.1)

## 🏗️ Архитектура

Логика отделена от UI: `GameSession` в `core/session.py`, бой в `core/combat/`, экраны в `ui/screens/`, HUD через `PlayerViewModel` в `ui/bindings/`. Подробнее — [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```
NLH_remake/
├── main.py
├── core/
│   ├── models/          # Player, Creature, Inventory
│   ├── combat/          # Battlefield, лут, спавн
│   ├── session.py       # GameSession
│   └── game.py          # re-export Game
├── data/
├── systems/             # квесты, NPC, save; battle.py → core.combat
├── ui/
│   ├── ui_app.py
│   ├── screens/
│   ├── widgets/
│   └── bindings/
├── tests/
└── docs/
```

## 🚀 Быстрый старт

### Требования
- Python 3.8+
- pip

### Установка

```bash
# 1. Клонировать репозиторий
git clone <repository>
cd NLH_remake

# 2. Установить зависимости
pip install -r docs/requirements.txt

# 3. Запустить игру
python main.py
```

### Режимы запуска

```bash
# Графический режим (основной)
python main.py

# Консольный режим
python main.py --console
```

## 🎮 Геймплей

### Локации

| Локация | Враги | Босс | Уровень |
|---------|-------|------|---------|
| 🌲 Лес | Слизни, Гоблины | Король гоблинов | 1-5 |
| 🟤 Болото | Ядовитые враги | Болотный лорд | 5-10 |
| ⛏️ Шахты | Кристаллы, Тролли | Король троллей | 10-15 |
| ⛰️ Горы | Драконы, Гиганты | Король гигантов | 15-20 |
| 🕷️ Пещера | Все враги | 4 босса | 20-25 |

### Боевая система

```
Ход боя:
1. Игрок атакует → урон = Урон + (-3 до +5) - Защита врага
2. Враг атакует → урон = Урон врага - Защита игрока
3. Повтор до победы или поражения

Особенности:
- Критические удары (x1.5 урона)
- Игнорирование брони
- Исцеление зельями
- Способности оружия
```

## 📖 Примеры

### Добавить нового врага

```python
# В data/enemies.py
enemies = [
    {
        'id': 'new_enemy',
        'name': 'Новый враг',
        'base_health': 100,
        'base_damage': 15,
        'base_coins': 50,
        'xp_reward': 150,
        'location': 'forest'
    }
]
```

### Запустить тестирование

```bash
# Все тесты
python -m pytest tests/ -v

# Конкретный тест
python -m pytest tests/test_full_playthrough.py -v
```

## 🧪 Тестирование

- ✅ `test_full_playthrough.py` - Полное прохождение
- ✅ `test_ancient_cave.py` - Тестирование пещеры
- ✅ `test_ancient_cave_bosses.py` - Боссы
- ✅ `quick_shop_test.py` - Магазин

**Все 25 тестов проходят! ✓**

## 📊 Статистика

- **~7100** строк кода
- **25+** классов
- **200+** функций
- **50+** предметов
- **40+** врагов
- **4** босса
- **25/25** тестов ✅

## 🔧 Разработка

### Кодовый стиль
- PEP 8
- Type hints
- Docstrings

### Добавление нового

1. Создать файл в соответствующей папке
2. Написать тесты
3. Обновить документацию

## 📖 Документация

Три файла в папке `docs/`:

1. **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Как устроен проект ⭐
   - Структура папок и модулей (Data, Core, Systems, UI)
   - Ключевые классы (Creature, Player, Battlefield, Item)
   - Как добавить новую фичу

2. **[GAME_MECHANICS.md](docs/GAME_MECHANICS.md)** - Все механики игры ⭐
   - Боевая система (урон, критические удары, способности)
   - Враги и боссы по локациям
   - Система предметов, опыта, локаций
   - Спутники, магазин, квесты

3. **[ADDING_CONTENT.md](docs/ADDING_CONTENT.md)** - Гайд по добавлению контента ⭐
   - Как добавить врага (step by step)
   - Как добавить предмет и оружие
   - Как добавить локацию
   - Как добавить квест, спутника, буфф
   - Примеры кода для каждого

---

**✅ Status:** Production Ready  
**📌 Version:** 1.1 (with Service Layer)
**📅 Last Updated:** November 2025  
**🐍 Python:** 3.13+  
**🎨 UI:** Kivy 2.3.1

**Начни отсюда:**
- 📚 [docs/INDEX.md](docs/INDEX.md) - Полный указатель документации
- ⚡ [docs/QUICKSTART.txt](docs/QUICKSTART.txt) - Быстрый старт для разработчиков

**Архитектура и дизайн:**
- 🏗️ [docs/ARCHITECTURE_CURRENT.md](docs/ARCHITECTURE_CURRENT.md) - Текущая архитектура
- 🎯 [docs/OOP_PRINCIPLES.md](docs/OOP_PRINCIPLES.md) - ООП принципы в проекте
- 🔧 [docs/REFACTORING_GUIDE.md](docs/REFACTORING_GUIDE.md) - Как рефакторить безопасно

**Новые сервисы (v1.1):**
- 💡 [docs/SERVICE_LAYER_GUIDE.md](docs/SERVICE_LAYER_GUIDE.md) - Как использовать Service Layer
- 📝 [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) - Практические примеры кода
- 📋 [docs/REFACTORING_SUMMARY.md](docs/REFACTORING_SUMMARY.md) - Что было сделано в v1.1

**Справки:**
- ⚔️ [docs/WEAPON_ABILITIES.md](docs/WEAPON_ABILITIES.md) - Система способностей
- 📚 [docs/API_REFERENCE.md](docs/API_REFERENCE.md) - API справка
- 📝 [docs/CHANGELOG.md](docs/CHANGELOG.md) - История изменений

## 🔧 Service Layer (NEW в v1.1)

### BattleService
Управляет логикой боя, инкапсулирует Battlefield:

```python
from systems.battle_service import BattleService

service = BattleService(battlefield)
status = service.get_battle_status()
log, killed = service.player_attack_enemy()
```

### LocationService  
Управляет логикой локаций, генерацией врагов:

```python
from systems.location_service import LocationService

service = LocationService(location_manager, player)
success, battlefield, error = service.start_battle_for_location('forest')
```

**Подробнее:** [docs/SERVICE_LAYER_GUIDE.md](docs/SERVICE_LAYER_GUIDE.md)
