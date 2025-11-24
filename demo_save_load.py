#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quick demonstration of save/load system working correctly.
Shows actual save file and loaded player data.
"""

import sys
import json
from items import ItemDatabase
from creatures import Player
from save_system import save_game, load_game, delete_save, get_save_path


def demo():
    """Demonstration of working save/load system."""
    print("\n" + "=" * 60)
    print("SAVE/LOAD SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    ItemDatabase.initialize()
    
    # Create a character with some gear
    print("\nSTEP 1: Creating character...")
    player = Player("Hero", "warrior")
    print(f"   Created: {player.name} (Class: {player.cls})")
    hp_str = f"{player.health}/{player.max_health}"
    print(f"   Level: {player.level}, HP: {hp_str}")
    print(f"   Coins: {player.coins}, XP: {player.experience}")
    
    # Add some items
    print("\nSTEP 2: Adding items to inventory...")
    iron_axe = ItemDatabase.get("w_iron_axe")
    steel_plate = ItemDatabase.get("a_steel_plate")
    player.inventory.add(iron_axe, 3)
    player.inventory.add(steel_plate, 1)
    print(f"   Added 3x {iron_axe.name}")
    print(f"   Added 1x {steel_plate.name}")
    
    # Equip items
    print("\nSTEP 3: Equipping items...")
    player.equip_weapon(iron_axe)
    player.equip_armor(steel_plate)
    print(f"   Weapon: {player.weapon.name}")
    print(f"   Armor: {player.armor.name}")
    
    # Modify some stats
    print("\nSTEP 4: Modifying character state...")
    player.coins = 500
    player.experience = 250
    player.health = 100
    print(f"   Coins: {player.coins}")
    print(f"   Experience: {player.experience}")
    print(f"   Health: {player.health}")
    
    # Save
    filename = "demo_save"
    print(f"\nSTEP 5: Saving character as '{filename}'...")
    success = save_game(player, filename)
    print(f"   Save successful: {success}")
    
    # Show save file
    print("\nSTEP 6: Viewing save file...")
    save_path = get_save_path(filename)
    with open(save_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"   File size: {len(json.dumps(data))} bytes")
    print(f"   Version: {data['version']}")
    print(f"   Name: {data['player']['name']}")
    print(f"   Class: {data['player']['cls']}")
    items_count = len(data['player']['inventory']['items'])
    print(f"   Inventory items: {items_count} types")
    
    # Load
    print("\nSTEP 7: Loading character from save...")
    loaded_player = load_game(filename)
    if not loaded_player:
        print("   Load failed!")
        return False
    print("   Load successful!")
    
    # Verify
    print("\nSTEP 8: Verifying loaded character...")
    checks = [
        ("Name", loaded_player.name == "Hero"),
        ("Class", loaded_player.cls == "warrior"),
        ("Coins", loaded_player.coins == 500),
        ("Experience", loaded_player.experience == 250),
        ("Health", loaded_player.health == 100),
    ]
    
    all_pass = True
    for check_name, passed in checks:
        status = "OK" if passed else "FAIL"
        print(f"   [{status}] {check_name}")
        all_pass = all_pass and passed
    
    # Equipment verify
    has_weapon = (loaded_player.weapon and
                  loaded_player.weapon.id == "w_iron_axe")
    has_armor = (loaded_player.armor and
                 loaded_player.armor.id == "a_steel_plate")
    
    print(f"   [{'OK' if has_weapon else 'FAIL'}] Weapon equipped")
    print(f"   [{'OK' if has_armor else 'FAIL'}] Armor equipped")
    all_pass = all_pass and has_weapon and has_armor
    
    # Inventory check
    print("\nSTEP 9: Verifying inventory...")
    inv_items = loaded_player.inventory.list_items()
    print(f"   Items count: {len(inv_items)}")
    for item, qty in inv_items:
        print(f"      - {item.name} x{qty}")
    
    # Cleanup
    print("\nSTEP 10: Cleaning up...")
    delete_save(filename)
    print("   Demo save deleted")
    
    # Summary
    print("\n" + "=" * 60)
    if all_pass:
        print("SUCCESS: SAVE/LOAD SYSTEM WORKING!")
        print("All character data preserved correctly.")
    else:
        print("FAILED: Some checks failed - see above")
    print("=" * 60 + "\n")
    
    return all_pass


if __name__ == "__main__":
    success = demo()
    sys.exit(0 if success else 1)
