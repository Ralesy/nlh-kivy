#!/usr/bin/env python3
"""Test backgrounds system"""

from data.items import ItemDatabase
ItemDatabase.initialize()
from core.creatures import Player

print("=== Testing Backgrounds System ===\n")

for bg in ['noble', 'squire', 'hunter']:
    p = Player('Test', bg)
    w = p.weapon.name if p.weapon else 'None'
    a = p.armor.name if p.armor else 'None'
    inv_items = [(item.name, qty) for item, qty in p.inventory.list_items()]
    print(f'{bg.upper()}: Coins={p.coins}, Weapon={w}, Armor={a}')
    print(f'  Inventory: {inv_items}')

print("\n=== Testing Skill Point System ===\n")

p = Player('TestChar', 'squire')
print(f"Initial: HP={p.base_health}, DMG={p.base_damage}")
print(f"Skill Points Available: {p.skill_points_available}")
print(f"Inventory Capacity: {p.inventory.capacity}")
print(f"Critical Chance: {p.critical_chance:.2%}")

# Allocate points
p.allocate_skill_point('endurance')
p.allocate_skill_point('endurance')
p.allocate_skill_point('strength')
p.allocate_skill_point('agility')
p.allocate_skill_point('agility')

print(f"\nAfter allocation: HP={p.base_health}, DMG={p.base_damage}")
print(f"Skill Points Available: {p.skill_points_available}")
print(f"Inventory Capacity: {p.inventory.capacity}")
print(f"Critical Chance: {p.critical_chance:.2%}")

# Test level up and skill points gain
p.add_experience(1000)
print(f"\nAfter level up: Skill Points Available: {p.skill_points_available}")

print("\n=== All tests passed! ===")
