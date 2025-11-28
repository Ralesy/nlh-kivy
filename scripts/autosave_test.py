import sys, os
# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.items import ItemDatabase
from core.creatures import TestPlayer
from systems.save_system import save_game, load_game, get_save_list, get_save_path
import json

ItemDatabase.initialize()

p = TestPlayer('AutoTest')
# modify fields
p.coins = 1234
p.experience = 789
# add potion
it = ItemDatabase.get('p_small')
if it:
    p.inventory.add(it, 5)

ok = save_game(p, 'autosave_test')
print('saved:', ok)
print('saves list (top 5):', get_save_list()[:5])
pl = load_game('autosave_test')
print('loaded:', pl.name, pl.coins, pl.experience)
with open(get_save_path('autosave_test'), 'r', encoding='utf-8') as f:
    data = json.load(f)
print('json keys:', list(data.keys()))
print('player keys sample:', list(data['player'].keys()))
