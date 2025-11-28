# ➕ Гайд по добавлению нового контента

## Добавление нового врага

### Шаг 1: Определить врага в `data/enemies.py`

```python
# В списке EnemyDatabase.ENEMY_TEMPLATES
{
    'id': 'new_goblin',
    'name': 'Усиленный гоблин',
    'base_health': 50,
    'base_damage': 8,
    'base_coins': 35,
    'base_xp': 75,
    'location': 'forest',  # Локация где спауните
    'is_boss': False,
    'loot_table': {  # Рарные дропы
        'item_id': 25  # 25% шанс
    }
}
```

### Шаг 2: Добавить лут (если нужен)
```python
# В том же определении врага
'loot_table': {
    'w_iron_sword': 10,  # 10% шанс
    'p_small': 20,       # 20% шанс
}
```

### Шаг 3: Протестировать
```bash
python -c "
from data.enemies import EnemyDatabase
from systems.battle import EnemyGenerator
from core.creatures import Player

EnemyDatabase.initialize()
player = Player('Test', 'squire')
enemies = EnemyGenerator.generate_for_location('forest', player.level)
print(f'Сгенерировано {len(enemies)} врагов')
for e in enemies:
    print(f'  - {e.name}: {e.health}HP, {e.damage} урона')
"
```

## Добавление нового предмета

### Шаг 1: Определить предмет в `data/items.py`

```python
# В списке ITEMS
{
    'id': 'new_sword',
    'name': 'Новый меч',
    'type': 'weapon',
    'damage': 20,
    'rarity': 'rare',
    'price': 500,
    'description': 'Описание меча'
}
```

### Шаг 2: Если оружие - добавить способность

```python
# В data/weapon_abilities.py
{
    'id': 'new_ability',
    'name': 'Новая способность',
    'weapon_type': 'sword',  # или 'axe', 'dagger'
    'ability_type': 'active',  # или 'passive'
    'damage_multiplier': 1.5,
    'description': 'Описание'
}
```

### Шаг 3: Привязать способность к оружию

В `data/items.py`:
```python
{
    'id': 'new_sword',
    'name': 'Новый меч',
    'type': 'weapon',
    'damage': 20,
    'ability_id': 'new_ability',  # ← Добавить это
    'price': 500,
}
```

### Шаг 4: Добавить в магазин (опционально)

В `core/game.py`:
```python
base_stock = {
    'new_sword': 2,  # 2 штуки в магазине
    # ... остальное
}
```

## Добавление новой локации

### Шаг 1: Определить локацию в `data/locations.py`

```python
# В LocationManager.LOCATIONS
{
    'id': 'new_location',
    'name': 'Новая локация',
    'description': 'Описание локации',
    'difficulty': 'Средне',
    'unlock_condition': 'Требуется уровень 10',
    'is_boss': False
}
```

### Шаг 2: Добавить врагов для локации

В `data/enemies.py` добавить врагов с `'location': 'new_location'`

### Шаг 3: Если босс - добавить босса

```python
# В data/enemies.py
{
    'id': 'boss_new_location',
    'name': 'Босс новой локации',
    'base_health': 200,
    'base_damage': 30,
    'base_coins': 500,
    'base_xp': 1000,
    'location': 'new_location',
    'is_boss': True,
    'loot_table': {
        'legendary_item': 100  # Гарантирован
    }
}
```

### Шаг 4: Обновить UI

В `ui/ui_app.py` найти где отображаются локации и обновить карту.

### Шаг 5: Протестировать

```bash
python -c "
from data.locations import LocationManager
lm = LocationManager()
loc = lm.get_location('new_location')
print(f'Локация: {loc.name}')
print(f'Описание: {loc.description}')
"
```

## Добавление нового оружия с способностью

### Полный пример

```python
# 1. В data/weapon_abilities.py
{
    'id': 'dragon_slash',
    'name': 'Удар дракона',
    'weapon_type': 'sword',
    'ability_type': 'active',
    'damage_multiplier': 2.0,
    'hits': 1,
    'damage_per_hit': 0,
    'crit_multiplier': None,
    'armor_ignore': None
}

# 2. В data/items.py
{
    'id': 'dragon_sword',
    'name': 'Меч дракона',
    'type': 'weapon',
    'weapon_type': 'sword',
    'damage': 35,
    'ability_id': 'dragon_slash',
    'rarity': 'legendary',
    'price': 2000,
    'description': 'Легендарный меч с способностью удара дракона'
}

# 3. В core/game.py добавить в магазин
base_stock = {
    'dragon_sword': 1,
}

# 4. Протестировать
from data.items import ItemDatabase
ItemDatabase.initialize()
item = ItemDatabase.get('dragon_sword')
print(f'{item.name}: {item.damage} урона')
print(f'Способность: {item.ability.name}')
```

