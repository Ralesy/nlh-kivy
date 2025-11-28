#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Battle Screen Refactoring Guide: пример как рефакторить BattleScreen.

Этап 1: ТЕКУЩЕЕ СОСТОЯНИЕ (РАБОТАЮЩЕЕ)
======================================

BattleScreen содержит:
✅ Все UI элементы (правильно)
⚠️  Логику боя (смешано с UI)
⚠️  Логику врагов (смешано с UI)
⚠️  Обработку спутников (смешано с UI)

```python
class BattleScreen(Screen):
    def __init__(self, **kwargs):
        # UI элементы
        self.enemies_layout = BoxLayout()
        self.log_label = Label()
        # ...
    
    def start_battle(self, battlefield):
        # Инициализация боя
        self.battlefield = battlefield
        self.update_battle_display()
    
    def update_battle_display(self):
        # Отображение UI на основе battlefield
        # Вся логика по подсчету здоровья, цветов кнопок и т.д.
    
    def attack_enemy(self, enemy_index):
        # Вызов battlefield.player_attack()
        # Обновление UI
        # Вызов enemy_turn()
    
    def enemy_turn(self):
        # Обработка хода враждебных существ
        # Обработка спутников
        # Логика с врагами
```

Этап 2: СОЗДАТЬ СЛОЙ ABSTRACTION
=================================

Создаем BattleService для инкапсуляции логики (DONE):

```python
class BattleService:
    def __init__(self, battlefield):
        self.battlefield = battlefield
    
    def get_battle_status(self):
        """Возвращает текущий статус боя"""
        return {...}
    
    def player_attack_enemy(self):
        """Логика атаки игрока"""
        return log, killed
    
    def use_ability(self):
        """Логика использования способности"""
        return success, logs
    
    def enemy_attack(self):
        """Логика атаки врагов"""
        return log, player_killed
```

Этап 3: ПЕРЕВОДИТЬ UI НА SERVICE СЛОЙ (ПОСТЕПЕННО)
===================================================

Изменяем BattleScreen постепенно:

```python
class BattleScreen(Screen):
    def start_battle(self, battlefield):
        self.battlefield = battlefield
        self.service = BattleService(battlefield)  # ← Создаем сервис
        self.update_battle_display()
    
    def attack_enemy(self, enemy_index):
        if self.is_processing_turn:
            return
        
        self.is_processing_turn = True
        
        # ← Вместо: log, killed = self.battlefield.player_attack()
        # Используем: log, killed = self.service.player_attack_enemy()
        log, killed = self.service.player_attack_enemy()
        
        self.add_log(log)
        self.update_battle_display()
        
        if not self.service.is_battle_over():
            Clock.schedule_once(lambda dt: self.enemy_turn(), 1.0)
        else:
            self.end_battle()
```

Этап 4: ОТДЕЛИТЬ DISPLAY ЛОГИКУ
================================

Создать отдельный класс для отображения:

```python
class BattleDisplay:
    '''Отвечает только за отображение информации о бое'''
    
    def __init__(self, battle_info_label, enemies_layout, log_label):
        self.battle_info = battle_info_label
        self.enemies_layout = enemies_layout
        self.log_label = log_label
    
    def update_battle_info(self, status: dict):
        """Обновить информацию о бое из статуса"""
        p = status
        self.battle_info.text = (
            f"⚔️ Раунд {p['round'] + 1}\\n"
            f"💚 Ваш HP: {p['player_health']}/{p['player_max_health']}"
        )
    
    def update_enemies_display(self, enemies: list):
        """Обновить отображение врагов"""
        self.enemies_layout.clear_widgets()
        for enemy in enemies:
            btn = self._create_enemy_button(enemy)
            self.enemies_layout.add_widget(btn)
    
    def add_log(self, message):
        """Добавить сообщение в лог"""
        self.log_label.text += message + '\\n'
```

Потом в BattleScreen:

```python
class BattleScreen(Screen):
    def update_battle_display(self):
        status = self.service.get_battle_status()
        self.display.update_battle_info(status)
        self.display.update_enemies_display(status['enemies'])
```

ПЛАН ПОСТЕПЕННОГО РЕФАКТОРИНГА:
=================================

Фаза 1 (СЕЙЧАС):
- ✅ BattleService создан
- ✅ LocationService создан
- ✅ Документация создана
- BattleScreen и LocationSelectScreen остаются как есть

Фаза 2 (КОГДА ЗАХОЧЕШЬ):
- Добавить BattleService как опцию в BattleScreen
- Новые фичи добавлять через сервис
- Старый код не трогать

Фаза 3 (ПОЗЖЕ):
- Постепенно переводить методы BattleScreen на сервис
- Создать BattleDisplay для отделения UI от логики
- Тестировать каждый шаг

Фаза 4 (КОГДА БУДЕТ ВРЕМЯ):
- Полный рефакторинг BattleScreen
- Использование только сервис слоя
- Удаление дублированного кода

КАК НЕ СЛОМАТЬ НИЧЕГО:
======================

1. НЕ изменяй существующие методы
   - Только добавляй новые
   - Если нужно изменить - создай новый метод и переходи постепенно

2. Тестируй каждый шаг
   - После каждого изменения запусти игру
   - Проверь что все работает

3. Оставляй комментарии
   - Отмечай какой код старый, какой новый
   - Оставляй TODOs для будущего рефакторинга

4. Используй ветки git
   - Работай в отдельной ветке
   - Можно откатиться если что-то сломается

5. Документируй изменения
   - Добавляй примеры использования
   - Описывай почему сделал именно так

ПРИМЕР КОД МИГРАЦИИ:
====================

Было:
-----
def attack_enemy(self, enemy_index):
    log, killed = self.battlefield.player_attack()
    self.add_log(log)
    self.update_battle_display()

Будет:
------
def attack_enemy(self, enemy_index):
    # Сначала оставляем старый путь, но через сервис
    if hasattr(self, 'service') and self.service:
        log, killed = self.service.player_attack_enemy()
    else:
        log, killed = self.battlefield.player_attack()
    
    self.add_log(log)
    self.update_battle_display()

Потом:
------
def attack_enemy(self, enemy_index):
    # Полностью на сервис
    log, killed = self.service.player_attack_enemy()
    self.add_log(log)
    self.update_battle_display()
"""
