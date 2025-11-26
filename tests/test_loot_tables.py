from data.enemies import EnemyDatabase

EnemyDatabase.initialize()

test_enemies = [
    "enemy_forest_raider",
    "enemy_forest_bandit",
    "enemy_forest_deserter",
    "enemy_swamp_goblin",
    "enemy_mines_orc",
    "enemy_mines_dwarven_draugr"
]

for enemy_id in test_enemies:
    enemy = EnemyDatabase.get(enemy_id)
    if enemy and enemy.loot_table:
        items = [f"{item} ({prob*100:.0f}%)" for item, prob in enemy.loot_table]
        print(f"\n{enemy.name}:")
        for item in items:
            print(f"  • {item}")
