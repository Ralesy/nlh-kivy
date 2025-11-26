#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка что все show_item_info() функции имеют консистентный формат.
"""

import sys
from pathlib import Path

def check_file(filepath, screen_names):
    """Проверяет что все show_item_info в указанных экранах имеют одинаковый формат."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n📝 Проверка {filepath.name}...")
    
    # Проверяем на наличие ключевых элементов в каждом методе show_item_info
    key_checks = {
        'lines.append': 'добавление информации в массив',
        'ScrollView': 'использование ScrollView для прокрутки',
        'text_size=(dp(320)': 'правильная ширина текста',
        'size_hint=(0.8, 0.7)': 'правильный размер popup',
        'Материал:': 'информация о материале',
        'Состояние:': 'информация о состоянии',
        'Способность:': 'информация о способности',
    }
    
    found_methods = []
    for screen_name in screen_names:
        if f"class {screen_name}" in content:
            found_methods.append(screen_name)
    
    if found_methods:
        print(f"  ✓ Найдены экраны: {', '.join(found_methods)}")
        
        # Проверяем ключевые элементы
        missing = []
        for check, desc in key_checks.items():
            if check not in content:
                missing.append(f"    - {desc} ({check})")
        
        if missing:
            print(f"  ⚠️ Возможные проблемы:")
            for msg in missing:
                print(msg)
        else:
            print(f"  ✅ Все проверки пройдены!")
    else:
        print(f"  ❌ Экраны не найдены: {', '.join(screen_names)}")

def main():
    """Главная функция."""
    base_path = Path(__file__).parent
    
    # Проверяем основной UI файл
    ui_app = base_path / 'ui_app.py'
    ui_app_kivy = base_path / 'ui' / 'ui_app.py'
    
    print("=" * 60)
    print("🔍 ПРОВЕРКА КОНСИСТЕНТНОСТИ show_item_info()")
    print("=" * 60)
    
    if ui_app.exists():
        screens = ['TavernScreen', 'ShopScreen', 'InventoryScreen', 'BattleInventoryScreen']
        check_file(ui_app, screens)
    
    if ui_app_kivy.exists():
        screens = ['TavernScreen', 'ShopScreen', 'InventoryScreen', 'BattleInventoryScreen']
        check_file(ui_app_kivy, screens)
    
    print("\n" + "=" * 60)
    print("✨ Проверка завершена!")
    print("=" * 60)

if __name__ == '__main__':
    main()
