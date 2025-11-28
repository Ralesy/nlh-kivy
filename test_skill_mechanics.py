#!/usr/bin/env python3
"""Automated test for skill mechanics.
Checks: endurance, strength, agility, luck, trade, and level-up skill point grant.
"""
from data.items import ItemDatabase
ItemDatabase.initialize()
from core.creatures import Player

failed = False

p = Player('Tester', 'squire')
print('Initial stats:')
print(' base_health=', p.base_health)
print(' base_damage=', p.base_damage)
print(' inventory_capacity=', p.inventory.capacity)
print(' critical_chance=', p.critical_chance)
print(' luck=', p.luck)
print(' selling_multiplier=', p.selling_multiplier)
print(' skill_points_available=', p.skill_points_available)

# Store baselines
bh = p.base_health
bd = p.base_damage
cap = p.inventory.capacity
crit = p.critical_chance
luck = p.luck
sell = p.selling_multiplier
pts = p.skill_points_available

# Allocate one point to each skill
skills = ['endurance','strength','agility','luck','trade']
for s in skills:
    ok = p.allocate_skill_point(s)
    if not ok:
        print(f'Failed to allocate to {s}')
        failed = True

# After allocations
print('\nAfter allocations:')
print(' base_health=', p.base_health)
print(' base_damage=', p.base_damage)
print(' inventory_capacity=', p.inventory.capacity)
print(' critical_chance=', p.critical_chance)
print(' luck=', p.luck)
print(' selling_multiplier=', p.selling_multiplier)
print(' skill_points_available=', p.skill_points_available)

# Expected changes according to STAT_COEFFICIENTS in code
exp_bh = bh + p.STAT_COEFFICIENTS['endurance']['health']
exp_bd = bd + p.STAT_COEFFICIENTS['strength']['damage']
exp_cap = 20 + p.STAT_COEFFICIENTS['strength']['inventory_capacity']  # base 20 + strength
exp_crit = crit + p.STAT_COEFFICIENTS['agility']['critical_chance']
exp_luck = luck + p.STAT_COEFFICIENTS['luck']['luck']
exp_sell = sell + p.STAT_COEFFICIENTS['trade']['selling_multiplier']

if p.base_health != exp_bh:
    print(f'Endurance failed: got {p.base_health}, expected {exp_bh}')
    failed = True
if p.base_damage != exp_bd:
    print(f'Strength damage failed: got {p.base_damage}, expected {exp_bd}')
    failed = True
if p.inventory.capacity != exp_cap:
    print(f'Strength capacity failed: got {p.inventory.capacity}, expected {exp_cap}')
    failed = True
# Allow small float tolerance
if abs(p.critical_chance - exp_crit) > 1e-6:
    print(f'Agility failed: got {p.critical_chance}, expected {exp_crit}')
    failed = True
if abs(p.luck - exp_luck) > 1e-6:
    print(f'Luck failed: got {p.luck}, expected {exp_luck}')
    failed = True
if abs(p.selling_multiplier - exp_sell) > 1e-6:
    print(f'Trade failed: got {p.selling_multiplier}, expected {exp_sell}')
    failed = True

# Test level-up grants +1 skill point
before_pts = p.skill_points_available
# give exactly enough XP to level once
msgs = p.add_experience(p.level * 100)
after_pts = p.skill_points_available
print('\nLevel-up messages:', msgs)
print(' skill points before=', before_pts, 'after=', after_pts)
if after_pts - before_pts != 1:
    print('Level-up skill point grant failed')
    failed = True

if failed:
    print('\nTEST RESULT: FAILED')
    raise SystemExit(1)
else:
    print('\nTEST RESULT: PASSED')
    raise SystemExit(0)
