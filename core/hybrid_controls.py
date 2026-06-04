"""
HybridControlManager - новая система управления, совмещающая клавиатуру и мышь.
"""

from typing import Tuple


class HybridControlManager:
    """
    Управление игроком через:
    1. WASD (клавиатура) - движение
    2. Клики мыши (тач) - движение к цели
    3. Другие клавиши - действия (инвентарь, взаимодействия)
    Все методы работают одновременно без конфликтов.
    """

    def __init__(self):
        # Состояния клавиш для плавного управления
        self.keys = {
            'w': False,
            'a': False,
            's': False,
            'd': False
        }
        # Обработчики действий по клавишам
        self.action_handlers = {
            'e': self.open_inventory,
            'f': self.interact,
            'i': self.toggle_inventory,
            'c': self.open_character_screen
        }
        self.target_position = None

    def open_inventory(self):
        """Открыть инвентарь"""
        print("Открыть инвентарь")

    def interact(self):
        """Взаимодействие с объектом"""
        print("Взаимодействие с объектом")

    def toggle_inventory(self):
        """Переключить инвентарь"""
        print("Переключить инвентарь")

    def open_character_screen(self):
        """Открыть экран персонажа"""
        print("Открыть экран персонажа")

    def handle_keyboard(self, key: str, pressed: bool) -> None:
        """
        Обработка нажатий/отпусканий клавиш.
        pressed: True при нажатии, False при отпускании
        """
        # Обработка клавиш движения
        if key in self.keys:
            self.keys[key] = pressed
        
        # Обработка действий
        elif key in self.action_handlers and pressed:
            self.action_handlers[key]()

    def handle_mouse_click(self, pos: Tuple[float, float]) -> None:
        """
        Обработка клика мыши - устанавливаем целевую позицию.
        pos: (x, y) в координатах игрового мира
        """
        self.target_position = pos

    def get_movement_vector(self, current_pos: Tuple[float, float]) -> Tuple[float, float]:
        """
        Возвращает итоговый вектор движения, объединяющий:
        1. Направление от клавиатуры
        2. Направление к целевой точке от мыши

        Приоритет: клавиатура > мышь
        Возвращает нормализованный вектор [x, y] от -1 до 1.
        """
        # Рассчитываем вектор клавиатуры
        keyboard_vector = [0, 0]
        if self.keys['d']:
            keyboard_vector[0] += 1
        if self.keys['a']:
            keyboard_vector[0] -= 1
        if self.keys['w']:
            keyboard_vector[1] += 1
        if self.keys['s']:
            keyboard_vector[1] -= 1

        # Нормализуем вектор клавиатуры
        if any(keyboard_vector):
            # Вычисляем длину вектора
            length = (keyboard_vector[0]**2 + keyboard_vector[1]**2)**0.5
            # Возвращаем нормализованный вектор
            x_component = keyboard_vector[0] / length
            y_component = keyboard_vector[1] / length
            return [x_component, y_component]

        # Если нет клавиатурного ввода - обрабатываем мышь
        if self.target_position:
            # Вычисляем разницу координат
            dx = self.target_position[0] - current_pos[0]
            dy = self.target_position[1] - current_pos[1]
            
            # Вычисляем квадрат расстояния
            sq_distance = dx**2 + dy**2
            
            # Если расстояние больше мертвой зоны
            if sq_distance > 25:  # 5^2 = 25
                # Вычисляем фактическое расстояние
                distance = sq_distance**0.5
                # Возвращаем нормализованный вектор
                x_component = dx / distance
                y_component = dy / distance
                return [x_component, y_component]
            else:
                self.target_position = None  # Достигли цели

        # Нет активного управления
        return [0, 0]