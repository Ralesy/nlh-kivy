#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive test suite for save/load system.
Tests player state persistence, inventory, equipment, and quests.
"""

import sys
import os
import json
from pathlib import Path

_this_dir = os.path.dirname(__file__)
_proj_root = os.path.abspath(os.path.join(_this_dir, '..'))
sys.path.insert(0, _proj_root)

from data.items import ItemDatabase, Weapon, Armor
from core.creatures import Player, Inventory
from systems.save_system import save_game, load_game, delete_save, get_save_list


def test_basic_save_load():
    """Test basic player save and load."""
    print("\n=== Test 1: Basic Save/Load ===")
    
    # Initialize database
    ItemDatabase.initialize()
    
    # Create a player
    player = Player("TestHero", "warrior")
    player.coins = 500
    player.experience = 250
    player.level = 2
    
    # Save the player
    filename = "test_basic"
    success = save_game(player, filename)
    
    if not success:
        print("❌ FAIL: save_game returned False")
        return False
    
    # Load the player
    loaded_player = load_game(filename)
    if not loaded_player:
        print("❌ FAIL: load_game returned None")
        delete_save(filename)
        return False
    
    # Verify basic attributes
    if loaded_player.name != "TestHero":
        print(f"❌ FAIL: Name mismatch: {loaded_player.name}")
        delete_save(filename)
        return False
    
    if loaded_player.coins != 500:
        print(f"❌ FAIL: Coins mismatch: {loaded_player.coins}")
        delete_save(filename)
        return False
    
    if loaded_player.experience != 250:
        print(f"❌ FAIL: Experience mismatch: {loaded_player.experience}")
        delete_save(filename)
        return False
    
    print("✅ PASS: Basic save/load works")
    delete_save(filename)
    return True


def test_player_reconstruction():
    """Test reconstructing player from dict."""
    print("\n=== Test 2: Player Reconstruction ===")
    
    ItemDatabase.initialize()
    
    # Create and save
    player1 = Player("Adventurer", "archer")
    player1.coins = 1000
    player1.experience = 500
    player1.health = 45  # Reduce from max
    
    filename = "test_reconstruction"
    save_game(player1, filename)
    
    # Load (which returns Player directly now)
    player2 = load_game(filename)
    if not player2:
        print("❌ FAIL: Could not load save file")
        delete_save(filename)
        return False
    
    if player2.name != "Adventurer":
        print(f"❌ FAIL: Name not preserved: {player2.name}")
        delete_save(filename)
        return False
    
    if player2.cls != "archer":
        print(f"❌ FAIL: Class not preserved: {player2.cls}")
        delete_save(filename)
        return False
    
    if player2.coins != 1000:
        print(f"❌ FAIL: Coins not preserved: {player2.coins}")
        delete_save(filename)
        return False
    
    if player2.experience != 500:
        print(f"❌ FAIL: Experience not preserved: {player2.experience}")
        delete_save(filename)
        return False
    
    if player2.health != 45:
        print(f"❌ FAIL: Health not preserved: {player2.health}")
        delete_save(filename)
        return False
    
    print("✅ PASS: Player reconstruction works")
    delete_save(filename)
    return True


def test_inventory_persistence():
    """Test inventory items are saved and loaded."""
    print("\n=== Test 3: Inventory Persistence ===")
    
    ItemDatabase.initialize()
    
    # Create player and add items
    player = Player("Collector", "warrior")
    
    # Get some items from database
    iron_sword = ItemDatabase.get("w_iron_sword")
    steel_armor = ItemDatabase.get("a_steel_plate")
    
    if not iron_sword or not steel_armor:
        print("❌ FAIL: Could not get test items from database")
        return False
    
    # Add items to inventory
    player.inventory.add(iron_sword, 2)  # Add 2 swords
    player.inventory.add(steel_armor, 1)  # Add 1 armor
    
    filename = "test_inventory"
    save_game(player, filename)
    
    # Load player
    loaded_player = load_game(filename)
    if not loaded_player:
        print("❌ FAIL: Could not load save file")
        delete_save(filename)
        return False
    
    # Check inventory data
    found_sword = False
    found_armor = False
    
    for item, qty in loaded_player.inventory.list_items():
        if item.id == "w_iron_sword" and qty == 2:
            found_sword = True
        if item.id == "a_steel_plate" and qty == 1:
            found_armor = True
    
    if not found_sword:
        print("❌ FAIL: Sword not found in loaded inventory")
        delete_save(filename)
        return False
    
    if not found_armor:
        print("❌ FAIL: Armor not found in loaded inventory")
        delete_save(filename)
        return False
    
    print("✅ PASS: Inventory persistence works")
    delete_save(filename)
    return True


def test_equipped_items():
    """Test equipped weapon and armor are saved."""
    print("\n=== Test 4: Equipped Items ===")
    
    ItemDatabase.initialize()
    
    player = Player("Warrior", "warrior")
    
    # Equip items
    sword = ItemDatabase.get("w_steel_sword")
    armor = ItemDatabase.get("a_iron_plate")
    
    if not sword or not armor:
        print("❌ FAIL: Could not get test items")
        return False
    
    player.inventory.add(sword, 1)
    player.inventory.add(armor, 1)
    player.equip_weapon(sword)
    player.equip_armor(armor)
    
    filename = "test_equipped"
    save_game(player, filename)
    
    # Load and verify
    loaded_player = load_game(filename)
    if not loaded_player:
        print("❌ FAIL: Could not load save")
        delete_save(filename)
        return False
    
    if not loaded_player.weapon or \
            loaded_player.weapon.id != "w_steel_sword":
        print("❌ FAIL: Weapon not equipped after load")
        delete_save(filename)
        return False
    
    if not loaded_player.armor or \
            loaded_player.armor.id != "a_iron_plate":
        print("❌ FAIL: Armor not equipped after load")
        delete_save(filename)
        return False
    
    print("✅ PASS: Equipped items persistence works")
    delete_save(filename)
    return True


def test_save_list():
    """Test getting list of saves."""
    print("\n=== Test 5: Save List ===")
    
    ItemDatabase.initialize()
    
    # Create multiple saves
    player = Player("Tester", "warrior")
    
    filenames = ["test_list_1", "test_list_2", "test_list_3"]
    for fname in filenames:
        save_game(player, fname)
    
    # Get save list
    saves = get_save_list()
    
    # Check all saves are listed
    for fname in filenames:
        if fname not in saves:
            print(f"❌ FAIL: {fname} not in save list")
            for fname in filenames:
                delete_save(fname)
            return False
    
    print(f"✅ PASS: Save list works ({len(filenames)} saves found)")
    
    # Clean up
    for fname in filenames:
        delete_save(fname)
    
    return True


def test_delete_save():
    """Test deleting a save."""
    print("\n=== Test 6: Delete Save ===")
    
    ItemDatabase.initialize()
    
    player = Player("Deleter", "warrior")
    filename = "test_delete_me"
    
    save_game(player, filename)
    
    # Verify it exists
    saves = get_save_list()
    if filename not in saves:
        print("❌ FAIL: Save not created")
        return False
    
    # Delete it
    success = delete_save(filename)
    if not success:
        print("❌ FAIL: delete_save returned False")
        return False
    
    # Verify it's gone
    saves = get_save_list()
    if filename in saves:
        print("❌ FAIL: Save still exists after deletion")
        delete_save(filename)
        return False
    
    print("✅ PASS: Delete save works")
    return True


def test_multiple_characters():
    """Test saving/loading multiple different characters."""
    print("\n=== Test 7: Multiple Characters ===")
    
    ItemDatabase.initialize()
    
    # Create and save different characters
    players = [
        ("Warrior_1", "warrior", 100, 500),
        ("Mage_1", "mage", 75, 300),
        ("Archer_1", "archer", 60, 400),
    ]
    
    filenames = []
    for name, cls, coins, exp in players:
        player = Player(name, cls)
        player.coins = coins
        player.experience = exp
        
        filename = f"test_char_{name}"
        filenames.append(filename)
        success = save_game(player, filename)
        
        if not success:
            print(f"❌ FAIL: Could not save {name}")
            for fn in filenames:
                delete_save(fn)
            return False
    
    # Load and verify each
    for i, (name, cls, coins, exp) in enumerate(players):
        filename = filenames[i]
        loaded_player = load_game(filename)
        
        if not loaded_player:
            print(f"❌ FAIL: Could not load {filename}")
            for fn in filenames:
                delete_save(fn)
            return False
        
        if loaded_player.name != name:
            print(f"❌ FAIL: Name mismatch in {filename}")
            for fn in filenames:
                delete_save(fn)
            return False
        
        if loaded_player.cls != cls:
            print(f"❌ FAIL: Class mismatch in {filename}")
            for fn in filenames:
                delete_save(fn)
            return False
        
        if loaded_player.coins != coins:
            print(f"❌ FAIL: Coins mismatch in {filename}")
            for fn in filenames:
                delete_save(fn)
            return False
    
    print("✅ PASS: Multiple characters saved/loaded correctly")
    
    # Clean up
    for fn in filenames:
        delete_save(fn)
    
    return True


def test_json_format():
    """Test that save files are valid JSON with proper structure."""
    print("\n=== Test 8: JSON Format ===")
    
    ItemDatabase.initialize()
    
    player = Player("JsonTester", "warrior")
    player.coins = 12345
    
    filename = "test_json_format"
    save_game(player, filename)
    
    # Read the file directly
    from save_system import get_save_path
    save_path = get_save_path(filename)
    
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ FAIL: Invalid JSON: {e}")
        delete_save(filename)
        return False
    
    # Check structure
    if "player" not in data:
        print("❌ FAIL: 'player' key missing from save file")
        delete_save(filename)
        return False
    
    if "version" not in data:
        print("❌ FAIL: 'version' key missing from save file")
        delete_save(filename)
        return False
    
    player_data = data["player"]
    required_keys = ["name", "cls", "level", "coins", "experience", "health"]
    
    for key in required_keys:
        if key not in player_data:
            print(f"❌ FAIL: '{key}' missing from player data")
            delete_save(filename)
            return False
    
    print("✅ PASS: Save file has correct JSON structure")
    delete_save(filename)
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 60)
    print("SAVE/LOAD SYSTEM TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_basic_save_load,
        test_player_reconstruction,
        test_inventory_persistence,
        test_equipped_items,
        test_save_list,
        test_delete_save,
        test_multiple_characters,
        test_json_format,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"❌ EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60 + "\n")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
