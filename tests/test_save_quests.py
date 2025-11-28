# Test saving and loading game state for quests/temp locations
import sys
import os
_this_dir = os.path.dirname(__file__)
_proj_root = os.path.abspath(os.path.join(_this_dir, '..'))
sys.path.insert(0, _proj_root)

from data.items import ItemDatabase
from core.game import Game
from systems.save_system import save_game, load_game


def run():
    ItemDatabase.initialize()
    g = Game()
    # create a simple player (avoid interactive create_character)
    from creatures import Player
    p = Player("Saver", "squire")
    g.player = p

    tav = g.cities['Rivertown'].tavern
    qid = 'q_missing_traveler'
    q = tav.get_quest(qid)
    assert q is not None

    # accept and make some progress
    q.accept()
    q.register_kill('Бандит')
    g.active_quests[qid] = ('Rivertown', q)
    if q.location and q.temporary:
        g.temp_locations[q.location] = qid

    # Save
    fname = 'test_save'
    gs = {
        'temp_locations': g.temp_locations,
        'active_quests': {
            qid: {
                'city': 'Rivertown',
                'progress': q.progress,
                'complete': q.complete,
                'claimed': q.claimed,
                'active': q.active,
                'location': q.location,
            }
        }
    }
    ok = save_game(g.player, fname, gs)
    if not ok:
        print('FAIL: save_game returned False')
        return 2

    pl, loaded_state = load_game(fname)
    if not pl:
        print('FAIL: load_game did not return player')
        return 2

    # Ensure loaded_state contains our data
    if not loaded_state or 'active_quests' not in loaded_state:
        print('FAIL: saved game_state missing after load')
        return 2

    act = loaded_state['active_quests']
    if qid not in act:
        print('FAIL: active quest id missing in saved state')
        return 2

    print('PASS: save/load preserved quest state')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(run())