## Добавление квеста

### Шаг 1: Создать квест в `systems/quests.py`

```python
class Quest:
    def __init__(self, quest_id, name, description, target):
        self.id = quest_id
        self.name = name
        self.description = description
        self.target = target
        self.completed = False
```

### Шаг 2: Добавить в Tavern

```python
# В systems/quests.py
QUESTS = [
    {
        'id': 'kill_goblins',
        'name': 'Охота на гоблинов',
        'description': 'Убей 5 гоблинов',
        'target': 'kill',
        'target_count': 5,
        'target_enemy': 'goblin',
        'reward_gold': 100,
        'reward_xp': 200
    }
]
```

## Добавление спутника

### Шаг 1: Определить спутника

```python
# В core/creatures.py или отдельном файле
class Companion(Creature):
    def __init__(self, name, health, damage, level=1):
        super().__init__(name, health, damage, 0, level)
        self.ability = None
```

### Шаг 2: Добавить в игру

```python
# В core/game.py
companion = Companion('Эльф-помощник', 50, 5, level=1)
player.add_companion(companion)
```

## Добавление баффа/дебаффа

### Шаг 1: Создать класс баффа

```python
# В systems/battle.py или новом файле
class Buff:
    def __init__(self, name, duration, effect_type, value):
        self.name = name
        self.duration = duration
        self.effect_type = effect_type  # 'damage', 'defense', 'heal'
        self.value = value
```

### Шаг 2: Применять в бою

```python
# В Battlefield.player_attack()
if target.has_buff('poison'):
    damage *= 1.2  # 20% больше урона отравленному
```

## Добавление события в локации

### Шаг 1: Создать событие

```python
# В systems/ новый файл events.py
class LocationEvent:
    def __init__(self, name, description, chance):
        self.name = name
        self.description = description
        self.chance = chance  # 0.0-1.0
    
    def trigger(self, player):
        pass  # Логика события
```

### Шаг 2: Применять при входе в локацию

```python
# В LocationSelectScreen.on_select_location()
if random.random() < event.chance:
    event.trigger(player)
    self.show_popup(event.description)
```

## Тестирование нового контента

### Проверить врага
```bash
python -c "
from data.enemies import EnemyDatabase
EnemyDatabase.initialize()
enemy = EnemyDatabase.get_by_id('new_goblin')
print(f'{enemy.name}: {enemy.base_health}HP')
"
```

### Проверить предмет
```bash
python -c "
from data.items import ItemDatabase
ItemDatabase.initialize()
item = ItemDatabase.get('new_sword')
print(f'{item.name}: {item.damage} урона')
"
```

### Проверить локацию
```bash
python -c "
from data.locations import LocationManager
from systems.battle import EnemyGenerator
lm = LocationManager()
loc = lm.get_location('new_location')
enemies = EnemyGenerator.generate_for_location('new_location', 5)
print(f'Врагов в {loc.name}: {len(enemies)}')
"
```

### Полный тест в игре
1. Запустить игру: `python main.py`
2. Создать персонажа
3. Пройти бой в локации с новым контентом
4. Проверить что врагов правильно генерируются
5. Проверить что новый предмет дропится
6. Проверить что можно использовать новое оружие

## Best Practices

1. **Всегда тестируй** перед коммитом
2. **Используй существующие классы** не создавай новые без необходимости
3. **Следуй именам** типа `new_goblin`, не `newenemyfromorc`
4. **Добавь описания** для всех новых механик
5. **Обнови документацию** если добавляешь новую систему
6. **Проверь баланс** - враги не должны быть слишком сильными
7. **Тестируй разные уровни** - враги должны работать на разных уровнях

## Полезные команды

```bash
# Запустить игру
python main.py

# Запустить тесты
python -m pytest tests/ -v

# Запустить конкретный тест
python -m pytest tests/test_battle.py -v

# Проверить импорты
python -c "from systems.battle import *; print('OK')"

# Очистить кэш
rm -r __pycache__ .pytest_cache
```
