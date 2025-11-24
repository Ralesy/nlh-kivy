from items import ItemDatabase
from creatures import Player
from shop_casino import Shop

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
shop = Shop({'w_iron_sword': None})
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
shop2 = Shop({'a_leather_armor': None})
print('Armor inventory before:', p2.inventory.qty('a_leather_armor'))
print('Armor equipped id:', p2.armor.id if p2.armor else None)
print('Sell 1 (should be allowed):', shop2.sell(p2,'a_leather_armor',1))
print('Armor inventory after:', p2.inventory.qty('a_leather_armor'))
print('Sell 1 more (should be blocked):', shop2.sell(p2,'a_leather_armor',1))
