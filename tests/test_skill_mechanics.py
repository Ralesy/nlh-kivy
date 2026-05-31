#!/usr/bin/env python3
"""Тест механики навыков: распределение очков и бонус за уровень."""
from data.items import ItemDatabase
from core.creatures import Player

ItemDatabase.initialize()


def test_skill_mechanics():
    """Проверить endurance, strength, agility, luck, trade и очко за level-up."""
    p = Player('Tester', 'squire')

    bh = p.base_health
    bd = p.base_damage
    cap = p.inventory.capacity
    crit = p.critical_chance
    luck = p.luck
    sell = p.selling_multiplier

    skills = ['endurance', 'strength', 'agility', 'luck', 'trade']
    for skill in skills:
        assert p.allocate_skill_point(skill), f'Failed to allocate to {skill}'

    exp_bh = bh + p.STAT_COEFFICIENTS['endurance']['health']
    exp_bd = bd + p.STAT_COEFFICIENTS['strength']['damage']
    exp_cap = 20 + p.STAT_COEFFICIENTS['strength']['inventory_capacity']
    exp_crit = crit + p.STAT_COEFFICIENTS['agility']['critical_chance']
    exp_luck = luck + p.STAT_COEFFICIENTS['luck']['luck']
    exp_sell = sell + p.STAT_COEFFICIENTS['trade']['selling_multiplier']

    assert p.base_health == exp_bh
    assert p.base_damage == exp_bd
    assert p.inventory.capacity == exp_cap
    assert abs(p.critical_chance - exp_crit) <= 1e-6
    assert abs(p.luck - exp_luck) <= 1e-6
    assert abs(p.selling_multiplier - exp_sell) <= 1e-6

    before_pts = p.skill_points_available
    p.add_experience(p.level * 100)
    assert p.skill_points_available - before_pts == 1


if __name__ == '__main__':
    test_skill_mechanics()
    print('TEST RESULT: PASSED')
