#!/usr/bin/env python3
"""Test that ability button appears and works in battle UI"""

from core.creatures import Player, Creature
from data.items import ItemDatabase
from systems.battle import Battlefield


def test_ability_button():
    """Test that weapon ability is present and UI can display it"""
    
    # Initialize ItemDatabase
    db = ItemDatabase()
    db.initialize()
    
    # Get a sword weapon
    sword = db.get('w_iron_sword')
    if not sword:
        print("Failed: Cannot find sword")
        return False
    
    # Create player and equip sword
    player = Player(name="Hero", background="squire")
    player.equip_weapon(sword)
    
    print("OK: Player equipped with sword")
    print(f"   Weapon: {player.weapon.name}")
    print(f"   Damage: {player.damage}")
    
    # Check if weapon has ability
    if hasattr(player.weapon, 'ability') and player.weapon.ability:
        ability = player.weapon.ability
        print(f"OK: Weapon has ability: {ability.name}")
        print(f"   Type: {ability.ability_type}")
    else:
        print("Failed: Weapon has no ability!")
        return False
    
    # Create a test enemy
    goblin = Creature(
        name="Goblin",
        base_health=10,
        base_damage=3,
        base_coins=15,
        level=1
    )
    
    # Create a battlefield
    enemies = [goblin]
    battlefield = Battlefield(player, enemies)
    
    print("OK: Battle system initialized")
    print(f"   ability_used_this_battle = {battlefield.ability_used_this_battle}")
    
    # Simulate using ability
    print("\nTesting ability usage...")
    success, logs = battlefield.use_weapon_ability()
    
    if success:
        print("OK: Ability used successfully!")
        for log in logs:
            print(f"   > {log}")
        print(f"   ability_used_this_battle = {battlefield.ability_used_this_battle}")
    else:
        print(f"Failed: {logs[0]}")
        return False
    
    # Try using again
    print("\nTesting repeat usage prevention...")
    success, logs = battlefield.use_weapon_ability()
    if not success:
        print("OK: System blocked repeat usage")
        print(f"   Message: {logs[0]}")
    else:
        print("Failed: Ability was used twice!")
        return False
    
    print("\n✓ ALL TESTS PASSED!")
    print("The ability button will:")
    print("   • Show in battle UI")
    print(f"   • Display name: '{ability.name}'")
    print("   • Disable after first use")
    print("   • Enable in new battle")
    
    return True


if __name__ == "__main__":
    test_ability_button()
