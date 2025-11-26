import sys
import os
_this_dir = os.path.dirname(__file__)
_proj_root = os.path.abspath(os.path.join(_this_dir, '..'))
sys.path.insert(0, _proj_root)

from data.items import ItemDatabase
from core.creatures import Player
from systems.shop_casino import Shop

ItemDatabase.initialize()

p = Player('Tester','warrior')
# Add two iron swords to inventory
sword = ItemDatabase.get('w_iron_sword')
if not sword:
    print('Missing sword in DB')
    raise SystemExit(1)

p.inventory.add(sword,2)
# Equip one copy
p.equip_weapon(sword)
shop = Shop({'w_iron_sword': 10})
print('Inventory qty before:', p.inventory.qty('w_iron_sword'))
print('Weapon equipped id:', p.weapon.id if p.weapon else None)
print('Attempt to sell 1 (should be allowed):', shop.sell(p,'w_iron_sword',1))
print('Inventory qty after:', p.inventory.qty('w_iron_sword'))
print('Attempt to sell 1 more (should be blocked):', shop.sell(p,'w_iron_sword',1))

# Now test armor
p2 = Player('ArmTester','warrior')
armor = ItemDatabase.get('a_leather_armor')
if not armor:
    print('Missing armor')
    raise SystemExit(1)

p2.inventory.add(armor,2)
# Equip one copy
p2.equip_armor(armor)
shop2 = Shop({'a_leather_armor': 10})
print('Armor inventory before:', p2.inventory.qty('a_leather_armor'))
print('Armor equipped id:', p2.armor.id if p2.armor else None)
print('Sell 1 (should be allowed):', shop2.sell(p2,'a_leather_armor',1))
print('Armor inventory after:', p2.inventory.qty('a_leather_armor'))
print('Sell 1 more (should be blocked):', shop2.sell(p2,'a_leather_armor',1))
