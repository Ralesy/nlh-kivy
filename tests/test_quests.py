# Quick test for quest activation and isolation
import sys
import os

# Ensure project root is on sys.path
_this_dir = os.path.dirname(__file__)
_proj_root = os.path.abspath(os.path.join(_this_dir, '..'))
sys.path.insert(0, _proj_root)

from items import ItemDatabase
from game import Game
from creatures import Player


def run():
    ItemDatabase.initialize()
    g = Game()
    # create a simple player (avoid interactive create_character)
    p = Player("Tester", "warrior")
    g.player = p

    # Two taverns exist in different cities
    tav_a = g.cities['Rivertown'].tavern
    tav_b = g.cities['Highkeep'].tavern

    qid = 'q_missing_traveler'
    qa = tav_a.get_quest(qid)
    qb = tav_b.get_quest(qid)

    assert qa is not None, 'Quest missing in tavern A'
    assert qb is not None, 'Quest missing in tavern B'
    # Ensure they are distinct objects
    if qa is qb:
        print('ERROR: Quest instances are the same object across taverns')
        return 2

    # Accept quest in Rivertown (register active quest)
    qa.accept()
    g.active_quests[qa.id] = ('Rivertown', qa)
    if qa.location and qa.temporary:
        g.temp_locations[qa.location] = qa.id

    # Simulate 4 bandit kills in 'gorge' location
    for i in range(4):
        # Only active quests for gorge should progress
        for (city_name, q) in list(g.active_quests.values()):
            if q.location is None or q.location == 'gorge':
                q.register_kill('Бандит')

    # Now check that the accepted quest progressed to complete
    if not qa.complete:
        print('FAIL: Accepted quest did not complete')
        return 1

    # Check that the other tavern's quest instance did NOT progress
    if qb.progress.get('Бандит', 0) != 0:
        print('FAIL: Other tavern quest was incorrectly progressed')
        return 1

    print('PASS: Quest progression isolated and works as expected')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(run())
