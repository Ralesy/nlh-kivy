#!/usr/bin/env python3
"""Тест сохранения и загрузки распределённых навыков."""

from core.creatures import Player

# Создаём игрока
player = Player("TestHero", "noble")

print("=== ИСХОДНОЕ СОСТОЯНИЕ ===")
print(f"Имя: {player.name}")
print(f"Фон: {player.background}")
print(f"Уровень: {player.level}")
print(f"Очки навыков: {player.skill_points_available}")
print(f"Распределены: {player.skill_points_allocated}")
print(f"Удача: {player.luck}")
print(f"Сила продажи: {player.selling_multiplier}")

# Распределяем навыки
print("\n=== РАСПРЕДЕЛЯЕМ НАВЫКИ ===")
player.allocate_skill_point("luck")
player.allocate_skill_point("luck")
player.allocate_skill_point("trade")
player.allocate_skill_point("strength")

print(f"После распределения:")
print(f"Очки навыков: {player.skill_points_available}")
print(f"Распределены: {player.skill_points_allocated}")
print(f"Удача: {player.luck}")
print(f"Сила продажи: {player.selling_multiplier}")
print(f"Урон: {player.damage}")

# Сохраняем
print("\n=== СОХРАНЯЕМ ===")
saved_data = player.to_dict()
print(f"Сохранено: skill_points_allocated = {saved_data.get('skill_points_allocated')}")
print(f"Сохранено: skill_points_available = {saved_data.get('skill_points_available')}")

# Загружаем
print("\n=== ЗАГРУЖАЕМ ===")
loaded_player = Player.from_dict(saved_data)
print(f"Загруженное имя: {loaded_player.name}")
print(f"Загруженный фон: {loaded_player.background}")
print(f"Очки навыков: {loaded_player.skill_points_available}")
print(f"Распределены: {loaded_player.skill_points_allocated}")
print(f"Удача: {loaded_player.luck}")
print(f"Сила продажи: {loaded_player.selling_multiplier}")
print(f"Урон: {loaded_player.damage}")

# Проверка
print("\n=== ПРОВЕРКА ===")
if loaded_player.luck == player.luck:
    print("[Да] Удача сохранена и загружена правильно!")
else:
    print(f"[Нет] Ошибка удачи: ожидали {player.luck}, получили {loaded_player.luck}")

if loaded_player.selling_multiplier == player.selling_multiplier:
    print("[Да] Сила продажи сохранена и загружена правильно!")
else:
    print(f"[Нет] Ошибка продажи: ожидали {player.selling_multiplier}, получили {loaded_player.selling_multiplier}")

if loaded_player.damage == player.damage:
    print("[Да] Урон сохранён и загружен правильно!")
else:
    print(f"[Нет] Ошибка урона: ожидали {player.damage}, получили {loaded_player.damage}")

if loaded_player.skill_points_allocated == player.skill_points_allocated:
    print("[Да] Распределение навыков сохранено и загружено правильно!")
else:
    print(f"[Нет] Ошибка навыков: ожидали {player.skill_points_allocated}, получили {loaded_player.skill_points_allocated}")
