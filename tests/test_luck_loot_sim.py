#!/usr/bin/env python3
"""Quick simulation to show luck effect on rare drop frequency."""
from data.items import ItemDatabase
ItemDatabase.initialize()
from data.enemies import Enemy, EnemyDatabase
from core.creatures import Player
import random

# Create a test enemy with loot table and humanoid type
EnemyDatabase.initialize()
# Use an existing enemy template that has loot_table, e.g., deserter
template = EnemyDatabase.get('enemy_forest_deserter')


def trial(luck_value, trials=1000):
    rare_count = 0
    chosen_counts = {}
    for _ in range(trials):
        drops = template.generate_loot(luck=luck_value)
        for item_id, qty in drops:
            # consider rare items as those starting with 'w_steel' or 'a_steel'
            if item_id.startswith('w_steel') or item_id.startswith('a_steel'):
                rare_count += 1
            chosen_counts[item_id] = chosen_counts.get(item_id, 0) + 1
    return rare_count, chosen_counts

def test_enemy_loot_template_exists():
    """Шаблон врага с таблицей лута должен быть в базе."""
    assert template is not None


if __name__ == '__main__':
    if not template:
        print('No template found')
        raise SystemExit(1)
    for luck in [0.8, 1.0, 1.2, 1.5, 2.0]:
        rare, counts = trial(luck, trials=2000)
        print(f'luck={luck}: rare_drops={rare} / 2000 -> {rare/2000:.3f}')
        top = sorted(counts.items(), key=lambda x: -x[1])[:5]
        print(' top:', top)

