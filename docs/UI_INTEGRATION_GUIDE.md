# UI Integration Guide - Kivy + New Systems

## Overview
Все новые системы (LocationManager, NPCManager, EnemyDatabase) интегрированы в Kivy UI приложение.

## New Screens

### 1. LocationSelectScreen
**Назначение:** Экран выбора локаций для боя

**Функции:**
- Показывает все 5 локаций с информацией о замках/разблокировках
- Отображает условия разблокировки локаций
- Показывает сложность каждой локации
- Позволяет выбрать локацию и начать бой

**Вызов:** `GameScreen.on_locations()` → кнопка "🗺️ Локации"

**Связанные системы:**
- `LocationManager` - управление локациями
- `EnemyGenerator.generate_for_location()` - генерация врагов для локации

---

### 2. NPCDialogueScreen
**Назначение:** Диалог с NPC и предложение квестов

**Функции:**
- Показывает диалог NPC
- Генерирует и предлагает новый квест
- Позволяет принять квест или отказать
- Показывает информацию о награде

**Вызов:** `TavernScreen.talk_to_npc(npc)` → вкладка "🧙 NPC"

**Связанные системы:**
- `NPCManager` - управление NPC
- `GeneratedQuest` - система квестов

---

### 3. LootWindowScreen
**Назначение:** Окно добычи после победы в бою

**Функции:**
- Показывает полученные монеты и опыт
- Список предметов добычи с материалом и условием
- Автоматически добавляет добычу в инвентарь
- Кнопка для продолжения игры

**Вызов:** Автоматически после окончания боя (победа)

**Связанные системы:**
- `BattleResult` - результат боя
- `LootDrop` - информация о добытом предмете

---

## Updated Screens

### GameScreen Changes
- Добавлена кнопка "🗺️ Локации" для выбора локаций
- Метод `enter_location(loc_id)` обновлен для:
  - Использования `LocationManager` вместо старой системы
  - Проверки замков локаций
  - Генерации врагов через `EnemyGenerator.generate_for_location()`

### BattleScreen Changes
- Метод `end_battle()` обновлен для:
  - Создания `BattleResult` с добычей
  - Вызова `LootWindowScreen` для отображения добычи
  - Корректного подсчета лута от врагов

### TavernScreen Changes
- Добавлена вкладка "🧙 NPC" с выбором NPC
- Метод `show_npcs()` показывает всех NPC для диалога
- Метод `show_quests()` показывает активные квесты
- Метод `talk_to_npc(npc)` открывает NPCDialogueScreen

---

## Flow Diagrams

### Location Selection → Battle → Loot
```
GameScreen
  ↓ (кнопка "🗺️ Локации")
LocationSelectScreen (выбор локации)
  ↓ (выбор локации)
BattleScreen (бой)
  ↓ (победа)
LootWindowScreen (показать добычу)
  ↓ (продолжить)
GameScreen
```

### NPC Dialogue → Quest
```
GameScreen
  ↓ (кнопка "🏰 Таверна")
TavernScreen
  ↓ (вкладка "🧙 NPC")
NPCDialogueScreen (выбор NPC)
  ↓ (разговор и предложение квеста)
TavernScreen
  ↓ (вкладка "📜 Квесты")
Показать активные квесты
```

---

## Integration Points

### New Imports in ui_app.py
```python
from locations import LocationManager
from npcs import NPCManager
from enemies import EnemyDatabase
from battle import BattleResult, LootDrop
```

### New Screens in RPGApp.build()
```python
location_select_screen = LocationSelectScreen(
    name='location_select'
)
npc_dialogue_screen = NPCDialogueScreen(
    name='npc_dialogue'
)
loot_window_screen = LootWindowScreen(name='loot_window')
```

---

## Testing Checklist

- [ ] Запуск UI приложения без ошибок
- [ ] Создание персонажа с начальными ресурсами
- [ ] Нажатие кнопки "🗺️ Локации"
- [ ] Проверка замков локаций
- [ ] Вход в локацию (например, Лес)
- [ ] Генерация врагов из локации
- [ ] Победа в бою
- [ ] Отображение экрана добычи
- [ ] Добавление добычи в инвентарь
- [ ] Возврат в главное меню игры
- [ ] Открытие Таверны
- [ ] Вкладка "🧙 NPC" - выбор NPC
- [ ] Открытие диалога с NPC
- [ ] Принятие квеста
- [ ] Проверка квеста в вкладке "📜 Квесты"

---

## Known Limitations

1. **Быстрое меню боя** - могут быть задержки при большом количестве врагов
2. **Сохранение игры** - не сохраняет активные квесты (нужно обновить save_system.py)
3. **Масштабирование UI** - оптимизировано для разрешения 1280x720

---

## Future Improvements

1. Добавить анимацию боя
2. Сохранение и загрузка активных квестов
3. Система товарищества (спутники)
4. Достижения и статистика
5. Поддержка мобильных устройств

