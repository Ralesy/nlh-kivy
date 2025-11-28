from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle


class LootWindow(BoxLayout):
    """
    Окно выбора лута в стиле Mount & Blade:
    - Левая колонка: лут с кнопками "Взять"
    - Правая колонка: инвентарь игрока
    - Снизу кнопка "Готово"
    """
    def __init__(self, loot_items, player_inventory, on_done, gold: int = 0, xp: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(10)
        self.padding = dp(10)
        self.loot_items = loot_items.copy() if loot_items else []
        self.player_inventory = player_inventory
        self.on_done = on_done
        self.gold = gold
        self.xp = xp
        self.selected = []

        # Заголовок
        title = Label(
            text='⚔️ ВЫБОР ЛУТА',
            font_size=dp(24),
            size_hint_y=None,
            height=dp(40)
        )
        self.add_widget(title)

        # Статистика награды (золото и опыт)
        stats = Label(
            text=f"💰 +{self.gold}   ✨ +{self.xp} XP",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(28)
        )
        self.add_widget(stats)

        # Две колонки (лут слева, инвентарь справа)
        columns_layout = BoxLayout(
            orientation='horizontal',
            spacing=dp(15),
            size_hint_y=1
        )

        # ===== ЛЕВАЯ КОЛОНКА: ЛУТ =====
        loot_container = BoxLayout(
            orientation='vertical',
            spacing=dp(6),
            size_hint_x=0.5
        )
        loot_title = Label(
            text='📦 ЛУТ',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(35)
        )
        loot_container.add_widget(loot_title)

        self.loot_layout = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None,
            padding=dp(5)
        )
        self.loot_layout.bind(
            minimum_height=self.loot_layout.setter('height')
        )

        for item in self.loot_items:
            row = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(40),
                spacing=dp(5)
            )
            row.add_widget(Label(
                text=f"{item.display()}",
                font_size=dp(14),
                size_hint_x=0.7
            ))
            btn = Button(
                text='→',
                size_hint_x=0.3,
                size_hint_y=1
            )
            btn.bind(on_press=lambda inst, i=item: self.take_item(i))
            row.add_widget(btn)
            self.loot_layout.add_widget(row)

        loot_scroll = ScrollView(size_hint_y=1)
        loot_scroll.add_widget(self.loot_layout)
        loot_container.add_widget(loot_scroll)
        columns_layout.add_widget(loot_container)

        # ===== ПРАВАЯ КОЛОНКА: ИНВЕНТАРЬ =====
        inv_container = BoxLayout(
            orientation='vertical',
            spacing=dp(6),
            size_hint_x=0.5
        )
        # Фон для инвентаря
        with inv_container.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            inv_bg = Rectangle(
                pos=inv_container.pos,
                size=inv_container.size
            )
            inv_container.bind(
                pos=lambda i, v: setattr(inv_bg, 'pos', i.pos),
                size=lambda i, v: setattr(inv_bg, 'size', i.size)
            )

        inv_title = Label(
            text='🎒 ИНВЕНТАРЬ',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(35),
            color=(0.8, 0.8, 0.8, 1)
        )
        inv_container.add_widget(inv_title)

        self.inv_layout = GridLayout(
            cols=1,
            spacing=dp(6),
            size_hint_y=None,
            padding=dp(5)
        )
        self.inv_layout.bind(
            minimum_height=self.inv_layout.setter('height')
        )

        inv_scroll = ScrollView(size_hint_y=1)
        inv_scroll.add_widget(self.inv_layout)
        inv_container.add_widget(inv_scroll)
        columns_layout.add_widget(inv_container)

        self.add_widget(columns_layout)

        # Кнопка завершения внизу
        done_btn = Button(
            text='✓ ГОТОВО',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(18)
        )
        done_btn.bind(on_press=self.finish)
        self.add_widget(done_btn)

        # Инициализируем инвентарь ПОСЛЕ добавления всех виджетов
        self.update_inventory()

    def take_item(self, item):
        """Взять предмет из лута в инвентарь."""
        if item in self.loot_items:
            self.loot_items.remove(item)
            self.selected.append(item)
            if self.player_inventory and item.item:
                # item это LootDrop, item.item это Item объект
                self.player_inventory.add(
                    item.item,
                    item.quantity
                )
            # Обновляем отображение лута и инвентаря
            self.refresh_display()

    def refresh_display(self):
        """Переиграть отображение лута и инвентаря."""
        # Обновляем лут
        self.loot_layout.clear_widgets()
        if not self.loot_items:
            empty = Label(
                text='(больше нет)',
                font_size=dp(14),
                color=(0.7, 0.7, 0.7, 1),
                size_hint_y=None,
                height=dp(30)
            )
            self.loot_layout.add_widget(empty)
        else:
            for item in self.loot_items:
                row = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(40),
                    spacing=dp(5)
                )
                row.add_widget(Label(
                    text=f"{item.display()}",
                    font_size=dp(14),
                    size_hint_x=0.7
                ))
                btn = Button(
                    text='→',
                    size_hint_x=0.3,
                    size_hint_y=1
                )
                btn.bind(
                    on_press=lambda inst, i=item:
                    self.take_item(i)
                )
                row.add_widget(btn)
                self.loot_layout.add_widget(row)
        # Обновляем инвентарь
        self.update_inventory()

    def update_inventory(self):
        """Обновить отображение инвентаря."""
        self.inv_layout.clear_widgets()

        if not self.player_inventory:
            # Если инвентаря вообще нет
            empty_label = Label(
                text='[ОШИБКА: НЕТ ИНВЕНТАРЯ]',
                font_size=dp(12),
                color=(1, 0.2, 0.2, 1),
                size_hint_y=None,
                height=dp(30)
            )
            self.inv_layout.add_widget(empty_label)
            return

        items_list = self.player_inventory.list_items()

        if not items_list:
            # Инвентарь пуст
            empty_label = Label(
                text='(пусто)',
                font_size=dp(14),
                color=(0.7, 0.7, 0.7, 1),
                size_hint_y=None,
                height=dp(30)
            )
            self.inv_layout.add_widget(empty_label)
        else:
            # Показываем все предметы с кнопками выброса
            # list_items() возвращает [(Item, qty), ...]
            for item, qty in items_list:
                if item and hasattr(item, 'name'):
                    text = f"{item.name} x{qty}"
                elif item:
                    text = f"{str(item)} x{qty}"
                else:
                    text = f"[Неизвестный предмет] x{qty}"
                
                row = BoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    height=dp(40),
                    spacing=dp(5)
                )
                item_label = Label(
                    text=text,
                    font_size=dp(14),
                    size_hint_x=0.7,
                    color=(1, 1, 1, 1)
                )
                row.add_widget(item_label)
                
                # Кнопка для выброса предмета обратно в лут
                drop_btn = Button(
                    text='←',
                    size_hint_x=0.3,
                    size_hint_y=1
                )
                drop_btn.bind(
                    on_press=lambda inst, i=item, q=qty:
                    self.drop_item(i, q)
                )
                row.add_widget(drop_btn)
                self.inv_layout.add_widget(row)

    def drop_item(self, item, qty):
        """Переместить предмет из инвентаря обратно в лут."""
        # Попытаемся удалить один экземпляр или qty из инвентаря
        if not self.player_inventory or not item:
            return

        # Найти item.id если это объект Item
        item_id = getattr(item, 'id', None)
        if item_id:
            # Удаляем одну единицу за раз
            removed = self.player_inventory.remove(item_id, qty)
            if removed:
                # Создаем LootDrop и добавляем в лут
                from systems.battle import LootDrop
                ld = LootDrop(item_id, qty)
                self.loot_items.append(ld)
                self.refresh_display()

    def finish(self, instance):
        """Завершить выбор лута."""
        if self.on_done:
            self.on_done(self.selected)
