# Automated playthrough simulation: accept temp quest, auto-win, verify cleanup
import sys
import os
_this_dir = os.path.dirname(__file__)
_proj_root = os.path.abspath(os.path.join(_this_dir, '..'))
sys.path.insert(0, _proj_root)

from items import ItemDatabase
from game import Game
from creatures import Player
from battle import Battlefield


def run():
    ItemDatabase.initialize()
    g = Game()
    g.player = Player('Playtester', 'warrior')

    # Accept temporary quest in Rivertown
    tav = g.cities['Rivertown'].tavern
    qid = 'q_rescue_boy'
    q = tav.get_quest(qid)
    assert q is not None, 'temp quest missing'

    q.accept()
    g.active_quests[q.id] = ('Rivertown', q)
    if q.location and q.temporary:
        g.temp_locations[q.location] = q.id

    print('Before travel: temp_locations=', g.temp_locations)

    # Monkeypatch battle_loop to simulate victory and dead enemies
    def fake_battle_loop(self, battlefield: Battlefield):
        # Mark all enemies as dead
        for e in battlefield.enemies:
            e.health = 0
            e.die('test')
        return True

    # Monkeypatch EnemyGenerator.generate to deterministically produce
    # the exact enemies needed for the temp quest (Лесной гоблин)
    from battle import EnemyGenerator
    from creatures import Creature

    def fake_generate(location: str, player_level: int, num: int = 1):
        enemies = []
        for _ in range(num):
            # construct a Creature that will be recognized by quest logic
            e = Creature('Лесной гоблин', 30, 8, 12, level=player_level)
            enemies.append(e)
        return enemies

    # Attach monkeypatches
    g.battle_loop = fake_battle_loop.__get__(g, Game)
    EnemyGenerator.generate = staticmethod(fake_generate)

    # Enter the temporary location (hill_cave) repeatedly until quest completes
    loc = q.location
    print(f'Entering location {loc}')
    max_attempts = 4
    for attempt in range(max_attempts):
        g.enter_location(loc)
        print(
            f"Attempt {attempt+1}: progress={q.progress} "
            f"complete={q.complete}"
        )
        if q.complete:
            break

    # After travel(s), quest should be complete and temp location removed
    complete = q.complete
    print('Quest complete:', complete)
    print('After travel: temp_locations=', g.temp_locations)

    if not complete:
        print('FAIL: temp quest did not complete after attempts')
        return 1
    if loc in g.temp_locations:
        print('FAIL: temp location not removed')
        return 1

    # Also check other city's quest instance unchanged
    other_q = g.cities['Highkeep'].tavern.get_quest(qid)
    if other_q and other_q.progress and any(
        v > 0 for v in other_q.progress.values()
    ):
        print('FAIL: other city quest progressed')
        return 1

    print('PASS: playthrough simulation successful')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(run())
