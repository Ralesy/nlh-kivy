#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mini RPG - Главная точка входа

Современная RPG игра на Python с:
- Системой сохранений
- Системой смерти со статистикой
- Боевой системой с врагами и спутниками
- Системой квестов и таверной
- Магазином и казино
- Несколькими локациями с событиями
- Kivy UI для Windows и Android
"""

import sys
from pathlib import Path

# Добавляем корень проекта в путь Python
sys.path.insert(0, str(Path(__file__).parent))

print("Hello world")

# Проверяем, запущен ли с флагом --console для консольного режима
if '--console' in sys.argv:
    from core.game import main
    if __name__ == "__main__":
        main()
else:
    # Запускаем Kivy UI
    from ui.ui_app import RPGApp
    if __name__ == "__main__":
        RPGApp().run()
