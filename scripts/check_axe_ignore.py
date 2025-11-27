import sys
from pathlib import Path

# Ensure project root is on sys.path so `data` and `core` packages import correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.items import ItemDatabase
from core.creatures import Player, Creature
from systems.battle import Battlefield

ItemDatabase.initialize()

# Create player and equip an axe
player = Player('Tester', 'warrior')
axe = ItemDatabase.get('w_iron_axe') or ItemDatabase.get('w_orc_maul')
if not axe:
    raise SystemExit('No axe found in ItemDatabase')
player.equip_weapon(axe)

# Create enemy and equip armor
enemy = Creature('Armored Dummy', base_health=100, base_damage=0, base_coins=0)
armor = ItemDatabase.get('a_iron_plate') or ItemDatabase.get('a_leather_armor')
if armor:
    enemy.equip_armor(armor)

# Setup battlefield to use its helper
bf = Battlefield(player, [enemy])

base_damage = player.damage
print('Player base damage:', base_damage)
print('Enemy defense:', enemy.defense)

# Apply armor-ignore calculation
damage_after = bf._apply_armor_ignore(base_damage, enemy)
ignored_amount = damage_after - base_damage
print('Damage after armor-ignore added:', damage_after)
print('Armor ignored amount (added to damage):', ignored_amount)

# Effective damage applied to enemy
effective = max(0, damage_after - enemy.defense)
print('Effective damage (damage - defense):', effective)

# Use take_damage to show actual applied damage and resulting HP
applied = enemy.take_damage(damage_after)
print('enemy.take_damage returned (actual HP reduced by):', applied)
print('Enemy HP now:', enemy.health)

# For clarity, show calculation expected: int(defense * 0.3)
try:
    from data.weapon_abilities import ArmorIgnoreAbility
    # compute expected armor ignore
    expected_ignore = int(enemy.defense * 0.30)
    print('Expected armor-ignore (int(defense * 0.30)):', expected_ignore)
except Exception:
    pass
