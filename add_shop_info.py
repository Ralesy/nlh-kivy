#!/usr/bin/env python3
"""
Script to add Info button and method to ShopScreen
"""
import sys

# Read ui/ui_app.py
with open('ui/ui_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace show_buy method to add Info button
old_show_buy = '''            item_layout.add_widget(item_label)
            
            btn_buy = Button(text='Купить', size_hint_x=0.3)
            btn_buy.bind(on_press=lambda x, item_id=iid: self.buy_item(item_id))
            item_layout.add_widget(btn_buy)'''

new_show_buy = '''            item_layout.add_widget(item_label)
            
            btn_info = Button(text='ℹ️', size_hint_x=0.1, font_size=dp(16))
            btn_info.bind(on_press=lambda x, it=item: self.show_item_info(it))
            item_layout.add_widget(btn_info)
            
            btn_buy = Button(text='Купить', size_hint_x=0.2)
            btn_buy.bind(on_press=lambda x, item_id=iid: self.buy_item(item_id))
            item_layout.add_widget(btn_buy)'''

content = content.replace(old_show_buy, new_show_buy, 1)

# Find and replace show_sell method to add Info button
old_show_sell = '''            item_layout.add_widget(item_label)
            
            btn_sell = Button(text='Продать', size_hint_x=0.3)
            btn_sell.bind(on_press=lambda x, item_id=item.id: self.sell_item(item_id))
            item_layout.add_widget(btn_sell)
            
            self.content_layout.add_widget(item_layout)
    
    def buy_item(self, item_id):'''

new_show_sell = '''            item_layout.add_widget(item_label)
            
            btn_info = Button(text='ℹ️', size_hint_x=0.1, font_size=dp(16))
            btn_info.bind(on_press=lambda x, it=item: self.show_item_info(it))
            item_layout.add_widget(btn_info)
            
            btn_sell = Button(text='Продать', size_hint_x=0.2)
            btn_sell.bind(on_press=lambda x, item_id=item.id: self.sell_item(item_id))
            item_layout.add_widget(btn_sell)
            
            self.content_layout.add_widget(item_layout)
    
    def show_item_info(self, item):
        """Показать информацию о предмете."""
        info_text = f"{item.display_name()}\n\n"
        
        if isinstance(item, Weapon):
            info_text += f"⚔️ Урон: {item.damage_bonus}\n"
            info_text += f"Материал: {WEAPON_MATERIALS.get(item.material, 'неизвестный')}\n"
            info_text += f"Состояние: {item.condition_display}\n"
        elif isinstance(item, Armor):
            info_text += f"🛡️ Защита: {item.defense}\n"
            info_text += f"Материал: {ARMOR_MATERIALS.get(item.material, 'неизвестная')}\n"
            info_text += f"Состояние: {item.condition_display}\n"
        elif isinstance(item, Potion):
            info_text += f"💚 Восстанавливает: {item.heal_amount} HP\n"
        
        info_text += f"Цена: {item.price} монет\n"
        if item.description:
            info_text += f"\n📝 {item.description}"
        
        # Информация о способности (если есть)
        if hasattr(item, 'ability') and item.ability:
            ab = item.ability
            info_text += "\n\n"
            info_text += f"Способность: {ab.name}"
            if hasattr(ab, 'ability_type'):
                info_text += f" ({ab.ability_type})"
            info_text += "\n"
            if hasattr(ab, 'damage_per_hit'):
                info_text += f"+{ab.damage_per_hit} урона за удар\n"
            if hasattr(ab, 'armor_ignore'):
                info_text += (f"Игнорирует "
                             f"{int(ab.armor_ignore * 100)}% брони\n")
            if hasattr(ab, 'crit_multiplier'):
                info_text += f"Крит. множитель: x{ab.crit_multiplier}\n"
        
        content = BoxLayout(orientation='vertical', spacing=dp(10),
                           padding=dp(15))
        scroll = ScrollView()
        info_label = Label(
            text=info_text,
            font_size=dp(16),
            size_hint_y=None,
            text_size=(dp(300), None),
            halign='left',
            valign='top'
        )
        info_label.bind(texture_size=info_label.setter('size'))
        scroll.add_widget(info_label)
        content.add_widget(scroll)
        
        btn_close = Button(text='Закрыть', size_hint_y=None, height=dp(50))
        content.add_widget(btn_close)
        
        popup = Popup(
            title='📖 Информация о предмете',
            content=content,
            size_hint=(0.8, 0.7)
        )
        btn_close.bind(on_press=popup.dismiss)
        popup.open()
    
    def buy_item(self, item_id):'''

content = content.replace(old_show_sell, new_show_sell, 1)

# Write back
with open('ui/ui_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Added Info button and show_item_info to ShopScreen")
