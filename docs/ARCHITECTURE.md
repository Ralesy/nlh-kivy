# Архитектура NLH Remake

Краткое описание слоёв после рефакторинга v2.

## Структура каталогов

```
NLH_remake/
├── main.py                 # Точка входа
├── core/
│   ├── models/             # Player, Creature, Inventory, Companion
│   ├── combat/             # Battlefield, урон, лут, спавн врагов
│   ├── session.py          # GameSession (игровая сессия)
│   ├── game.py             # Re-export: Game = GameSession
│   ├── creatures.py        # Фасад / legacy-импорты
│   ├── config.py
│   └── utils.py
├── data/                   # Статические данные (враги, предметы, локации)
├── systems/                # Квесты, NPC, магазин, сохранения, battle re-export
│   └── battle.py           # Re-export из core.combat
├── ui/
│   ├── ui_app.py           # RPGApp: ScreenManager + HUD (~200 строк)
│   ├── screens/            # Экраны Kivy (меню, бой, таверна, …)
│   ├── widgets/            # HUD, навигация, попапы
│   ├── bindings/           # PlayerViewModel — реактивный HUD
│   └── local_location_screen.py  # Карта локации (лес и др.)
├── tests/
└── docs/
```

## Слои

| Слой | Назначение |
|------|------------|
| **data/** | Только данные: враги, предметы, локации |
| **core/models/** | Состояние сущностей и инвентарь |
| **core/combat/** | Боевая логика без UI |
| **core/session.py** | `GameSession`: игрок, прогресс, связка систем |
| **systems/** | Квесты, NPC, магазин, save/load |
| **ui/** | Kivy: экраны читают `app.game` / `app.session` |

## Поток данных

```
Ввод игрока (ui/screens)
        ↓
GameSession (core/session.py)
        ↓
core/combat / systems/*
        ↓
core/models (Player, Creature)
        ↓
data/* (шаблоны)
```

## UI

- **ui_app.py** — регистрирует экраны, `NPCManager`, флаг `return_to_local_location`.
- **PlayerViewModel** (`ui/bindings/`) — обновляет HUD при изменении HP/монет/уровня.
- **local_location_screen** — отдельный экран карты; создаётся один раз в `build()`.

Новый экран: модуль в `ui/screens/`, импорт в `ui/screens/__init__.py`, регистрация в `RPGApp.build()`.

## Обратная совместимость

```python
from core.game import Game, GameSession  # GameSession — основной тип
from systems.battle import Battlefield     # → core.combat
```

## Добавление фичи

1. Данные → `data/`
2. Логика → `core/` или `systems/`
3. Экран/виджет → `ui/screens/` или `ui/widgets/`
4. Тест → `tests/`
