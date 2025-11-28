#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OOP Principles: ООП принципы в проекте.

SOLID ПРИНЦИПЫ:
================

S - Single Responsibility Principle (Принцип единственной ответственности)
─────────────────────────────────────────────────────────────────────────

Каждый класс должен отвечать за одно.

✅ ХОРОШО:
```python
class Creature:
    '''Управление состоянием существа (здоровье, урон, защита)'''
    def take_damage(self, damage): ...
    def heal(self, amount): ...

class Battlefield:
    '''Управление боевой механикой (раунды, ход врагов, проверка победы)'''
    def player_attack(self): ...
    def enemy_attack(self): ...
    def is_over(self): ...

class BattleService:
    '''Управление UI логикой боя (получение статуса, вызов действий)'''
    def get_battle_status(self): ...
    def player_attack_enemy(self): ...
```

❌ ПЛОХО:
```python
class Creature:
    '''Управляет и существом, и UI, и боем, и всем сразу'''
    def render_battle_ui(self): ...  # ❌ UI логика
    def save_to_database(self): ...  # ❌ Persistence
    def process_loot(self): ...  # ❌ Лут логика
```

O - Open/Closed Principle (Принцип открытости/закрытости)
──────────────────────────────────────────────────────────

Классы должны быть открыты для расширения, но закрыты для модификации.

✅ ХОРОШО:
```python
class Ability(ABC):
    '''Абстрактный класс способности'''
    @abstractmethod
    def execute(self): ...

class PassiveAbility(Ability):
    '''Конкретная реализация пассивной способности'''
    def execute(self): ...

class ActiveAbility(Ability):
    '''Конкретная реализация активной способности'''
    def execute(self): ...

# Новую способность добавляем не меняя существующий код
class SpecialAbility(Ability):
    def execute(self): ...
```

❌ ПЛОХО:
```python
def apply_ability(ability_type):
    if ability_type == "passive": ...
    elif ability_type == "active": ...
    elif ability_type == "special": ...  # ❌ Нужно менять функцию для каждой новой способности
```

L - Liskov Substitution Principle (Принцип подстановки Лискова)
──────────────────────────────────────────────────────────────

Объекты подклассов должны корректно подставляться вместо объектов базового класса.

✅ ХОРОШО:
```python
def damage_target(attacker: Creature, target: Creature):
    '''Работает с любым Creature'''
    damage = attacker.damage
    target.take_damage(damage)

player = Player(...)  # Player наследует Creature
enemy = Enemy(...)    # Enemy наследует Creature

damage_target(player, enemy)  # Работает для обоих
damage_target(enemy, player)  # Работает для обоих
```

❌ ПЛОХО:
```python
def damage_target(target):
    '''Требует знать конкретный тип'''
    if isinstance(target, Player):
        target.player_take_damage(...)  # ❌ Разные методы
    elif isinstance(target, Enemy):
        target.enemy_take_damage(...)   # ❌ Разные методы
```

I - Interface Segregation Principle (Принцип разделения интерфейсов)
─────────────────────────────────────────────────────────────────────

Лучше иметь много специфических интерфейсов, чем один универсальный.

✅ ХОРОШО:
```python
class Healable(ABC):
    @abstractmethod
    def heal(self, amount): ...

class Damageable(ABC):
    @abstractmethod
    def take_damage(self, damage): ...

class Player(Creature, Healable, Damageable):
    '''Реализует только нужные интерфейсы'''
    pass

# Предмет может быть Damageable, но не обязательно Healable
class Item(Damageable):
    pass
```

❌ ПЛОХО:
```python
class Entity(ABC):
    '''Слишком много методов, которые не все классы используют'''
    @abstractmethod
    def heal(self): ...
    @abstractmethod
    def take_damage(self): ...
    @abstractmethod
    def render(self): ...
    @abstractmethod
    def save(self): ...
    @abstractmethod
    def load(self): ...

class Item(Entity):
    '''Должен реализовать все, даже ненужные методы'''
    def heal(self): pass  # ❌ Не имеет смысла
    def take_damage(self): pass  # ❌ Может не нужно
```

D - Dependency Inversion Principle (Принцип инверсии зависимостей)
──────────────────────────────────────────────────────────────────

Зависеть от абстракций, а не от конкретных реализаций.

✅ ХОРОШО:
```python
class BattleService:
    def __init__(self, battlefield: Battlefield):
        '''Зависит от интерфейса Battlefield'''
        self.battlefield = battlefield
    
    def get_status(self):
        return self.battlefield.get_status()  # Работает с любым Battlefield

# Можно подставить любую реализацию
class MockBattlefield(Battlefield):
    pass

service = BattleService(MockBattlefield())  # Работает!
```

❌ ПЛОХО:
```python
class BattleService:
    def __init__(self):
        self.battlefield = RealBattlefield()  # ❌ Жестко привязана конкретная реализация
    
    def get_status(self):
        return self.battlefield.get_status()

# Сложно тестировать, нельзя использовать mock объекты
```

ПРАКТИЧЕСКИЕ ПРИМЕРЫ В ПРОЕКТЕ:
================================

Хорошие примеры:
───────────────

1. Creature иерархия:
   class Creature → class Player, Enemy
   - Единая ответственность: управление состоянием существа
   - Открыта для расширения: можно добавить Companion, Boss
   - Подстановка Лискова: все методы работают одинаково

2. Database классы:
   class ItemDatabase, EnemyDatabase, LocationManager
   - Единая ответственность: управление данными одного типа
   - Открыты для расширения: можно добавить WeaponAbilityDatabase

3. Service слой:
   class BattleService, LocationService
   - Единая ответственность: управление логикой одной системы
   - Инверсия зависимостей: зависит от Battlefield, LocationManager

Можно улучшить:
───────────────

1. BattleScreen
   - Содержит UI логику И боевую логику
   - Решение: использовать BattleService для логики

2. LocationSelectScreen
   - Содержит выбор локации И инициализацию боя
   - Решение: использовать LocationService для логики

КАК ДОБАВЛЯТЬ КОД ПРАВИЛЬНО:
=============================

1. Определи ответственность
   - Что должен делать этот класс? (SRP)
   - Можно ли его расширить без изменений? (OCP)

2. Используй абстракции
   - Зависимости передавай в конструктор (DI)
   - Используй интерфейсы/ABC (ISP)

3. Тестируй
   - Если код сложно тестировать - нарушены SOLID принципы
   - Хороший код легко мокировать

ТЕКУЩЕЕ СОСТОЯНИЕ:
===================

✅ Хорошо:
- Creature иерархия правильная
- Database классы чистые
- Battlefield имеет одну ответственность
- Service слой правильно выделен

⚠️  Нужно улучшить:
- BattleScreen смешивает UI и логику (рефакторить постепенно)
- LocationSelectScreen смешивает выбор и инициализацию (использовать LocationService)

⚠️  Перемешанное, но нормально для текущей версии:
- UI содержит некоторую логику обработки результатов
  (это нормально, пока не помешает функциональности)
"""
