# Исправление системы управления компаньонами

## Проблема
Когда вы экипировали компаньону броню или оружие через UI, его характеристики (защита и урон) не увеличивались, хотя предметы отображались как экипированные.

## Причина
В методе `_equip_item()` и `_unequip_item()` класса `CompanionManagementScreen` в `ui_app.py` предметы присваивались напрямую через присвоение атрибутов:

```python
# ❌ НЕПРАВИЛЬНО:
companion.weapon = item  # Просто присваиваем, не вызываем on_equip()
companion.armor = item   # Просто присваиваем, не вызываем on_equip()
```

Это означало, что методы `on_equip()` и `on_unequip()` предметов не вызывались, которые обновляют характеристики `temp_damage` и `temp_defense`.

## Решение
Используются методы класса `Creature` для правильной экипировки/снятия:

```python
# ✅ ПРАВИЛЬНО:
companion.equip_weapon(item)   # Вызывает on_equip(), обновляет урон
companion.equip_armor(item)    # Вызывает on_equip(), обновляет защиту
companion.unequip_weapon()     # Вызывает on_unequip(), убирает урон
companion.unequip_armor()      # Вызывает on_unequip(), убирает защиту
```

## Файлы, которые были изменены
- `ui/ui_app.py` - методы `_equip_item()` и `_unequip_item()` класса `CompanionManagementScreen`

## Система работает следующим образом:

1. **Класс Item** (`data/items.py`):
   - `Weapon.on_equip()` → добавляет `damage_bonus` в `owner.temp_damage`
   - `Armor.on_equip()` → добавляет `defense` в `owner.temp_defense`

2. **Класс Creature** (`core/creatures.py`):
   - `@property damage` → `base_damage + temp_damage`
   - `@property defense` → `temp_defense`
   - `equip_weapon()` / `equip_armor()` → вызывает `on_equip()` на предмете

3. **Класс Companion** (наследует Creature):
   - Имеет те же методы экипировки
   - Характеристики автоматически обновляются при экипировке

## Тестирование
Созданы два теста для проверки:
1. `test_companion_equip.py` - тест низкоуровневого API
2. `test_companion_equip_ui.py` - тест логики UI

Оба теста успешно проходят, подтверждая что:
- ✅ Урон увеличивается при экипировке оружия
- ✅ Защита увеличивается при экипировке брони
- ✅ Характеристики правильно убираются при снятии
- ✅ Предметы правильно перемещаются в инвентарь/из инвентаря
