# -*- coding: utf-8 -*-

# -- stdlib --
# -- third party --
import pytest

# -- own --


# -- code --
@pytest.mark.django_db
def test_RkAdjustRanking(Q, auth_header):
    import system.models
    system.models.Setting(key='ranking-season', value='1').save()

    from player.tests import PlayerFactory
    from game.tests import GameFactory

    PlayerFactory.create()
    PlayerFactory.create()
    g = GameFactory.create()
    return

    game = {
        'gameId': g.id,
        'name': 'foo!',
        'type': 'THBattle2v2',
        'flags': {},
        'players': [1, 2],
        'winners': [1],
        'deserters': [],
        'startedAt': '2020-12-02T15:43:05Z',
        'duration': 333,
    }

    rst = Q('''
        mutation TestRkAdjustRanking($game: GameInput!) {
            RkAdjustRanking(game: $game) {
                scoreBefore
            }
        }
    ''', variables={'game': game}, headers=auth_header)

    assert 'errors' not in rst
    assert rst['data']['RkAdjustRanking'][0]['scoreBefore'] > 0

    rst = Q('''
        mutation TestRkAdjustRanking($game: GameInput!) {
            RkAdjustRanking(game: $game) {
                scoreBefore
            }
        }
    ''', variables={'game': game}, headers=auth_header)

    assert 'errors' not in rst
    assert rst['data']['RkAdjustRanking'][0]['scoreBefore'] > 0
